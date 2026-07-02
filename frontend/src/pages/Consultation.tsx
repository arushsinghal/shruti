import { useEffect, useMemo, useState } from 'react';
import type { InputMode } from '../components/AudioUploader';
import { useNavigate, useParams } from 'react-router-dom';
import AudioUploader from '../components/AudioUploader';
import TranscriptViewer from '../components/TranscriptViewer';
import type { EntityHighlight } from '../components/TranscriptViewer';
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
    setConfirming(false);
  }

  return (
    <div className="border border-amber-200/80 rounded-xl bg-amber-50/70 p-4 space-y-3">
      <div className="flex items-start gap-3">
        <span className="grid place-items-center w-7 h-7 rounded-lg bg-amber-100 text-amber-600 shrink-0">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </span>
        <div>
          <p className="text-xs font-bold text-amber-900">Patient consent required before recording</p>
          <p className="text-[11px] text-amber-700 mt-1 leading-relaxed italic">
            "I will briefly record our conversation to help write accurate notes."
          </p>
        </div>
      </div>
      {error && (
        <p className="text-[11px] text-red-700 bg-red-50 border border-red-200 rounded-lg px-2.5 py-1.5 font-medium">{error}</p>
      )}
      <button
        onClick={handleConfirm}
        disabled={confirming}
        className="w-full py-2.5 rounded-lg text-xs font-bold bg-amber-600 hover:bg-amber-700 disabled:opacity-50 text-white transition-all active:scale-[0.99] cursor-pointer"
      >
        {confirming ? 'Recording consent…' : error ? 'Retry consent →' : 'Patient informed & consented →'}
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
        className="w-full px-4 py-3 rounded-lg bg-primary hover:bg-primary-dark text-white text-sm font-semibold transition-all shadow-sm active:scale-[0.99] flex items-center justify-center gap-2 cursor-pointer"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        View Full Document →
      </button>
    </div>
  );
}

