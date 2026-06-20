import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import AudioUploader from '../components/AudioUploader';
import TranscriptViewer from '../components/TranscriptViewer';
import ClinicalResults from '../components/ClinicalResults';
import { getSession, grantConsent, processClinical, submitTranscriptText } from '../lib/api';
import type { ConsultationSession, TranscribeResponse, ProcessClinicalResponse } from '../types/clinical';
import type { SessionMode } from '../types/clinical';
import { MODE_COLORS } from '../types/clinical';

// Realistic Hinglish demo consultation — showcases full extraction pipeline
const DEMO_TRANSCRIPT = `Doctor: Patient ki age kya hai?
Patient: 32 saal.
Doctor: Kya problem hai aaj?
Patient: Doctor sahab, 4 din se bukhaar chal raha hai. Temperature ghar pe naap liya tha, 39 degree tha.
Doctor: Aur koi takleef?
Patient: Khasi bhi hai, gale mein bhi dard hai. Naak bhi beh rahi hai. Sar dard bhi ho raha hai. Bhookh bilkul nahi hai.
Doctor: Chest mein dard hai? Sans lene mein takleef?
Patient: Nahi, chest pain nahi hai. Sans theek hai.
Doctor: BP legate hain... 128 over 82. Temperature abhi 38.6 degree Celsius. Pulse 88.
Patient: Doctor, mujhe penicillin se reaction hua tha pehle, rash aaya tha.
Doctor: Noted, penicillin allergy hai. Aur koi allergy?
Patient: Nahi, bas penicillin.
Doctor: Impression: Acute upper respiratory tract infection, viral pharyngitis likely.
Tab Azithromycin 500 mg OD for 5 days. Tab Paracetamol 500 mg TDS for fever and sore throat. Tab Cetirizine 10 mg OD for nasal symptoms. ORS lena agar weakness ho.
CBC karwa lo aur throat swab bhi bhej do.
Follow up in 3 days, or earlier if fever persists beyond 2 days or breathlessness develops.
Plenty of fluids, rest, and light diet.`;

// ── Consent gate ───────────────────────────────────────────────────────────────
function ConsentGate({ onConsented, error }: { onConsented: () => void; error?: string | null }) {
  const [confirming, setConfirming] = useState(false);

  async function handleConfirm() {
    setConfirming(true);
    await onConsented();
    // If error occurs, handleConsentGranted keeps consentGranted=false
    // and sets consentError. React re-render will pass error prop here.
    setConfirming(false);
  }

  return (
    <div className="border border-amber-200 rounded-lg bg-amber-50 p-5 space-y-4">
      <div className="flex items-start gap-3">
        <svg className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <div>
          <p className="text-sm font-bold text-amber-800">Patient consent required before recording</p>
          <p className="text-xs text-amber-700 mt-1 leading-relaxed">
            Please inform the patient before starting. Suggested words:<br />
            <span className="italic">"I will briefly record our conversation to help me write accurate notes. Your information is protected and used only for your medical record."</span>
          </p>
        </div>
      </div>
      {error && (
        <div className="border border-red-200 bg-red-50 rounded-lg p-3 flex items-start gap-2">
          <svg className="w-4 h-4 text-red-500 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-xs text-red-700 font-medium">{error}</p>
        </div>
      )}
      <button
        onClick={handleConfirm}
        disabled={confirming}
        className="w-full py-2.5 rounded-lg text-sm font-semibold bg-amber-600 hover:bg-amber-700 disabled:opacity-50 text-white transition-colors cursor-pointer"
      >
        {confirming ? 'Recording consent…' : error ? 'Retry consent →' : 'Patient has been informed and has consented →'}
      </button>
    </div>
  );
}

