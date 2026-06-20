import { useState, useEffect, useRef } from 'react';
import type { ProcessClinicalResponse } from '../types/clinical';
import { getFhirBundle } from '../lib/api';
import PrintableReport from './PrintableReport';
import PrescriptionPrint from './PrescriptionPrint';
import PatientInstructionsHindi from './PatientInstructionsHindi';
import AudioRecap from './AudioRecap';
import ReferralLetter from './ReferralLetter';
import DischargeSummary from './DischargeSummary';

const ICD10_MAP: Record<string, string> = {
  'urti': 'J06.9', 'upper respiratory': 'J06.9', 'pharyngitis': 'J02.9',
  'fever': 'R50.9', 'viral fever': 'A99',
  'hypertension': 'I10',
  'diabetes': 'E11.9', 'type 2 diabetes': 'E11.9',
  'pneumonia': 'J18.9',
  'gastroenteritis': 'A09', 'diarrhea': 'A09',
  'uti': 'N39.0', 'urinary tract': 'N39.0',
  'malaria': 'B54',
  'dengue': 'A90',
  'typhoid': 'A01.0',
  'tuberculosis': 'A15.9', 'tb': 'A15.9',
  'anemia': 'D64.9',
  'asthma': 'J45.9',
  'gerd': 'K21.9', 'acid reflux': 'K21.9',
  'hypothyroidism': 'E03.9',
  'common cold': 'J06.9',
  'bronchitis': 'J40',
  'sinusitis': 'J32.9',
  'migraine': 'G43.9',
  'headache': 'R51',
  'anxiety': 'F41.9',
  'depression': 'F32.9',
};

function getIcd10(assessmentText: string): string | null {
  const lower = assessmentText.toLowerCase();
  for (const [keyword, code] of Object.entries(ICD10_MAP)) {
    if (lower.includes(keyword)) return code;
  }
  return null;
}

interface ClinicalResultsProps {
  results: ProcessClinicalResponse;
  sessionId: string;
  patientName?: string;
  doctorName?: string;
  abhaNumber?: string;
  pmjayBeneficiary?: boolean;
  timings?: { asrMs?: number; nlpMs?: number };
}

