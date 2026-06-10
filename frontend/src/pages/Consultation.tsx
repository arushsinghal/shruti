import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import AudioUploader from '../components/AudioUploader';
import TranscriptViewer from '../components/TranscriptViewer';
import ClinicalResults from '../components/ClinicalResults';
import { getSession, processClinical } from '../lib/api';
import type { ConsultationSession, TranscribeResponse, ProcessClinicalResponse } from '../types/clinical';

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

  const [transcriptResult, setTranscriptResult] = useState<TranscribeResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [clinicalResults, setClinicalResults] = useState<ProcessClinicalResponse | null>(null);
  const [processError, setProcessError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getSession(id)
      .then((s) => {
        setSession(s);
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

  function handleTranscript(result: TranscribeResponse) {
    setTranscriptResult(result);
    setClinicalResults(null);
    setProcessError(null);
    if (id) getSession(id).then(setSession);
  }

  async function handleExtractFacts() {
    if (!id) return;
    setIsProcessing(true);
    setProcessError(null);
    try {
      const results = await processClinical(id);
      setClinicalResults(results);
      getSession(id).then(setSession);
    } catch (e) {
      console.error(e);
      setProcessError('Failed to process clinical documentation. Ensure backend service is active.');
    } finally {
      setIsProcessing(false);
    }
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
        <p className="text-sm text-slate-400 animate-pulse font-medium">Loading consultation details...</p>
      </div>
    );
  }

  const hasTranscript = !!transcriptResult;

  return (
    <div className="min-h-screen bg-bg-warm pb-20 font-sans text-text-dark">
      <header className="border-b border-slate-200/80 sticky top-0 bg-white/90 backdrop-blur-md z-10 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-slate-400 hover:text-primary transition-colors flex items-center text-xs font-semibold cursor-pointer"
            >
              <svg className="w-4 h-4 mr-1 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Dashboard
            </button>
            <div className="h-4 w-px bg-slate-200"></div>
            <div className="flex items-center gap-2">
              <span className="font-serif font-bold text-primary text-base">श</span>
              <span className="text-sm font-bold text-text-dark">SHRUTI</span>
            </div>
            <div className="h-4 w-px bg-slate-200"></div>
            <div>
              <h1 className="text-sm font-bold text-text-dark">
                {session.patient_name ? `Patient: ${session.patient_name}` : 'Anonymous Consultation'}
              </h1>
            </div>
            {session.doctor_name && (
              <>
                <div className="h-4 w-px bg-slate-200"></div>
                <p className="text-xs font-semibold text-slate-500">Dr. {session.doctor_name}</p>
              </>
            )}
          </div>
          <div className="flex items-center gap-3">
            <span className="bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">
              Local Clinical AI Active
            </span>
            <StatusBadge status={session.status} />
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-[1fr_2fr] gap-8 items-start">
          
          <div className="space-y-6 lg:sticky lg:top-20">
            <section className="border border-slate-200 rounded-lg p-5 bg-white shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest">
                  Consultation Input
                </h2>
                {/* Language indicator badge */}
                <span className="bg-accent/15 text-accent-dark border border-accent/20 px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-widest">
                  EN / HI / Hinglish
                </span>
              </div>
              
              <AudioUploader sessionId={session.id} onTranscript={handleTranscript} />
            </section>

            {hasTranscript && transcriptResult && (
              <section className="border border-slate-200 rounded-lg bg-white overflow-hidden flex flex-col max-h-[500px] shadow-sm">
                <div className="px-4 py-3 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
                  <h2 className="text-xs font-bold text-slate-600 uppercase tracking-widest">
                    Transcript Output
                  </h2>
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
                <button
                  onClick={handleExtractFacts}
                  disabled={isProcessing}
                  className="w-full px-4 py-3 rounded bg-primary hover:bg-primary-dark disabled:opacity-50 text-white text-sm font-semibold transition-all shadow-md flex items-center justify-center gap-2 cursor-pointer"
                >
                  {isProcessing ? 'Documenting Consultation...' : 'Begin Clinical Documentation →'}
                </button>
              </div>
            )}
          </div>

          <div className="min-h-[500px]">
            {clinicalResults ? (
              <ClinicalResults results={clinicalResults} sessionId={id!} patientName={session.patient_name} doctorName={session.doctor_name} />
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 border border-dashed border-slate-200 rounded-lg bg-white shadow-sm min-h-[450px]">
                <svg className="w-10 h-10 mb-3 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-xs font-semibold text-slate-500">Clinical documentation will render here after processing.</p>
              </div>
            )}
          </div>

        </div>
      </main>
    </div>
  );
}