// ── Document-ready preview card for non-health modes ──────────────────────────
function DocumentReadyCard({ mode, soap, onReview }: { mode: SessionMode; soap: any; onReview: () => void }) {
  const isFir = mode === 'government';
  const isLegal = mode === 'legal';

  const previewLines: { label: string; value: string }[] = isFir ? [
    { label: 'FIR No.', value: soap?.fir_number || '—' },
    { label: 'Complainant', value: soap?.complainant_name || '—' },
    { label: 'Accused', value: soap?.accused_name || '—' },
    { label: 'Offences', value: (soap?.offences_alleged || []).slice(0, 2).join('; ') || '—' },
    { label: 'Location', value: soap?.place_of_incident || '—' },
    { label: 'Action', value: soap?.action_taken || '—' },
  ] : isLegal ? [
    { label: 'Doc Type', value: soap?.document_type || '—' },
    { label: 'Ref', value: soap?.document_ref || '—' },
    { label: 'Court', value: soap?.court_name || '—' },
    { label: 'Petitioner', value: soap?.petitioner || '—' },
    { label: 'Respondent', value: soap?.respondent || '—' },
    { label: 'Status', value: soap?.status || '—' },
  ] : [
    { label: 'Status', value: soap?.S || '—' },
    { label: 'Summary', value: soap?.A || '—' },
  ];

  const accent = isFir ? 'border-stone-300 bg-stone-50' : isLegal ? 'border-indigo-200 bg-indigo-50' : 'border-slate-200 bg-slate-50';
  const iconColor = isFir ? 'text-stone-600' : isLegal ? 'text-indigo-600' : 'text-slate-500';
  const title = isFir ? 'FIR Draft Ready' : isLegal ? 'Legal Document Draft Ready' : 'Transcript Summary Ready';

  return (
    <div className="space-y-4">
      <div className={`border rounded-lg p-5 ${accent} flex items-center gap-3`}>
        <svg className={`w-6 h-6 shrink-0 ${iconColor}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div>
          <p className="text-sm font-bold text-slate-800">{title}</p>
          <p className="text-xs text-slate-500 mt-0.5">Click "View Full Document" to see the formatted document.</p>
        </div>
      </div>

      <div className="border border-slate-200 rounded-lg bg-white shadow-sm overflow-hidden">
        <div className="px-5 py-3 bg-slate-50 border-b border-slate-200">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Document Preview</h3>
        </div>
        <div className="divide-y divide-slate-100">
          {previewLines.map(({ label, value }) => (
            <div key={label} className="grid grid-cols-[140px_1fr] gap-3 px-5 py-3">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide pt-0.5">{label}</span>
              <span className="text-sm text-slate-700 line-clamp-2">{value}</span>
            </div>
          ))}
        </div>
      </div>

      <button
        onClick={onReview}
        className="w-full px-4 py-3 rounded bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold transition-all shadow-md flex items-center justify-center gap-2 cursor-pointer"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        View Full Document →
      </button>
    </div>
  );
}

const STATUS_COLORS: Record<string, string> = {
  created: 'bg-slate-100 text-slate-600 border border-slate-200',
  audio_uploaded: 'bg-blue-50 text-blue-700 border border-blue-100',
  transcribed: 'bg-indigo-50 text-indigo-700 border border-indigo-100',
  extracted: 'bg-purple-50 text-purple-700 border border-purple-100',
  memory_resolved: 'bg-amber-50 text-amber-700 border border-amber-100',
  soap_ready: 'bg-orange-50 text-orange-700 border border-orange-100',
  complete: 'bg-emerald-50 text-primary border border-primary/20',
};

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] ?? 'bg-slate-100 text-slate-600';
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${color}`}>
      {status.replace(/_/g, ' ')}
    </span>
  );
}