export default function ClinicalResults({ results, sessionId, patientName, doctorName, abhaNumber, pmjayBeneficiary, timings }: ClinicalResultsProps) {
  const { state, soap, cds, source } = results;
  const [fhirData, setFhirData] = useState<any>(null);
  const [isExporting, setIsExporting] = useState(false);

  // HITL State
  const [editableSoap, setEditableSoap] = useState({ S: '', O: '', A: '', P: '' });
  const [isSigned, setIsSigned] = useState(false);
  const hasAnimatedRef = useRef(false);

  // Typewriter animation: fills each SOAP section simultaneously over ~600ms
  useEffect(() => {
    if (!soap) return;

    if (hasAnimatedRef.current) {
      // Re-render after edit — set directly without animation
      setEditableSoap({ S: soap.S, O: soap.O, A: soap.A, P: soap.P });
      return;
    }
    hasAnimatedRef.current = true;

    const DURATION_MS = 600;
    const TICK_MS = 16; // ~60fps
    const intervals: ReturnType<typeof setInterval>[] = [];

    for (const key of ['S', 'O', 'A', 'P'] as const) {
      const text = soap[key] || '';
      const totalTicks = Math.ceil(DURATION_MS / TICK_MS);
      const charsPerTick = Math.max(1, Math.ceil(text.length / totalTicks));
      let pos = 0;

      const id = setInterval(() => {
        pos = Math.min(pos + charsPerTick, text.length);
        setEditableSoap(prev => ({ ...prev, [key]: text.slice(0, pos) }));
        if (pos >= text.length) clearInterval(id);
      }, TICK_MS);

      intervals.push(id);
    }

    return () => intervals.forEach(clearInterval);
  }, [soap]);

  function handleWhatsAppShare() {
    const meds = results.facts?.medications ?? [];
    const followUp = (results.facts as any)?.follow_up ?? [];
    const lines = [
      `*Prescription — ${patientName ?? 'Patient'}*`,
      `_${new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}_`,
      '',
      '*Medicines:*',
      ...meds.map((m: { name: string; dosage: string; frequency: string }) =>
        `• ${m.name.charAt(0).toUpperCase() + m.name.slice(1)} ${m.dosage} — ${m.frequency}`
      ),
      '',
      followUp.length > 0 ? `*Follow up:* ${followUp.join(', ')}` : '',
      '',
      '_Reviewed by physician · Lipi Health_',
    ].filter((l): l is string => l !== '');
    const text = encodeURIComponent(lines.join('\n'));
    window.open(`https://wa.me/?text=${text}`, '_blank');
  }

  async function handleExportFhir() {
    setIsExporting(true);
    try {
      const bundle = await getFhirBundle(sessionId);
      setFhirData(bundle);
    } catch (e) {
      console.error(e);
      alert('Failed to generate HL7 FHIR bundle.');
    } finally {
      setIsExporting(false);
    }
  }

  function handleSignNote() {
    setIsSigned(true);
  }

  const totalMs = (timings?.asrMs ?? 0) + (timings?.nlpMs ?? 0);

  return (
    <div className="space-y-6 animate-fade-in-up">

      <AudioRecap results={results} patientName={patientName} />

      {source === 'fallback' && (
        <div className="flex items-center gap-2 px-3 py-2.5 rounded border border-primary/25 bg-primary/10 text-xs text-primary shadow-sm">
          <svg className="w-4.5 h-4.5 shrink-0 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <span className="font-semibold">Lipi Local Engine Active — consultation processed securely at the edge.</span>
        </div>
      )}

      {/* SOAP Note Section */}
      <section className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        {/* Title row */}
        <div className="flex items-center justify-between px-6 pt-5 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3 flex-wrap">
            <h2 className="text-base font-serif font-bold text-text-dark">SOAP Document</h2>
            {isSigned ? (
              <span className="text-[10px] font-bold bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded-full uppercase tracking-wider">✓ Signed</span>
            ) : (
              <span className="text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full uppercase tracking-wider">Draft · Needs Review</span>
            )}
          </div>
          <div className="flex items-center gap-1.5">
            {timings?.asrMs !== undefined && (
              <span className="text-[10px] font-semibold text-slate-500 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded-full">
                ASR {(timings.asrMs / 1000).toFixed(1)}s
              </span>
            )}
            {timings?.nlpMs !== undefined && (
              <span className="text-[10px] font-semibold text-slate-500 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded-full">
                NLP {(timings.nlpMs / 1000).toFixed(1)}s
              </span>
            )}
            {timings?.asrMs !== undefined && timings?.nlpMs !== undefined && (
              <span className="text-[10px] font-bold text-primary bg-primary/5 border border-primary/20 px-2 py-0.5 rounded-full">
                {(totalMs / 1000).toFixed(1)}s total
              </span>
            )}
          </div>
        </div>

        {/* Action toolbar */}
        <div className="px-6 py-3 bg-slate-50/70 border-b border-slate-100 flex flex-wrap gap-x-4 gap-y-2 items-center">
          {/* Documents group */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mr-1">Generate</span>
            <PrescriptionPrint results={results} patientName={patientName} doctorName={doctorName} />
            <PatientInstructionsHindi results={results} patientName={patientName} doctorName={doctorName} />
            <ReferralLetter results={results} patientName={patientName} doctorName={doctorName} abhaNumber={abhaNumber} />
            <DischargeSummary results={results} patientName={patientName} doctorName={doctorName} />
          </div>

          <div className="w-px h-5 bg-slate-200 hidden sm:block" />

          {/* Share / sign group */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mr-1">Share</span>
            <button
              onClick={handleWhatsAppShare}
              className="flex items-center gap-1.5 text-xs font-medium text-emerald-700 hover:text-emerald-900 border border-emerald-200 hover:border-emerald-400 bg-white hover:bg-emerald-50 rounded-lg px-3 py-1.5 transition-all"
            >
              <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/>
                <path d="M12 0C5.373 0 0 5.373 0 12c0 2.123.554 4.112 1.528 5.834L0 24l6.336-1.503A11.956 11.956 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.818a9.818 9.818 0 01-5.002-1.371l-.36-.213-3.732.885.937-3.632-.234-.373A9.818 9.818 0 1112 21.818z"/>
              </svg>
              WhatsApp
            </button>
            <PrintableReport results={results} patientName={patientName} doctorName={doctorName} sessionId={sessionId} />
          </div>

          <div className="w-px h-5 bg-slate-200 hidden sm:block" />

          {/* Sign / export group */}
          <div className="flex items-center gap-1.5 ml-auto flex-wrap">
            {!isSigned && (
              <button
                onClick={handleSignNote}
                className="text-xs font-semibold text-white bg-primary hover:bg-primary-dark px-4 py-1.5 rounded-lg transition-all shadow-sm cursor-pointer"
              >
                Sign Note
              </button>
            )}
            <button
              onClick={handleExportFhir}
              disabled={isExporting}
              className="text-xs font-medium text-slate-500 hover:text-slate-700 border border-slate-200 hover:border-slate-300 bg-white px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50 cursor-pointer"
            >
              {isExporting ? 'Exporting…' : 'Export EMR'}
            </button>
          </div>
        </div>

        <div className="px-6 py-6">

        <div className="space-y-6 text-sm text-slate-800 leading-relaxed">
          {(['S', 'O', 'A', 'P'] as const).map((sectionCode) => {
            const labels: Record<string, string> = {
              S: 'Subjective (Symptoms, History)',
              O: 'Objective (Vitals, Observations)',
              A: 'Assessment (Clinical Impression)',
              P: 'Plan (Medications, Orders, Follow-Up)',
            };
            const label = labels[sectionCode];
            const icd10Code = sectionCode === 'A' && pmjayBeneficiary ? getIcd10(editableSoap.A) : null;
            return (
              <div key={sectionCode} className="group relative border-l-2 border-slate-100 hover:border-primary pl-4 transition-colors">
                <h3 className="font-bold text-text-dark mb-1 flex items-center gap-2 font-serif text-sm flex-wrap">
                  <span className="text-primary font-mono">{sectionCode}.</span>
                  {label}
                  {icd10Code && (
                    <span className="text-[10px] font-bold font-mono text-orange-700 bg-orange-50 border border-orange-200 px-2 py-0.5 rounded uppercase tracking-wider">
                      PMJAY · ICD-10: {icd10Code}
                    </span>
                  )}
                </h3>
                <textarea
                  value={editableSoap[sectionCode]}
                  onChange={(e) => setEditableSoap({ ...editableSoap, [sectionCode]: e.target.value })}
                  disabled={isSigned}
                  className="w-full min-h-[60px] outline-none hover:bg-slate-50/50 focus:bg-slate-50/50 transition-all rounded p-1.5 resize-y text-slate-700 border border-transparent focus:border-slate-200/80 cursor-text disabled:bg-transparent disabled:border-transparent disabled:cursor-default"
                />
              </div>
            );
          })}
        </div>

        <p className="text-[11px] text-slate-500 mt-6 pt-4 border-t border-slate-100 flex items-center gap-1.5">
          <svg className="w-4 h-4 text-slate-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span className="font-medium">This draft requires physician review and signature before clinical use. All clinical decisions remain with the physician.</span>
        </p>
        </div>
      </section>

      {/* CDS Suggestions Section */}
      {cds.length > 0 && (
        <section className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-text-dark font-serif uppercase tracking-wider">Clinical Decision Support Alerts</h2>
          </div>
          <div className="grid gap-3">
            {cds.map((alert, idx) => {
              const isCritical = alert.urgency === 'critical';
              const isHigh = alert.urgency === 'high';
              const isMedium = alert.urgency === 'medium';

              let cardStyle = 'border-amber-200 bg-amber-50/40 text-amber-900';
              let badgeStyle = 'bg-amber-100 text-amber-700 border-amber-200';
              let textStyle = 'text-amber-950 font-bold';

              if (isCritical || isHigh) {
                cardStyle = 'border-red-200 bg-red-50/50 text-alert-critical';
                badgeStyle = 'bg-red-100 text-alert-critical border-red-200';
                textStyle = 'text-red-950 font-bold';
              } else if (isMedium) {
                cardStyle = 'border-orange-200 bg-orange-50/30 text-orange-900';
                badgeStyle = 'bg-orange-100 text-orange-700 border-orange-200';
                textStyle = 'text-orange-950 font-bold';
              }

              return (
                <div key={idx} className={`p-4 rounded border flex flex-col sm:flex-row sm:items-start gap-3 shadow-xs ${cardStyle}`}>
                  <div className="flex-grow">
                    <div className="flex items-center gap-2 mb-1.5">
                      <h4 className={`text-sm ${textStyle}`}>{alert.suggestion}</h4>
                      <span className={`text-[9px] font-extrabold uppercase tracking-wider px-1.5 py-0.5 rounded border ${badgeStyle}`}>
                        {alert.urgency}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 leading-relaxed font-medium">{alert.rationale}</p>
                  </div>
                  <div className="sm:text-right shrink-0">
                    <span className="text-[10px] font-bold text-slate-500 bg-white border border-slate-200 px-2 py-1 rounded shadow-xs uppercase tracking-wider">
                      {alert.safety_label.replace(/_/g, ' ')}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Extracted Clinical Entities */}
      <section className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
          <h2 className="text-sm font-bold text-text-dark font-serif uppercase tracking-wider">Extracted Clinical Entities</h2>
          <span className="text-[10px] text-slate-400 font-bold tracking-widest uppercase">Hover for Context</span>
        </div>
        <div className="grid sm:grid-cols-2 gap-x-8 gap-y-6">

          <div>
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2.5">Symptoms Detected</h3>
            {state.symptoms.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {state.symptoms.map(s => (
                  <span key={s} title={state.contexts?.[s] || "No context recorded"} className="px-2 py-1 bg-slate-50 border border-slate-200 rounded text-xs font-medium text-slate-700 cursor-help hover:border-primary/50 transition-colors">
                    {s}
                  </span>
                ))}
              </div>
            ) : <p className="text-xs text-slate-400 italic">None detected</p>}
          </div>

          <div>
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2.5">Allergies Reported</h3>
            {state.allergies.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {state.allergies.map(a => (
                  <span key={a} title={state.contexts?.[a] || "No context recorded"} className="px-2 py-1 bg-red-50 text-alert-critical border border-red-200 rounded text-xs font-semibold cursor-help hover:border-red-400 transition-colors">
                    {a}
                  </span>
                ))}
              </div>
            ) : <p className="text-xs text-slate-400 italic">None reported</p>}
          </div>

          <div>
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2.5">Vitals Extracted</h3>
            {state.vitals.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {state.vitals.map(v => (
                  <span key={v} title={state.contexts?.[v] || "No context recorded"} className="px-2 py-1 bg-white text-slate-700 border border-slate-200 rounded shadow-xs text-xs font-semibold cursor-help hover:border-primary/50 transition-colors">
                    {v}
                  </span>
                ))}
              </div>
            ) : <p className="text-xs text-slate-400 italic">None extracted</p>}
          </div>

          <div className="sm:col-span-2">
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2.5">Medications Prescribed</h3>
            {Object.keys(state.medications).length > 0 ? (
              <div className="grid sm:grid-cols-2 gap-3">
                {Object.entries(state.medications).map(([name, details]) => (
                  <div key={name} title={state.contexts?.[name] || "No context recorded"} className="p-3 bg-white border border-slate-200 rounded shadow-xs flex items-start justify-between cursor-help hover:border-primary/50 transition-colors">
                    <div>
                      <span className="font-bold text-text-dark text-sm block">{name.charAt(0).toUpperCase() + name.slice(1)}</span>
                      <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
                        {details.dosage && <span>{details.dosage}</span>}
                        {details.dosage && details.frequency && <span>•</span>}
                        {details.frequency && <span className="font-semibold text-primary">{details.frequency}</span>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : <p className="text-xs text-slate-400 italic">None prescribed</p>}
          </div>

        </div>
      </section>

      {/* FHIR Export Modal */}
      {fhirData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[80vh] flex flex-col overflow-hidden border border-slate-200">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <h3 className="text-sm font-bold text-text-dark uppercase tracking-wider">HL7 FHIR R4 Bundle Payload</h3>
              <button onClick={() => setFhirData(null)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6 overflow-y-auto flex-grow bg-slate-950 text-emerald-400 font-mono text-xs leading-relaxed">
              <pre className="whitespace-pre-wrap break-all">
                {JSON.stringify(fhirData, null, 2)}
              </pre>
            </div>
            <div className="px-6 py-3 border-t border-slate-200 bg-slate-50 flex justify-end">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(JSON.stringify(fhirData, null, 2));
                  alert('Copied FHIR bundle to clipboard!');
                }}
                className="text-xs font-semibold bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded shadow-sm transition-colors cursor-pointer"
              >
                Copy to Clipboard
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