// Pipeline status → brand-aligned semantic scale: neutral (start) → saffron (working) → green (done).
const STATUS_COLORS: Record<string, string> = {
  created: 'bg-slate-100 text-slate-600 border border-slate-200',
  audio_uploaded: 'bg-amber-50 text-amber-700 border border-amber-200/70',
  transcribed: 'bg-amber-50 text-amber-700 border border-amber-200/70',
  extracted: 'bg-amber-50 text-amber-700 border border-amber-200/70',
  memory_resolved: 'bg-amber-50 text-amber-700 border border-amber-200/70',
  soap_ready: 'bg-amber-100 text-amber-800 border border-amber-300/60',
  complete: 'bg-primary/10 text-primary border border-primary/20',
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

  // Input mode control (for external tab control on AudioUploader)
  const [inputMode, setInputMode] = useState<InputMode>('record');

  // Entity highlights from extracted facts — maps evidence_spans → highlight positions
  const entityHighlights: EntityHighlight[] = useMemo(() => {
    if (!clinicalResults || !transcriptResult) return [];
    const facts: any[] = (clinicalResults as any).extracted_facts ?? [];
    return facts.flatMap((f) =>
      (f.evidence_spans ?? []).map((s: { start_char: number; end_char: number }) => ({
        start: s.start_char,
        end: s.end_char,
        category: f.category as string,
        value: f.normalized_value as string,
      }))
    );
  }, [clinicalResults, transcriptResult]);

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
        if (s.clinical_facts && s.soap_note) {
          setClinicalResults({
            facts: s.clinical_facts,
            state: s.memory_state ?? {},
            soap: s.soap_note,
            cds: s.cds_suggestions ?? {},
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
    } catch (e: any) {
      console.error(e);
      const detail = e?.response?.data?.detail;
      setProcessError(detail || 'Processing failed. Check that the backend is running and the session has a transcript.');
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
      // Simulate ASR timing (it's local text submission, but show realistic timing)
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
        <div className="absolute inset-0 border-4 border-primary/10 rounded-full"></div>
        <div className="absolute inset-0 border-4 border-transparent border-t-primary rounded-full animate-spin"></div>
        <div className="absolute inset-2 border-4 border-transparent border-b-accent rounded-full animate-[spin_1.5s_linear_infinite_reverse]"></div>
        <div className="absolute inset-0 flex items-center justify-center">
          <svg className="w-8 h-8 text-primary animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
      </div>

      <div className="w-full max-w-sm space-y-3">
        {steps.map((text, idx) => (
          <div key={idx} className={`flex items-center gap-3 transition-all duration-300 ${idx <= step ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-4'}`}>
            <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 transition-colors ${idx < step ? 'bg-primary/10 text-primary' : idx === step ? 'bg-primary/10 text-primary animate-pulse' : 'bg-slate-100 text-slate-300'}`}>
              {idx < step ? (
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
              ) : idx === step ? (
                <div className="w-2 h-2 bg-primary rounded-full"></div>
              ) : null}
            </div>
            <p className={`text-xs font-semibold ${idx === step ? 'text-primary' : idx < step ? 'text-slate-500' : 'text-slate-300'}`}>
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

  const isHealth = session.mode === 'health' || !session.mode;

  return (
    <div className="h-screen flex flex-col overflow-hidden font-sans text-text-dark bg-bg-warm">

      {/* ── Header ──────────────────────────────────────────────────── */}
      <header className="border-b border-slate-200/80 bg-white z-20 flex-none h-14 flex items-center gap-4 px-5">
        <button
          onClick={() => navigate('/dashboard')}
          className="text-slate-400 hover:text-primary transition-colors flex items-center gap-1 text-[13px] font-medium cursor-pointer shrink-0"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span className="hidden sm:inline">Dashboard</span>
        </button>
        <div className="h-5 w-px bg-slate-200 shrink-0"></div>
        <button onClick={() => navigate('/dashboard')} className="flex items-center gap-2 shrink-0 cursor-pointer group">
          <span className="grid place-items-center w-7 h-7 rounded-lg bg-primary/10 text-primary font-bold text-sm group-hover:bg-primary/15 transition-colors">श</span>
          <span className="text-[15px] font-bold tracking-tight text-text-dark hidden sm:inline">Lipi</span>
        </button>
        <div className="h-5 w-px bg-slate-200 shrink-0 hidden md:block"></div>
        <div className="min-w-0 flex-1">
          <h1 className="text-sm font-bold text-slate-800 truncate leading-tight">
            {session.patient_name || 'Anonymous Session'}
          </h1>
          {session.doctor_name && <p className="text-[11px] text-slate-400 truncate leading-tight">{session.doctor_name}</p>}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {session.mode && (
            <span className={`hidden sm:inline-flex px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider border ${MODE_COLORS[session.mode]}`}>
              {session.mode}
            </span>
          )}
          <StatusBadge status={session.status} />
          {isHealth && (
            <button
              onClick={() => navigate(`/review/${id}`)}
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-primary hover:bg-primary-dark text-white text-xs font-semibold rounded-lg cursor-pointer transition-all active:scale-[0.98]"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Review Note
            </button>
          )}
          {/* Avatar */}
          <div className="w-8 h-8 rounded-full bg-primary/10 text-primary border border-primary/15 flex items-center justify-center text-xs font-bold shrink-0">
            {(session.doctor_name || 'D').charAt(0).toUpperCase()}
          </div>
        </div>
      </header>

      {/* ── Body: two-column split ───────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">

        {/* LEFT PANEL — white, sticky, scrollable */}
        <aside className="w-[360px] xl:w-[400px] shrink-0 bg-white flex flex-col overflow-y-auto border-r border-slate-200">

          {/* Section header */}
          <div className="px-5 pt-5 pb-4 border-b border-slate-100 shrink-0">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0">
                <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse shrink-0"></div>
                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-widest truncate">
                  {session.mode === 'government' ? 'Officer Recording'
                   : session.mode === 'legal' ? 'Legal Recording'
                   : session.mode === 'general' ? 'Audio Input'
                   : 'Consultation Recording'}
                </span>
              </div>
              <span className="text-[9px] font-bold text-primary bg-primary/10 border border-primary/15 px-2 py-0.5 rounded-full tracking-widest uppercase shrink-0">
                HI / EN / HINGLISH
              </span>
            </div>
          </div>

          <div className="flex-1 flex flex-col px-5 py-5 gap-4">

            {/* Patient intake card — visible when assistant pre-registered the patient */}
            {(session.patient_age || session.patient_sex || session.patient_phone || session.initiated_by === 'assistant') && (
              <div className="rounded-xl border border-primary/20 bg-primary/5 px-4 py-3 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold text-primary uppercase tracking-widest">Patient on file</span>
                  {session.initiated_by === 'assistant' && (
                    <span className="text-[9px] font-bold text-white bg-primary/70 px-1.5 py-0.5 rounded-full">via assistant</span>
                  )}
                </div>
                <p className="text-[15px] font-bold text-slate-800 leading-tight">{session.patient_name}</p>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-[12px] text-slate-600">
                  {session.patient_age && <span><span className="font-semibold text-slate-500">Age</span> {session.patient_age}</span>}
                  {session.patient_sex && <span><span className="font-semibold text-slate-500">Sex</span> {session.patient_sex}</span>}
                  {session.patient_phone && (
                    <span className="flex items-center gap-1">
                      <svg className="w-3 h-3 text-green-600" fill="currentColor" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M11.962 0C5.354 0 0 5.354 0 11.962c0 2.11.552 4.088 1.514 5.808L0 24l6.395-1.677A11.928 11.928 0 0011.962 23.924C18.57 23.924 24 18.57 24 11.962 24 5.354 18.57 0 11.962 0zm0 21.849a9.875 9.875 0 01-5.031-1.376l-.361-.214-3.737.979 1.001-3.646-.235-.374A9.849 9.849 0 012.1 11.963c0-5.449 4.413-9.887 9.863-9.887 5.45 0 9.862 4.438 9.862 9.887 0 5.449-4.412 9.886-9.862 9.886z"/></svg>
                      <span className="text-green-700 font-medium">{session.patient_phone}</span>
                    </span>
                  )}
                </div>
                {session.transcript?.startsWith('[Chief complaint:') && (
                  <p className="text-[12px] text-amber-800 bg-amber-50 border border-amber-200/60 rounded-lg px-3 py-1.5">
                    <span className="font-semibold">CC: </span>
                    {session.transcript.replace('[Chief complaint: ', '').replace(']', '')}
                  </p>
                )}
              </div>
            )}

            {/* Consent gate or consent badge */}
            {!consentGranted ? (
              <ConsentGate onConsented={handleConsentGranted} error={consentError} />
            ) : (
              <div className="flex items-center justify-between bg-primary/5 border border-primary/15 rounded-lg px-3 py-2">
                <span className="flex items-center gap-1.5 text-[11px] font-semibold text-primary">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  Consent Captured (verbal)
                </span>
                <span className="text-[9px] font-mono text-slate-400 uppercase tracking-wider">
                  {session?.consent_log?.consent_hash ? session.consent_log.consent_hash.slice(0, 8) + '…' : 'AUDIT LOGGED'}
                </span>
              </div>
            )}

            {/* Input mode tabs */}
            {consentGranted && (
              <div className="flex bg-slate-100 rounded-lg p-1 text-[11px] font-semibold">
                {(['record', 'file', 'text'] as const).map((m, i) => (
                  <button
                    key={m}
                    onClick={() => setInputMode(m)}
                    className={`flex-1 py-1.5 rounded-md transition-colors cursor-pointer ${
                      inputMode === m
                        ? 'bg-white text-slate-900 shadow-sm'
                        : 'text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    {['Live Dictation', 'Upload Audio', 'Direct Text'][i]}
                  </button>
                ))}
              </div>
            )}

            {/* AudioUploader — tabs hidden, mode controlled externally */}
            {consentGranted && (
              <AudioUploader
                sessionId={session.id}
                onTranscript={handleTranscript}
                onAutoProcess={handleExtractFacts}
                externalMode={inputMode}
                onModeChange={setInputMode}
                hideTabs
              />
            )}

            {/* Demo fallback button */}
            {showDemoButton && (
              <button
                onClick={handleDemoMode}
                className="w-full py-2.5 rounded-xl text-xs font-semibold border border-dashed border-primary/30 text-primary hover:border-primary/50 hover:bg-primary/5 transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Run demo consultation
              </button>
            )}

            {isDemoRunning && (
              <div className="flex items-center justify-center gap-2 text-xs text-primary font-bold py-2 bg-primary/5 rounded-lg border border-primary/15">
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                Processing audio…
              </div>
            )}

            {/* Process button */}
            {hasTranscript && !clinicalResults && (
              <div className="flex flex-col gap-2">
                {processError && <p className="text-xs text-red-600 font-medium bg-red-50 border border-red-100 rounded-lg px-3 py-2">{processError}</p>}
                {!isProcessing ? (
                  <button
                    onClick={handleExtractFacts}
                    className="w-full px-4 py-3 rounded-xl bg-primary hover:bg-primary-dark text-white text-sm font-bold transition-all shadow-sm active:scale-[0.99] flex items-center justify-center gap-2 cursor-pointer"
                  >
                    {session.mode === 'government' ? 'Generate FIR →'
                    : session.mode === 'legal' ? 'Generate Legal Document →'
                    : session.mode === 'general' ? 'Summarise Transcript →'
                    : 'Process Clinical Intelligence →'}
                  </button>
                ) : (
                  <div className="w-full px-4 py-3 rounded-xl bg-primary/5 border border-primary/15 text-primary text-sm font-bold flex items-center justify-center gap-2">
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                    </svg>
                    Running AI pipeline…
                  </div>
                )}
              </div>
            )}

            {/* LIVE TRANSCRIPT */}
            {hasTranscript && transcriptResult && (
              <div className="flex flex-col gap-2.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Live Transcript</span>
                    {asrMs && (
                      <span className="text-[9px] font-bold text-primary bg-primary/10 border border-primary/15 px-1.5 py-0.5 rounded tabular-nums">
                        {(asrMs / 1000).toFixed(1)}s
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-[9px] font-mono text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">hi-IN</span>
                    {!transcriptResult.is_stub && (
                      <span className="text-[9px] font-bold text-primary bg-primary/10 border border-primary/15 px-1.5 py-0.5 rounded tracking-wide">PHI SCRUBBED</span>
                    )}
                  </div>
                </div>
                {entityHighlights.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {[
                      { cat: 'symptom', label: 'Symptom', color: 'text-blue-700 bg-blue-50 border-blue-200' },
                      { cat: 'medication', label: 'Medication', color: 'text-green-700 bg-green-50 border-green-200' },
                      { cat: 'vital', label: 'Vital', color: 'text-purple-700 bg-purple-50 border-purple-200' },
                      { cat: 'allergy', label: 'Allergy', color: 'text-rose-700 bg-rose-50 border-rose-200' },
                    ].filter(({ cat }) => entityHighlights.some(h => h.category === cat)).map(({ cat, label, color }) => (
                      <span key={cat} className={`inline-flex items-center gap-1 text-[9px] font-bold px-1.5 py-0.5 rounded-md border tracking-wide ${color}`}>
                        <span className="w-1.5 h-1.5 rounded-full bg-current" /> {label}
                      </span>
                    ))}
                  </div>
                )}
                <div className="bg-slate-50/80 border border-slate-200 rounded-xl p-3.5 max-h-[260px] overflow-y-auto">
                  <TranscriptViewer
                    transcript={transcriptResult.transcript}
                    languageDetected={transcriptResult.language_detected}
                    isStub={transcriptResult.is_stub}
                    diarizedTranscript={transcriptResult.diarized_transcript}
                    highlights={entityHighlights}
                  />
                </div>
              </div>
            )}

          </div>

          {/* Bottom CTA — Review & Sign */}
          {clinicalResults && id && (
            <div className="p-4 border-t border-slate-100 bg-white shrink-0">
              <button
                onClick={() => navigate(`/review/${id}`)}
                className="w-full px-4 py-3.5 rounded-xl bg-primary hover:bg-primary-dark text-white text-sm font-bold transition-all shadow-sm active:scale-[0.99] flex items-center justify-center gap-2 cursor-pointer"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Review &amp; Sign Note →
              </button>
            </div>
          )}
        </aside>

        {/* RIGHT PANEL — scrollable */}
        <main className="flex-1 overflow-y-auto bg-bg-warm">
          {clinicalResults ? (
            isHealth ? (
              <div className="p-6 xl:p-8 animate-in fade-in slide-in-from-right-4 duration-500 ease-out">
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
              <div className="p-6 xl:p-8">
                <DocumentReadyCard
                  mode={session.mode!}
                  soap={clinicalResults.soap as any}
                  onReview={() => navigate(`/review/${id}`)}
                />
              </div>
            )
          ) : (
            <div className={`h-full flex flex-col items-center justify-center min-h-[500px] transition-all duration-500 ${isProcessing ? 'bg-white' : 'bg-transparent'}`}>
              {isProcessing ? (
                <AiProgressSequencer />
              ) : (
                <div className="text-center px-8 max-w-sm">
                  <div className="w-16 h-16 mx-auto mb-5 rounded-2xl bg-white shadow-sm border border-slate-200/70 flex items-center justify-center">
                    <svg className="w-8 h-8 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                    </svg>
                  </div>
                  <p className="text-sm font-semibold text-slate-600">
                    {session.mode === 'government' ? 'FIR document will appear here after processing.'
                    : session.mode === 'legal' ? 'Legal document will appear here after processing.'
                    : session.mode === 'general' ? 'Transcript summary will appear here after processing.'
                    : 'Clinical documentation will appear here after processing.'}
                  </p>
                  <p className="text-xs text-slate-400 mt-2">Record or upload audio on the left to begin.</p>
                </div>
              )}
            </div>
          )}
        </main>

      </div>
    </div>
  );
}
