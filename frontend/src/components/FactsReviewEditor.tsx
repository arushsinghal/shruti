import { useState } from 'react';
import type { ProcessClinicalResponse, DeterministicMedication, ExtractedFact } from '../types/clinical';
import { finalizeReviewedFacts, reviewExtractedFact, updateFactsAndRegenerate, submitExtractionFeedback } from '../lib/api';

interface Props {
  results: ProcessClinicalResponse;
  sessionId: string;
  onConfirm: (updated: ProcessClinicalResponse) => void;
  onSkip: () => void;
}

export default function FactsReviewEditor({ results, sessionId, onConfirm, onSkip }: Props) {
  const [evidenceFacts, setEvidenceFacts] = useState<ExtractedFact[]>(results.extracted_facts ?? []);
  const [previewSoap, setPreviewSoap] = useState(results.soap);
  const [symptoms, setSymptoms] = useState<string[]>([...results.facts.symptoms]);
  const [medications, setMedications] = useState<DeterministicMedication[]>(
    results.facts.medications.map(m => ({ ...m })),
  );
  const [vitals, setVitals] = useState<string[]>([...results.facts.vitals]);
  const [allergies, setAllergies] = useState<string[]>([...results.facts.allergies]);
  const [investigations, setInvestigations] = useState<string[]>([...results.facts.investigations]);
  const [diagnoses, setDiagnoses] = useState<string[]>([...(results.facts as any).diagnoses ?? []]);
  const [followUp, setFollowUp] = useState<string[]>([...(results.facts as any).follow_up ?? []]);

  const [saving, setSaving] = useState(false);
  const [newItem, setNewItem] = useState('');
  const [addingTo, setAddingTo] = useState<string | null>(null);

  // Feedback state
  const [feedbackField, setFeedbackField] = useState<string | null>(null);
  const [feedbackOriginal, setFeedbackOriginal] = useState('');
  const [feedbackCorrected, setFeedbackCorrected] = useState('');
  const [feedbackType, setFeedbackType] = useState<'missing' | 'wrong' | 'extra'>('wrong');
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [correctionToast, setCorrectionToast] = useState(false);

  function applyUpdatedResults(updated: ProcessClinicalResponse) {
    setEvidenceFacts(updated.extracted_facts ?? []);
    setPreviewSoap(updated.soap);
    setSymptoms([...(updated.facts.symptoms ?? [])]);
    setMedications((updated.facts.medications ?? []).map(m => ({ ...m })));
    setVitals([...(updated.facts.vitals ?? [])]);
    setAllergies([...(updated.facts.allergies ?? [])]);
    setInvestigations([...(updated.facts.investigations ?? [])]);
    setDiagnoses([...(updated.facts as any).diagnoses ?? []]);
    setFollowUp([...(updated.facts as any).follow_up ?? []]);
  }

  async function handleFactReview(fact: ExtractedFact, action: 'accept' | 'edit' | 'reject') {
    let value = fact.normalized_value;
    if (action === 'edit') {
      const next = window.prompt('Correct this fact', fact.normalized_value);
      if (!next || !next.trim()) return;
      value = next.trim();
    }
    setSaving(true);
    try {
      const updated = await reviewExtractedFact(sessionId, fact.id, action, value, fact.metadata ?? {});
      applyUpdatedResults(updated);
    } catch (e) {
      console.error(e);
      alert('Failed to update evidence review.');
    } finally {
      setSaving(false);
    }
  }

  async function handleFinalizeEvidence() {
    setSaving(true);
    try {
      const updated = await finalizeReviewedFacts(sessionId);
      onConfirm(updated);
    } catch (e) {
      console.error(e);
      alert('Failed to finalize reviewed facts.');
    } finally {
      setSaving(false);
    }
  }

  function highlightEvidence(fact: ExtractedFact) {
    const sentence = fact.source_sentence || 'Doctor-entered correction';
    const raw = fact.raw_text;
    if (!raw || !sentence.toLowerCase().includes(raw.toLowerCase())) {
      return sentence;
    }
    const idx = sentence.toLowerCase().indexOf(raw.toLowerCase());
    return (
      <>
        {sentence.slice(0, idx)}
        <mark className="rounded bg-yellow-100 px-0.5 text-yellow-900">{sentence.slice(idx, idx + raw.length)}</mark>
        {sentence.slice(idx + raw.length)}
      </>
    );
  }

  function factHasProof(fact: ExtractedFact): boolean {
    if (fact.extractor === 'doctor') return true;
    return (fact.evidence_spans ?? []).some(span => (
      span.start_char >= 0 &&
      span.end_char > span.start_char &&
      Boolean(span.raw_text)
    ));
  }

  function validationIssue(fact: ExtractedFact): string | null {
    const issue = fact.metadata?.evidence_validation;
    return typeof issue === 'string' ? issue.replaceAll('_', ' ') : null;
  }

  function hasEdits(): boolean {
    const orig = results.facts;
    if (JSON.stringify(symptoms) !== JSON.stringify(orig.symptoms)) return true;
    if (JSON.stringify(medications) !== JSON.stringify(orig.medications)) return true;
    if (JSON.stringify(vitals) !== JSON.stringify(orig.vitals)) return true;
    if (JSON.stringify(allergies) !== JSON.stringify(orig.allergies)) return true;
    if (JSON.stringify(investigations) !== JSON.stringify(orig.investigations)) return true;
    if (JSON.stringify(diagnoses) !== JSON.stringify((orig as any).diagnoses ?? [])) return true;
    if (JSON.stringify(followUp) !== JSON.stringify((orig as any).follow_up ?? [])) return true;
    return false;
  }

  async function handleConfirm() {
    setSaving(true);
    try {
      const editedFacts = {
        ...results.facts,
        symptoms,
        medications,
        vitals,
        allergies,
        investigations,
        diagnoses,
        follow_up: followUp,
      };
      const updated = await updateFactsAndRegenerate(sessionId, editedFacts);
      if (hasEdits()) {
        setCorrectionToast(true);
        setTimeout(() => setCorrectionToast(false), 3000);
      }
      onConfirm(updated);
    } catch (e) {
      console.error(e);
      alert('Failed to regenerate note. Please try again.');
    } finally {
      setSaving(false);
    }
  }

  async function handleSubmitFeedback() {
    if (!feedbackField) return;
    try {
      await submitExtractionFeedback(sessionId, feedbackField, feedbackOriginal, feedbackCorrected, feedbackType);
      setFeedbackSent(true);
      setFeedbackField(null);
      setTimeout(() => setFeedbackSent(false), 3000);
    } catch {
      alert('Failed to submit feedback.');
    }
  }

  function removeItem(arr: string[], setArr: (v: string[]) => void, idx: number) {
    setArr(arr.filter((_, i) => i !== idx));
  }

  function addItem(arr: string[], setArr: (v: string[]) => void) {
    if (!newItem.trim()) return;
    setArr([...arr, newItem.trim()]);
    setNewItem('');
    setAddingTo(null);
  }

  function removeMed(idx: number) {
    setMedications(medications.filter((_, i) => i !== idx));
  }

  function updateMed(idx: number, field: keyof DeterministicMedication, value: string) {
    setMedications(medications.map((m, i) => i === idx ? { ...m, [field]: value } : m));
  }

  function addMed() {
    setMedications([...medications, { name: '', dosage: '', frequency: '' }]);
  }

  function renderTagSection(
    title: string,
    fieldKey: string,
    items: string[],
    setItems: (v: string[]) => void,
    color: string,
  ) {
    return (
      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">{title}</h3>
          <div className="flex gap-1">
            <button
              onClick={() => { setFeedbackField(fieldKey); setFeedbackOriginal(items.join(', ')); setFeedbackCorrected(''); }}
              className="text-[10px] text-amber-600 hover:text-amber-800 font-medium"
              title="Report extraction error"
            >
              Flag issue
            </button>
            <span className="text-slate-300">|</span>
            <button
              onClick={() => setAddingTo(addingTo === fieldKey ? null : fieldKey)}
              className="text-[10px] text-indigo-600 hover:text-indigo-800 font-medium"
            >
              + Add
            </button>
          </div>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {items.map((item, i) => (
            <span key={i} className={`group px-2 py-1 rounded text-xs font-medium border flex items-center gap-1.5 ${color}`}>
              {item}
              <button
                onClick={() => removeItem(items, setItems, i)}
                className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600 transition-opacity"
              >
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </span>
          ))}
          {items.length === 0 && <span className="text-xs text-slate-400 italic">None detected</span>}
        </div>
        {addingTo === fieldKey && (
          <div className="mt-2 flex gap-2">
            <input
              type="text"
              value={newItem}
              onChange={(e) => setNewItem(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addItem(items, setItems)}
              placeholder={`Add ${title.toLowerCase()}...`}
              className="flex-1 text-xs border border-slate-200 rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-400"
              autoFocus
            />
            <button onClick={() => addItem(items, setItems)} className="text-xs bg-indigo-600 text-white px-3 py-1.5 rounded hover:bg-indigo-700">
              Add
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in-up">
      <section className="bg-white border border-indigo-200 rounded-xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 bg-indigo-50 border-b border-indigo-100 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-indigo-900 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              Review Extracted Facts
            </h2>
            <p className="text-[11px] text-indigo-600 mt-0.5">Add, remove, or correct items before generating the SOAP note.</p>
          </div>
          <span className="text-[10px] font-bold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-1 rounded-full uppercase tracking-wider">
            Needs Review
          </span>
        </div>

        <div className="p-6 space-y-5">
          {evidenceFacts.length > 0 && (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div>
 <h3 className="text-xs font-bold uppercase tracking-widest text-slate-600">Evidence review</h3>
                  <p className="mt-0.5 text-[11px] text-slate-500">No proof means candidate only. Confirmed facts must trace to transcript evidence or doctor entry.</p>
                </div>
 <div className="flex flex-wrap justify-end gap-1">
 <span className="rounded-full bg-white px-2 py-1 text-[10px] font-bold uppercase text-slate-500">
 {evidenceFacts.filter(f => f.review_status === 'confirmed').length} confirmed
 </span>
 <span className="rounded-full bg-white px-2 py-1 text-[10px] font-bold uppercase text-amber-600">
 {evidenceFacts.filter(f => f.review_status === 'candidate').length} candidate
 </span>
 <span className="rounded-full bg-white px-2 py-1 text-[10px] font-bold uppercase text-red-600">
 {evidenceFacts.filter(f => !factHasProof(f)).length} no proof
 </span>
 </div>
              </div>
              <div className="grid gap-2">
                {evidenceFacts.map(fact => (
                  <div key={fact.id} className="rounded-md border border-slate-200 bg-white p-3 text-xs">
                    <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded bg-slate-100 px-1.5 py-0.5 font-bold uppercase text-slate-500">{fact.category.replace('_', ' ')}</span>
                        <span className="font-semibold text-slate-800">{fact.normalized_value}</span>
                        <span className={`rounded-full px-1.5 py-0.5 font-bold uppercase ${
                          fact.review_status === 'confirmed' ? 'bg-emerald-50 text-emerald-700' :
                          fact.review_status === 'rejected' ? 'bg-red-50 text-red-700' :
                          'bg-amber-50 text-amber-700'
                        }`}>
                          {fact.review_status}
                        </span>
                        {fact.certainty !== 'affirmed' && (
                          <span className="rounded-full bg-violet-50 px-1.5 py-0.5 font-bold uppercase text-violet-700">{fact.certainty}</span>
                        )}
                        <span className="font-mono text-[10px] text-slate-400">{fact.extractor} {(fact.confidence * 100).toFixed(0)}%</span>
                        <span className={`rounded-full px-1.5 py-0.5 font-bold uppercase ${
                          factHasProof(fact) ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'
                        }`}>
                          {factHasProof(fact) ? 'proof' : 'no proof'}
                        </span>
                        {validationIssue(fact) && (
                          <span className="rounded-full bg-red-50 px-1.5 py-0.5 font-bold uppercase text-red-700">
                            {validationIssue(fact)}
                          </span>
                        )}
                      </div>
                      <div className="flex gap-1">
                        <button onClick={() => handleFactReview(fact, 'accept')} disabled={saving} className="rounded border border-emerald-200 px-2 py-1 font-semibold text-emerald-700 hover:bg-emerald-50 disabled:opacity-50">
                          Accept
                        </button>
                        <button onClick={() => handleFactReview(fact, 'edit')} disabled={saving} className="rounded border border-indigo-200 px-2 py-1 font-semibold text-indigo-700 hover:bg-indigo-50 disabled:opacity-50">
                          Edit
                        </button>
                        <button onClick={() => handleFactReview(fact, 'reject')} disabled={saving} className="rounded border border-red-200 px-2 py-1 font-semibold text-red-700 hover:bg-red-50 disabled:opacity-50">
                          Reject
                        </button>
                      </div>
                    </div>
                    <p className="leading-relaxed text-slate-600">{highlightEvidence(fact)}</p>
                    {fact.evidence_spans.length > 1 && (
                      <p className="mt-1 text-[11px] text-slate-400">
                        Extra evidence: {fact.evidence_spans.slice(1).map(span => span.raw_text).join(', ')}
                      </p>
                    )}
                  </div>
                ))}
              </div>
              <div className="mt-4 rounded-md border border-white bg-white p-3 text-xs text-slate-600">
                <p className="mb-2 font-bold uppercase tracking-wider text-slate-500">SOAP preview from confirmed facts</p>
                <div className="grid gap-2 md:grid-cols-2">
                  {(['S', 'O', 'A', 'P'] as const).map(key => (
                    <div key={key} className="rounded border border-slate-100 bg-slate-50 p-2">
                      <p className="mb-1 font-mono font-bold text-primary">{key}</p>
                      <p className="whitespace-pre-wrap">{previewSoap?.[key] || 'Not specified'}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {renderTagSection('Symptoms', 'symptoms', symptoms, setSymptoms, 'bg-slate-50 border-slate-200 text-slate-700')}
          {renderTagSection('Vitals', 'vitals', vitals, setVitals, 'bg-white border-slate-200 text-slate-700')}
          {renderTagSection('Allergies', 'allergies', allergies, setAllergies, 'bg-red-50 border-red-200 text-red-700')}
          {renderTagSection('Investigations', 'investigations', investigations, setInvestigations, 'bg-blue-50 border-blue-200 text-blue-700')}
          {renderTagSection('Diagnoses', 'diagnoses', diagnoses, setDiagnoses, 'bg-purple-50 border-purple-200 text-purple-700')}
          {renderTagSection('Follow-up', 'follow_up', followUp, setFollowUp, 'bg-teal-50 border-teal-200 text-teal-700')}

          {/* Medications — editable table */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Medications</h3>
              <div className="flex gap-1">
                <button
                  onClick={() => { setFeedbackField('medications'); setFeedbackOriginal(medications.map(m => m.name).join(', ')); setFeedbackCorrected(''); }}
                  className="text-[10px] text-amber-600 hover:text-amber-800 font-medium"
                >
                  Flag issue
                </button>
                <span className="text-slate-300">|</span>
                <button onClick={addMed} className="text-[10px] text-indigo-600 hover:text-indigo-800 font-medium">
                  + Add medication
                </button>
              </div>
            </div>
            {medications.length > 0 ? (
              <div className="space-y-2">
                {medications.map((med, i) => (
                  <div key={i} className="group flex items-center gap-2 p-2 bg-white border border-slate-200 rounded-lg hover:border-indigo-200 transition-colors">
                    <input
                      type="text"
                      value={med.name}
                      onChange={(e) => updateMed(i, 'name', e.target.value)}
                      placeholder="Name"
                      className="flex-[2] text-sm font-semibold border-0 outline-none bg-transparent text-slate-800 placeholder-slate-300"
                    />
                    <input
                      type="text"
                      value={med.dosage}
                      onChange={(e) => updateMed(i, 'dosage', e.target.value)}
                      placeholder="Dosage"
                      className="flex-1 text-xs border-0 outline-none bg-transparent text-slate-600 placeholder-slate-300"
                    />
                    <input
                      type="text"
                      value={med.frequency}
                      onChange={(e) => updateMed(i, 'frequency', e.target.value)}
                      placeholder="Freq"
                      className="w-16 text-xs font-semibold text-indigo-600 border-0 outline-none bg-transparent placeholder-slate-300"
                    />
                    <button
                      onClick={() => removeMed(i)}
                      className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600 transition-opacity shrink-0"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">None prescribed</p>
            )}
          </div>
        </div>

        {/* Feedback modal */}
        {feedbackField && (
          <div className="mx-6 mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg space-y-3">
            <h4 className="text-xs font-bold text-amber-800">Report extraction issue — {feedbackField}</h4>
            <div className="flex gap-2">
              {(['missing', 'wrong', 'extra'] as const).map(t => (
                <button
                  key={t}
                  onClick={() => setFeedbackType(t)}
                  className={`text-[10px] font-bold px-2 py-1 rounded border ${feedbackType === t ? 'bg-amber-600 text-white border-amber-600' : 'bg-white text-amber-700 border-amber-300'}`}
                >
                  {t}
                </button>
              ))}
            </div>
            <input
              type="text"
              value={feedbackCorrected}
              onChange={(e) => setFeedbackCorrected(e.target.value)}
              placeholder="What should it be? (optional)"
              className="w-full text-xs border border-amber-200 rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-amber-400"
            />
            <div className="flex gap-2">
              <button onClick={handleSubmitFeedback} className="text-xs bg-amber-600 text-white px-3 py-1.5 rounded hover:bg-amber-700 font-semibold">
                Submit feedback
              </button>
              <button onClick={() => setFeedbackField(null)} className="text-xs text-slate-500 hover:text-slate-700">
                Cancel
              </button>
            </div>
          </div>
        )}

        {feedbackSent && (
          <div className="mx-6 mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-700 font-semibold flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </svg>
            Feedback logged — thank you! This helps improve the extraction pipeline.
          </div>
        )}

        {correctionToast && (
          <div className="mx-6 mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-700 font-semibold flex items-center gap-2 animate-fade-in-up">
            <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </svg>
            Correction saved — helps improve future extractions
          </div>
        )}

        {/* Action buttons */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
          <button
            onClick={evidenceFacts.length > 0 ? handleFinalizeEvidence : onSkip}
            className="text-xs text-slate-500 hover:text-slate-700 font-medium"
          >
            {evidenceFacts.length > 0 ? 'Finalize confirmed evidence only' : 'Skip review — use as-is'}
          </button>
          <button
            onClick={handleConfirm}
            disabled={saving}
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-700 hover:to-cyan-700 disabled:opacity-50 text-white text-sm font-bold transition-all shadow-md"
          >
            {saving ? 'Regenerating SOAP...' : 'Confirm & Generate SOAP Note'}
          </button>
        </div>
      </section>
    </div>
  );
}