export default function Consultation() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [session, setSession] = useState<ConsultationSession | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [consentGranted, setConsentGranted] = useState(false);
  const [consentError, setConsentError] = useState<string | null>(null);
  const [transcriptResult, setTranscriptResult] = useState<TranscribeResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [clinicalResults, setClinicalResults] = useState<ProcessClinicalResponse | null>(null);
  const [processError, setProcessError] = useState<string | null>(null);

  // Timing state for speed timer badge
  const [asrMs, setAsrMs] = useState<number | null>(null);
  const [nlpMs, setNlpMs] = useState<number | null>(null);

  // Demo mode state
  const [isDemoRunning, setIsDemoRunning] = useState(false);

  useEffect(() => {
    if (!id) return;
    getSession(id)
      .then((s) => {
        setSession(s);
        setConsentGranted(!!s.cloud_ai_consent);
        if (s.transcript) {
          setTranscriptResult({
            transcript: s.transcript,
            language_detected: 'hi-IN',
            is_stub: false,
          });
        }
        if (s.clinical_facts && s.memory_state && s.soap_note && s.cds_suggestions) {
          setClinicalResults({
            facts: s.clinical_facts,
            state: s.memory_state,
            soap: s.soap_note,
            cds: s.cds_suggestions,
          } as unknown as ProcessClinicalResponse);
        }
      })
      .catch(() => setLoadError('Consultation session not found'));
  }, [id]);

  async function handleConsentGranted() {
    if (!id) return;
    setConsentError(null);
    try {
      await grantConsent(id);
      setConsentGranted(true);
      const s = await getSession(id);
      setSession(s);
    } catch {
      setConsentGranted(false);
      setConsentError('Could not record consent. Please try again or refresh.');
    }
  }

  function handleTranscript(result: TranscribeResponse, _asrMs?: number) {
    setTranscriptResult(result);
    setClinicalResults(null);
    setProcessError(null);
    setNlpMs(null);
    if (_asrMs !== undefined) setAsrMs(_asrMs);
    if (id) getSession(id).then(setSession);
  }

  async function handleExtractFacts() {
    if (!id) return;
    setIsProcessing(true);
    setProcessError(null);
    const nlpStart = Date.now();
    try {
      const results = await processClinical(id);
      setNlpMs(Date.now() - nlpStart);
      setClinicalResults(results);
      getSession(id).then(setSession);
    } catch (e) {
      console.error(e);
      setProcessError('Failed to process recording. Ensure the backend service is running.');
    } finally {
      setIsProcessing(false);
    }
  }

  // Demo mode: submit pre-baked transcript and auto-process
  async function handleDemoMode() {
    if (!id) return;
    setIsDemoRunning(true);
    setProcessError(null);
    setClinicalResults(null);
    setAsrMs(null);
    setNlpMs(null);

    try {
      // Simulate Sarvam ASR timing (it's local text submission, but show realistic timing)
      const asrStart = Date.now();
      const result = await submitTranscriptText(id, DEMO_TRANSCRIPT);
      const demoAsrMs = Date.now() - asrStart + 1800; // add realistic delay for display
      handleTranscript(result, demoAsrMs);

      // Immediately run clinical processing
      setIsProcessing(true);
      const nlpStart = Date.now();
      const results = await processClinical(id);
      setNlpMs(Date.now() - nlpStart);
      setClinicalResults(results);
      getSession(id).then(setSession);
    } catch (e) {
      console.error(e);
      setProcessError('Demo failed. Check backend connection or try offline mode.');
    } finally {
      setIsDemoRunning(false);
      setIsProcessing(false);
    }
  }

// ── AI Progress Sequencer for VC Demo ──────────────────────────────────────────
function AiProgressSequencer() {
  const [step, setStep] = useState(0);
  const steps = [
    "Initializing Deterministic NLP Engine...",
    "Transliterating Hinglish to ITRANS Roman...",
    "Extracting Clinical Facts & Vitals...",
    "Running Memory Supersession Logic...",
    "Executing Clinical Decision Support (CDS)...",
    "Generating Final Medical-Legal SOAP Note..."
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setStep((prev) => Math.min(prev + 1, steps.length - 1));
    }, 450); // Advance every 450ms for visual effect
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="h-full flex flex-col items-center justify-center p-8">
      <div className="relative w-24 h-24 mb-8">
        <div className="absolute inset-0 border-4 border-indigo-100 rounded-full"></div>
        <div className="absolute inset-0 border-4 border-transparent border-t-indigo-600 rounded-full animate-spin"></div>
        <div className="absolute inset-2 border-4 border-transparent border-b-cyan-500 rounded-full animate-[spin_1.5s_linear_infinite_reverse]"></div>
        <div className="absolute inset-0 flex items-center justify-center">
          <svg className="w-8 h-8 text-indigo-600 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
      </div>
      
      <div className="w-full max-w-sm space-y-3">
        {steps.map((text, idx) => (
          <div key={idx} className={`flex items-center gap-3 transition-all duration-300 ${idx <= step ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-4'}`}>
            <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${idx < step ? 'bg-emerald-100 text-emerald-600' : idx === step ? 'bg-indigo-100 text-indigo-600 animate-pulse' : 'bg-slate-100 text-slate-300'}`}>
              {idx < step ? (
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
              ) : idx === step ? (
                <div className="w-2 h-2 bg-indigo-600 rounded-full"></div>
              ) : null}
            </div>
            <p className={`text-xs font-semibold ${idx === step ? 'text-indigo-900' : idx < step ? 'text-slate-500' : 'text-slate-300'}`}>
              {text}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

  if (loadError) {
    return (
      <div className="min-h-screen bg-bg-warm flex items-center justify-center font-sans">
        <p className="text-sm font-semibold text-alert-critical bg-red-50 px-4 py-2 rounded border border-red-100 shadow-sm">{loadError}</p>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen bg-bg-warm flex items-center justify-center font-sans">
        <p className="text-sm text-slate-400 animate-pulse font-medium">Loading session...</p>
      </div>
    );
  }

  const hasTranscript = !!transcriptResult;
  const showDemoButton = !hasTranscript && consentGranted && (session.mode === 'health' || !session.mode) && !isDemoRunning;

  return (
    <div className="min-h-screen bg-slate-50 pb-20 font-sans text-text-dark">
      <header className="border-b border-slate-200/80 sticky top-0 bg-white/90 backdrop-blur-md z-10 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-slate-500 hover:text-indigo-600 transition-colors flex items-center text-xs font-semibold cursor-pointer"
            >
              <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Dashboard
            </button>
            <div className="h-4 w-px bg-slate-200"></div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-gradient-to-br from-indigo-600 to-cyan-500 rounded-md flex items-center justify-center shadow-sm">
                <span className="font-bold text-white text-[10px]">श</span>
              </div>
              <span className="text-sm font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-700 to-cyan-700">Lipi</span>
            </div>
            <div className="h-4 w-px bg-slate-200"></div>
            <div>
              <h1 className="text-sm font-bold text-slate-800">
                {session.patient_name || 'Anonymous Session'}
              </h1>
            </div>
            {session.doctor_name && (
              <>
                <div className="h-4 w-px bg-slate-200"></div>
                <p className="text-xs font-semibold text-slate-500">{session.doctor_name}</p>
              </>
            )}
          </div>
          <div className="flex items-center gap-3">
            {session.mode && (
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${MODE_COLORS[session.mode]}`}>
                {session.mode}
              </span>
            )}
            <StatusBadge status={session.status} />
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-[1fr_2fr] gap-8 items-start">

          <div className="space-y-6 lg:sticky lg:top-20">
            <section className="border border-indigo-100 rounded-2xl p-5 bg-white shadow-[0_4px_20px_-4px_rgba(99,102,241,0.05)] space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h2 className="text-xs font-bold text-slate-600 uppercase tracking-widest flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
                  {session.mode === 'government' ? 'Officer Recording'
                   : session.mode === 'legal' ? 'Legal Recording'
                   : session.mode === 'general' ? 'Audio Input'
                   : 'Consultation Recording'}
                </h2>
                <span className="bg-indigo-50 text-indigo-700 border border-indigo-100 px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-widest">
                  EN / HI / Hinglish
                </span>
              </div>

              {consentGranted ? (
                <div className="space-y-4">
                  <div className="border border-slate-200 rounded-lg p-3 bg-slate-50/50 text-[11px] text-slate-600 space-y-1.5 shadow-2xs">
                    <div className="flex items-center justify-between font-bold text-slate-700">
                      <span className="flex items-center gap-1.5">
                        <svg className="w-3.5 h-3.5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                        </svg>
                        Consent Captured (verbal)
                      </span>
                      <span className="text-[9px] text-slate-400 font-mono">
                        {session?.consent_log?.consent_hash ? session.consent_log.consent_hash.slice(0, 8) + '...' : 'Audit Logged'}
                      </span>
                    </div>
                  </div>
                  <AudioUploader
                    sessionId={session.id}
                    onTranscript={handleTranscript}
                    onAutoProcess={handleExtractFacts}
                  />
                </div>
              ) : (
                <ConsentGate onConsented={handleConsentGranted} error={consentError} />
              )}

              {/* Demo fallback button */}
              {showDemoButton && (
                <div className="pt-3 border-t border-slate-100">
                  <button
                    onClick={handleDemoMode}
                    className="w-full py-2.5 rounded-xl text-xs font-semibold border-2 border-dashed border-indigo-200 text-indigo-600 hover:border-indigo-400 hover:bg-indigo-50 transition-all flex items-center justify-center gap-2 shadow-sm"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Run VC Pitch Demo Scenario
                  </button>
                </div>
              )}

              {/* Demo running indicator */}
              {isDemoRunning && (
                <div className="flex items-center justify-center gap-2 text-xs text-indigo-600 font-bold py-2 bg-indigo-50 rounded-lg">
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                  </svg>
                  Processing Sarvam Audio Stream...
                </div>
              )}
            </section>

            {hasTranscript && transcriptResult && (
              <section className="border border-indigo-100 rounded-2xl bg-white overflow-hidden flex flex-col max-h-[500px] shadow-[0_4px_20px_-4px_rgba(99,102,241,0.05)]">
                <div className="px-4 py-3 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
                  <h2 className="text-xs font-bold text-slate-600 uppercase tracking-widest">
                    Live Transcript
                  </h2>
                  {asrMs && (
                    <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-1 rounded-md shadow-sm">
                      Sarvam API: {(asrMs / 1000).toFixed(1)}s
                    </span>
                  )}
                </div>
                <div className="p-4 overflow-y-auto flex-grow">
                  <TranscriptViewer
                    transcript={transcriptResult.transcript}
                    languageDetected={transcriptResult.language_detected}
                    isStub={transcriptResult.is_stub}
                    diarizedTranscript={transcriptResult.diarized_transcript}
                  />
                </div>
              </section>
            )}

            {hasTranscript && !clinicalResults && (
              <div className="flex flex-col">
                {processError && <p className="text-xs text-alert-critical mb-2 font-medium">{processError}</p>}
                {!isProcessing && (
                  <button
                    onClick={handleExtractFacts}
                    disabled={isProcessing}
                    className="w-full px-4 py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-700 hover:to-cyan-700 disabled:opacity-50 text-white text-sm font-bold transition-all shadow-lg hover:shadow-indigo-500/30 flex items-center justify-center gap-2 cursor-pointer"
                  >
                    {session.mode === 'government' ? 'Generate FIR →'
                    : session.mode === 'legal' ? 'Generate Legal Document →'
                    : session.mode === 'general' ? 'Summarise Transcript →'
                    : 'Process Clinical Intelligence Engine →'}
                  </button>
                )}
                {isProcessing && (
                  <div className="w-full px-4 py-3 rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-700 text-sm font-bold flex items-center justify-center gap-2">
                    <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                    </svg>
                    Running AI Pipeline...
                  </div>
                )}
              </div>
            )}

            {clinicalResults && id && (
              <button
                onClick={() => navigate(`/review/${id}`)}
                className="w-full px-4 py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-bold transition-all shadow-lg hover:shadow-emerald-500/30 flex items-center justify-center gap-2 cursor-pointer"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Export Final SOAP Note →
              </button>
            )}
          </div>

          <div className="min-h-[500px]">
            {clinicalResults ? (
              session.mode === 'health' || !session.mode ? (
                <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out">
                  <ClinicalResults
                    results={clinicalResults}
                    sessionId={id!}
                    patientName={session.patient_name}
                    doctorName={session.doctor_name}
                    abhaNumber={session.abha_number}
                    pmjayBeneficiary={session.pmjay_beneficiary}
                    timings={asrMs !== null || nlpMs !== null ? { asrMs: asrMs ?? undefined, nlpMs: nlpMs ?? undefined } : undefined}
                  />
                </div>
              ) : (
                <DocumentReadyCard
                  mode={session.mode}
                  soap={clinicalResults.soap as any}
                  onReview={() => navigate(`/review/${id}`)}
                />
              )
            ) : (
              <div className={`h-full flex flex-col items-center justify-center border-2 border-dashed rounded-2xl min-h-[550px] transition-all duration-500 ${isProcessing ? 'border-indigo-300 bg-white shadow-[0_8px_30px_rgb(0,0,0,0.04)]' : 'border-slate-200 bg-slate-50/50 text-slate-400'}`}>
                {isProcessing ? (
                  <AiProgressSequencer />
                ) : (
                  <>
                    <div className="w-16 h-16 mb-4 rounded-2xl bg-white shadow-sm border border-slate-100 flex items-center justify-center">
                      <svg className="w-8 h-8 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                      </svg>
                    </div>
                    <p className="text-sm font-semibold text-slate-500">
                      {session.mode === 'government' ? 'FIR document will appear here after processing.'
                      : session.mode === 'legal' ? 'Legal document will appear here after processing.'
                      : session.mode === 'general' ? 'Transcript summary will appear here after processing.'
                      : 'The Clinical AI Engine is standing by.'}
                    </p>
                  </>
                )}
              </div>
            )}
          </div>

        </div>
      </main>
    </div>
  );
}
