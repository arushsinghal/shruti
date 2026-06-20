import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api, { getSession } from '../lib/api';
import type { ConsultationSession } from '../types/clinical';
import { MODE_LABELS, MODE_COLORS } from '../types/clinical';
import { motion } from 'framer-motion';

function TypewriterText({ text }: { text?: string }) {
  if (!text) return null;
  const letters = Array.from(text);
  
  const container = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.005 },
    },
  };
  
  const child = {
    visible: { opacity: 1 },
    hidden: { opacity: 0 },
  };

  return (
    <motion.span variants={container} initial="hidden" animate="visible">
      {letters.map((char, index) => (
        <motion.span variants={child} key={index}>
          {char}
        </motion.span>
      ))}
    </motion.span>
  );
}

// ─── Shared helpers ───────────────────────────────────────────────────────────

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-sm">
      <div className="px-5 py-3 bg-slate-50 border-b border-slate-200">
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">{title}</h3>
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="py-2 border-b border-slate-100 last:border-0 grid grid-cols-[160px_1fr] gap-4">
      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide pt-0.5">{label}</span>
      <span className="text-sm text-slate-800">{value || '—'}</span>
    </div>
  );
}

function Badge({ label, color }: { label: string; color?: string }) {
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold border mr-1 mb-1 ${color || 'bg-slate-100 text-slate-600 border-slate-200'}`}>
      {label}
    </span>
  );
}

// ─── SOAP Health View ─────────────────────────────────────────────────────────

function SOAPView({ 
  soap, 
  cds, 
  session, 
  isEditing, 
  editedSoap, 
  setEditedSoap 
}: { 
  soap: any; 
  cds: any[]; 
  session: ConsultationSession;
  isEditing: boolean;
  editedSoap: { S: string; O: string; A: string; P: string };
  setEditedSoap: React.Dispatch<React.SetStateAction<{ S: string; O: string; A: string; P: string }>>;
}) {
  const simpleSOAP = soap && ('S' in soap || 'O' in soap);

  return (
    <div className="space-y-4">
      {/* Disclaimer */}
      <div className="border border-emerald-200 bg-emerald-50 rounded-lg p-4 flex items-start gap-3">
        <svg className="w-5 h-5 text-emerald-600 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        <div>
          <p className="text-xs font-bold text-emerald-700 uppercase tracking-wide">SOAP Clinical Note</p>
          <p className="text-xs text-emerald-600 mt-0.5">AI-generated draft — requires physician review and co-signature before clinical use.</p>
        </div>
      </div>

      {/* Patient info */}
      <Section title="Patient Details">
        <Field label="Patient" value={session.patient_name || 'Anonymous Patient'} />
        <Field label="Physician" value={session.doctor_name ? `Dr. ${session.doctor_name}` : '—'} />
        <Field label="Date" value={new Date(session.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })} />
      </Section>

      {simpleSOAP ? (
        <>
          <Section title="S — Subjective">
            {isEditing ? (
              <textarea
                value={editedSoap.S}
                onChange={(e) => setEditedSoap({ ...editedSoap, S: e.target.value })}
                className="w-full min-h-[100px] text-sm text-slate-800 bg-white border border-slate-200 rounded p-2.5 outline-none focus:border-indigo-500/50"
              />
            ) : (
              <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                <TypewriterText text={editedSoap.S || soap.S} />
              </p>
            )}
          </Section>
          <Section title="O — Objective">
            {isEditing ? (
              <textarea
                value={editedSoap.O}
                onChange={(e) => setEditedSoap({ ...editedSoap, O: e.target.value })}
                className="w-full min-h-[100px] text-sm text-slate-800 bg-white border border-slate-200 rounded p-2.5 outline-none focus:border-indigo-500/50"
              />
            ) : (
              <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                <TypewriterText text={editedSoap.O || soap.O} />
              </p>
            )}
          </Section>
          <Section title="A — Assessment">
            {isEditing ? (
              <textarea
                value={editedSoap.A}
                onChange={(e) => setEditedSoap({ ...editedSoap, A: e.target.value })}
                className="w-full min-h-[100px] text-sm text-slate-800 bg-white border border-slate-200 rounded p-2.5 outline-none focus:border-indigo-500/50"
              />
            ) : (
              <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                <TypewriterText text={editedSoap.A || soap.A} />
              </p>
            )}
          </Section>
          <Section title="P — Plan">
            {isEditing ? (
              <textarea
                value={editedSoap.P}
                onChange={(e) => setEditedSoap({ ...editedSoap, P: e.target.value })}
                className="w-full min-h-[100px] text-sm text-slate-800 bg-white border border-slate-200 rounded p-2.5 outline-none focus:border-indigo-500/50"
              />
            ) : (
              <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                <TypewriterText text={editedSoap.P || soap.P} />
              </p>
            )}
          </Section>
        </>
      ) : soap ? (
        <>
          <Section title="S — Subjective">
            {soap.subjective?.chief_complaint && <Field label="Chief Complaint" value={<TypewriterText text={soap.subjective.chief_complaint} />} />}
            {soap.subjective?.hpi && <Field label="History" value={<TypewriterText text={soap.subjective.hpi} />} />}
            {soap.subjective?.symptoms?.length > 0 && (
              <Field label="Symptoms" value={
                <div className="flex flex-wrap">{soap.subjective.symptoms.map((s: string) => <Badge key={s} label={s} color="bg-red-50 text-red-700 border-red-200" />)}</div>
              } />
            )}
            {soap.subjective?.allergies?.length > 0 && (
              <Field label="Allergies" value={
                <div className="flex flex-wrap">{soap.subjective.allergies.map((a: string) => <Badge key={a} label={`⚠ ${a}`} color="bg-amber-50 text-amber-700 border-amber-200" />)}</div>
              } />
            )}
          </Section>
          <Section title="O — Objective">
            {soap.objective?.vitals && Object.keys(soap.objective.vitals).length > 0 && (
              <Field label="Vitals" value={
                <div className="flex flex-wrap">
                  {Object.entries(soap.objective.vitals).map(([k, v]) => (
                    <Badge key={k} label={`${k}: ${v}`} color="bg-blue-50 text-blue-700 border-blue-200" />
                  ))}
                </div>
              } />
            )}
            {soap.objective?.labs?.length > 0 && (
              <Field label="Labs Ordered" value={
                <div className="flex flex-wrap">{soap.objective.labs.map((l: string) => <Badge key={l} label={l} />)}</div>
              } />
            )}
          </Section>
          <Section title="A — Assessment">
            {soap.assessment?.diagnosis && <Field label="Diagnosis" value={<TypewriterText text={soap.assessment.diagnosis} />} />}
            {soap.assessment?.impression && <Field label="Impression" value={<TypewriterText text={soap.assessment.impression} />} />}
            {soap.assessment?.differentials?.length > 0 && (
              <Field label="Differentials" value={<TypewriterText text={soap.assessment.differentials.join('; ')} />} />
            )}
          </Section>
          <Section title="P — Plan">
            {soap.plan?.medications?.length > 0 && (
              <Field label="Medications" value={
                <div className="space-y-1">
                  {soap.plan.medications.map((m: any, i: number) => (
                    <p key={i} className="text-sm text-slate-700">
                      <TypewriterText text={`${m.name} ${m.dose || m.dosage || ''} ${m.frequency || ''}`} />
                    </p>
                  ))}
                </div>
              } />
            )}
            {soap.plan?.investigations?.length > 0 && <Field label="Investigations" value={<TypewriterText text={soap.plan.investigations.join(', ')} />} />}
            {soap.plan?.follow_up && <Field label="Follow-up" value={<TypewriterText text={soap.plan.follow_up} />} />}
            {soap.plan?.red_flags?.length > 0 && <Field label="Red Flags" value={<TypewriterText text={soap.plan.red_flags.join('; ')} />} />}
          </Section>
        </>
      ) : (
        <div className="text-center py-12 text-slate-400 text-sm">No SOAP note generated yet.</div>
      )}

      {/* CDS Alerts */}
      {cds && cds.length > 0 && (
        <Section title="Clinical Decision Support Alerts">
          <div className="space-y-3">
            {cds.map((alert: any, i: number) => {
              const urgencyColor = alert.urgency === 'critical' ? 'border-red-200 bg-red-50' :
                alert.urgency === 'high' ? 'border-orange-200 bg-orange-50' :
                alert.urgency === 'medium' ? 'border-amber-200 bg-amber-50' : 'border-slate-200 bg-slate-50';
              const textColor = alert.urgency === 'critical' ? 'text-red-700' :
                alert.urgency === 'high' ? 'text-orange-700' :
                alert.urgency === 'medium' ? 'text-amber-700' : 'text-slate-700';
              return (
                <div key={i} className={`border rounded-lg p-3 ${urgencyColor}`}>
                  <p className={`text-sm font-semibold ${textColor}`}>{alert.suggestion}</p>
                  <p className="text-xs text-slate-500 mt-1">{alert.rationale}</p>
                  <span className={`inline-block mt-1 text-[10px] font-bold uppercase tracking-wide ${textColor}`}>{alert.urgency} priority</span>
                </div>
              );
            })}
          </div>
        </Section>
      )}
    </div>
  );
}

// ─── FIR Government View ──────────────────────────────────────────────────────

function FIRView({ fir, session: _session }: { fir: any; session: ConsultationSession }) {
  if (!fir) return <div className="text-center py-12 text-slate-400 text-sm">No FIR document generated yet.</div>;

  return (
    <div className="space-y-4">
      <div className="border border-stone-300 bg-stone-100 rounded-lg p-4 flex items-start gap-3">
        <svg className="w-5 h-5 text-stone-600 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div>
          <p className="text-xs font-bold text-stone-700 uppercase tracking-wide">First Information Report (FIR) — Draft</p>
          <p className="text-xs text-stone-600 mt-0.5">AI-generated draft — requires officer verification and official registration at the police station.</p>
        </div>
      </div>

      {/* Official Header */}
      <div className="border border-stone-200 rounded-lg bg-white p-6 text-center shadow-sm">
        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Government of India</p>
        <h2 className="text-lg font-bold text-slate-800">FIRST INFORMATION REPORT</h2>
        <p className="text-xs text-slate-500 mt-0.5">(Under Section 154 Cr.P.C.)</p>
        <div className="mt-4 grid grid-cols-3 gap-4 text-left text-xs">
          <div><span className="font-semibold text-slate-500">FIR No.</span><br /><span className="font-bold text-slate-800">{fir.fir_number}</span></div>
          <div><span className="font-semibold text-slate-500">Date</span><br /><span className="font-bold text-slate-800">{fir.date_of_filing}</span></div>
          <div><span className="font-semibold text-slate-500">Time</span><br /><span className="font-bold text-slate-800">{fir.time_of_filing}</span></div>
        </div>
      </div>

      <Section title="Station Details">
        <Field label="Police Station" value={fir.police_station} />
        <Field label="District" value={fir.district} />
        <Field label="Investigating Officer" value={fir.investigating_officer} />
      </Section>

      <Section title="Complainant Information">
        <Field label="Name" value={fir.complainant_name} />
        <Field label="Address" value={fir.complainant_address} />
      </Section>

      <Section title="Accused Information">
        <Field label="Name / Description" value={fir.accused_name} />
      </Section>

      <Section title="Incident Details">
        <Field label="Date of Incident" value={<TypewriterText text={fir.date_of_incident} />} />
        <Field label="Place" value={<TypewriterText text={fir.place_of_incident} />} />
        <Field label="Property Involved" value={<TypewriterText text={fir.property_involved} />} />
      </Section>

      <Section title="Offences Alleged">
        <div className="space-y-1">
          {(fir.offences_alleged || []).map((o: string, i: number) => (
            <p key={i} className="text-sm text-slate-700 font-medium"><TypewriterText text={o} /></p>
          ))}
        </div>
      </Section>

      <Section title="Complainant's Statement">
        <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap"><TypewriterText text={fir.incident_summary} /></p>
      </Section>

      <Section title="Witnesses">
        <div className="space-y-1">
          {(fir.witnesses || []).map((w: string, i: number) => (
            <p key={i} className="text-sm text-slate-700">{i + 1}. <TypewriterText text={w} /></p>
          ))}
        </div>
      </Section>

      <Section title="Action Taken">
        <p className="text-sm text-slate-700"><TypewriterText text={fir.action_taken} /></p>
      </Section>

      <div className="border border-slate-200 rounded-lg bg-white p-5 shadow-sm">
        <div className="grid grid-cols-2 gap-8 mt-4">
          <div className="border-t border-slate-300 pt-3 text-center text-xs text-slate-400">Complainant's Signature / Thumb Impression</div>
          <div className="border-t border-slate-300 pt-3 text-center text-xs text-slate-400">Station House Officer (SHO)</div>
        </div>
      </div>
    </div>
  );
}

// ─── Legal Document View ──────────────────────────────────────────────────────

function LegalView({ doc, session: _session }: { doc: any; session: ConsultationSession }) {
  if (!doc) return <div className="text-center py-12 text-slate-400 text-sm">No legal document generated yet.</div>;

  return (
    <div className="space-y-4">
      <div className="border border-indigo-200 bg-indigo-50 rounded-lg p-4 flex items-start gap-3">
        <svg className="w-5 h-5 text-indigo-600 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
        </svg>
        <div>
          <p className="text-xs font-bold text-indigo-700 uppercase tracking-wide">Legal Document — Draft</p>
          <p className="text-xs text-indigo-600 mt-0.5">AI-generated draft — requires advocate review, notarisation, and court filing.</p>
        </div>
      </div>

      <div className="border border-indigo-100 rounded-lg bg-white p-6 text-center shadow-sm">
        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Before The</p>
        <h2 className="text-base font-bold text-slate-800">{doc.court_name}</h2>
        <p className="text-xs text-slate-500 mt-1">Case No: {doc.case_number} · {doc.date}</p>
        <p className="mt-3 text-sm font-bold text-slate-800">{doc.document_type}</p>
        <p className="text-xs text-slate-500 mt-0.5">Ref: {doc.document_ref}</p>
      </div>

      <Section title="Parties">
        <Field label="Petitioner / Plaintiff" value={doc.petitioner} />
        <Field label="Respondent / Defendant" value={doc.respondent} />
        <Field label="Counsel / Advocate" value={doc.advocate} />
      </Section>

      <Section title="Legal Sections Cited">
        <div className="space-y-1">
          {(doc.legal_sections_cited || []).map((s: string, i: number) => (
            <p key={i} className="text-sm text-slate-700 font-medium">{s}</p>
          ))}
        </div>
      </Section>

      <Section title="Facts of the Case">
        <div className="space-y-2">
          {(doc.facts_of_the_case || []).map((f: string, i: number) => (
            <p key={i} className="text-sm text-slate-700 leading-relaxed">{f}</p>
          ))}
        </div>
      </Section>

      <Section title="Reliefs Sought">
        <div className="space-y-1">
          {(doc.reliefs_sought || []).map((r: string, i: number) => (
            <p key={i} className="text-sm text-slate-700">{String.fromCharCode(97 + i)}. {r}</p>
          ))}
        </div>
      </Section>

      <Section title="Verification">
        <p className="text-sm text-slate-700 leading-relaxed italic">{doc.verification}</p>
        <p className="text-xs text-amber-600 mt-2 font-semibold">⚠ Status: {doc.status}</p>
      </Section>

      <div className="border border-slate-200 rounded-lg bg-white p-5 shadow-sm">
        <div className="grid grid-cols-2 gap-8 mt-4">
          <div className="border-t border-slate-300 pt-3 text-center text-xs text-slate-400">Deponent's Signature</div>
          <div className="border-t border-slate-300 pt-3 text-center text-xs text-slate-400">Advocate / Notary</div>
        </div>
      </div>
    </div>
  );
}

// ─── General View ─────────────────────────────────────────────────────────────

function GeneralView({ doc }: { doc: any }) {
  if (!doc) return <div className="text-center py-12 text-slate-400 text-sm">No transcript summary generated yet.</div>;

  return (
    <div className="space-y-4">
      <div className="border border-slate-200 bg-slate-50 rounded-lg p-4 flex items-start gap-3">
        <svg className="w-5 h-5 text-slate-500 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <div>
          <p className="text-xs font-bold text-slate-600 uppercase tracking-wide">General Transcript Summary</p>
          <p className="text-xs text-slate-500 mt-0.5">Auto-summarised transcript with extracted action items.</p>
        </div>
      </div>
      <Section title="Transcription Info">
        <Field label="Status" value={doc.S} />
        <Field label="Analysis" value={doc.O} />
      </Section>
      <Section title="Summary">
        <p className="text-sm text-slate-700 leading-relaxed">{doc.A}</p>
      </Section>
      <Section title="Action Items">
        <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">{doc.P}</p>
      </Section>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

const CATEGORY_LABELS: Record<string, string> = {
  missing_symptom: "Missing symptom",
  wrong_medication: "Wrong medication",
  wrong_dosage: "Wrong dosage",
  formatting_issue: "Formatting issue",
  language_issue: "Language issue",
  diagnosis_issue: "Diagnosis issue",
  hallucinated_fact: "Hallucinated fact",
  other: "Other"
};

export default function ReviewNote() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [session, setSession] = useState<ConsultationSession | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [isEditing, setIsEditing] = useState(false);
  const [rejectMode, setRejectMode] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState('');
  const [editedSoap, setEditedSoap] = useState({ S: '', O: '', A: '', P: '' });

  useEffect(() => {
    if (!id) return;
    getSession(id)
      .then((s) => {
        setSession(s);
        if (s.soap_note) {
          const soap = s.soap_note as any;
          setEditedSoap({
            S: soap.S || '',
            O: soap.O || '',
            A: soap.A || '',
            P: soap.P || ''
          });
        }
      })
      .catch(() => setError('Session not found'));
  }, [id]);

  const handleAccept = async () => {
    if (!id || !session) return;
    try {
      await api.post(`/sessions/${id}/feedback`, {
        status: 'accept',
        original_soap: session.soap_note,
        final_soap: session.soap_note,
        categories: []
      });
      setFeedbackSubmitted(true);
      setFeedbackMessage('Feedback saved for pilot evaluation.');
    } catch (e) {
      console.error(e);
      alert('Failed to submit feedback');
    }
  };

  const handleEditToggle = () => {
    if (isEditing) {
      setIsEditing(false);
    } else {
      setIsEditing(true);
      setRejectMode(false);
    }
  };

  const toggleCategory = (catKey: string) => {
    if (selectedCategories.includes(catKey)) {
      setSelectedCategories(selectedCategories.filter(c => c !== catKey));
    } else {
      setSelectedCategories([...selectedCategories, catKey]);
    }
  };

  const submitFeedback = async () => {
    if (!id || !session) return;
    const status = rejectMode ? 'reject' : 'edit';
    try {
      await api.post(`/sessions/${id}/feedback`, {
        status,
        original_soap: session.soap_note,
        final_soap: rejectMode ? session.soap_note : editedSoap,
        categories: selectedCategories
      });
      setFeedbackSubmitted(true);
      setFeedbackMessage('Feedback saved for pilot evaluation.');
      setIsEditing(false);
      setRejectMode(false);
    } catch (e) {
      console.error(e);
      alert('Failed to submit feedback');
    }
  };

  if (error) {
    return (
      <div className="min-h-screen bg-bg-warm flex items-center justify-center font-sans">
        <p className="text-sm font-semibold text-red-600 bg-red-50 px-4 py-2 rounded border border-red-100">{error}</p>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen bg-bg-warm flex items-center justify-center font-sans">
        <p className="text-sm text-slate-400 animate-pulse">Loading document...</p>
      </div>
    );
  }

  const mode = session.mode || 'health';
  const doc = session.soap_note as any;
  const cds = (session.cds_suggestions as any[]) || [];

  return (
    <div className="min-h-screen bg-bg-warm pb-20 font-sans text-slate-800">
      {/* Dynamic inline print styles to keep document output high-fidelity */}
      <style dangerouslySetInnerHTML={{__html: `
        @media print {
          body {
            background: white !important;
            color: black !important;
          }
          header, button, nav, footer, .print-hidden, .print\\:hidden {
            display: none !important;
          }
          main {
            padding: 0 !important;
            margin: 0 !important;
            max-width: 100% !important;
          }
          .border {
            border: 1px solid #cbd5e1 !important;
          }
          .bg-slate-50 {
            background-color: #f8fafc !important;
          }
          .shadow-sm, .shadow-md, .shadow-xl {
            box-shadow: none !important;
          }
        }
      `}} />

      <header className="border-b border-slate-200/80 sticky top-0 bg-white/90 backdrop-blur-md z-10 shadow-sm print:hidden">
        <div className="max-w-3xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate(`/consultation/${id}`)}
              className="text-slate-400 hover:text-primary transition-colors flex items-center text-xs font-semibold cursor-pointer"
            >
              <svg className="w-4 h-4 mr-1 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Session
            </button>
            <div className="h-4 w-px bg-slate-200" />
            <div className="flex items-center gap-2">
              <span className="font-bold text-primary text-base">श</span>
              <span className="text-sm font-bold text-text-dark font-sans">Lipi</span>
            </div>
            <div className="h-4 w-px bg-slate-200" />
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide border ${MODE_COLORS[mode]}`}>
              {MODE_LABELS[mode]}
            </span>
          </div>
          <div className="flex items-center gap-3">
            {doc && (
              <button
                onClick={() => window.print()}
                className="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold px-3 py-1.5 rounded transition-all flex items-center gap-1.5 cursor-pointer"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                </svg>
                Print / Export
              </button>
            )}
            <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">
              {session.status.replace(/_/g, ' ')}
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-8">
        
        {/* Printable Lipi Header */}
        <div className="hidden print:block mb-6 border-b-2 border-emerald-600 pb-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-xl font-bold text-slate-900">Lipi Health Clinical Note</h1>
              <p className="text-[10px] text-slate-500">Multilingual Doctor Voice-to-SOAP Clinical Support System</p>
            </div>
            <div className="text-right">
              <p className="text-sm font-bold text-slate-800">{session.doctor_name ? `Dr. ${session.doctor_name}` : 'Lipi Pilot Clinician'}</p>
              <p className="text-[10px] text-slate-400">Generated on {new Date(session.created_at).toLocaleDateString('en-IN')}</p>
            </div>
          </div>
        </div>

        {/* Visible Consent Trust Panel */}
        {session.cloud_ai_consent && (
          <div className="border border-slate-200 rounded-lg p-4 bg-slate-50/50 shadow-xs mb-6 text-xs text-slate-600 print:hidden animate-fade-in-up">
            <div className="flex items-center justify-between font-bold text-slate-700 mb-2 border-b border-slate-100 pb-1.5">
              <div className="flex items-center gap-1.5">
                <svg className="w-4 h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                <span>Consent Audit Trail</span>
              </div>
              <span className="text-[10px] text-slate-400 font-bold tracking-wider">Audit Integrity Hash</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-slate-600">
              <div>
                <span className="block text-[10px] text-slate-400 font-bold uppercase tracking-wider">Consent Captured</span>
                <span className="font-semibold text-emerald-700">✓ Granted</span>
              </div>
              <div>
                <span className="block text-[10px] text-slate-400 font-bold uppercase tracking-wider">Mode</span>
                <span className="font-semibold capitalize">{session.consent_log?.consent_mode || "verbal"}</span>
              </div>
              <div>
                <span className="block text-[10px] text-slate-400 font-bold uppercase tracking-wider">Version</span>
                <span className="font-semibold">{session.consent_log?.consent_text_version || "v1"}</span>
              </div>
              <div>
                <span className="block text-[10px] text-slate-400 font-bold uppercase tracking-wider">Timestamp</span>
                <span className="font-semibold text-slate-700">
                  {session.consent_log?.timestamp 
                    ? new Date(session.consent_log.timestamp).toLocaleString('en-IN', { hour12: true }) 
                    : new Date(session.created_at).toLocaleString('en-IN', { hour12: true })}
                </span>
              </div>
            </div>
            {session.consent_log?.consent_hash && (
              <div className="mt-3 bg-white border border-slate-200 rounded px-2.5 py-1.5 font-mono text-[10px] flex items-center justify-between select-all text-slate-500">
                <span>Hash: {session.consent_log.consent_hash}</span>
                <span className="text-slate-400 font-sans font-bold text-[9px] uppercase">Short: {session.consent_log.consent_hash.slice(0, 8)}...{session.consent_log.consent_hash.slice(-8)}</span>
              </div>
            )}
          </div>
        )}

        {!doc ? (
          <div className="text-center py-20 border border-dashed border-slate-200 rounded-lg bg-white shadow-sm print:hidden">
            <svg className="w-10 h-10 mx-auto mb-4 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-sm font-semibold text-slate-500">No document generated yet</p>
            <p className="text-xs text-slate-400 mt-1">Go back to the consultation and run "Begin Documentation".</p>
            <button
              onClick={() => navigate(`/consultation/${id}`)}
              className="mt-4 bg-primary hover:bg-primary-dark text-white text-xs font-semibold px-4 py-2 rounded transition-all shadow-sm cursor-pointer"
            >
              Go to Consultation →
            </button>
          </div>
        ) : mode === 'government' ? (
          <FIRView fir={doc} session={session} />
        ) : mode === 'legal' ? (
          <LegalView doc={doc} session={session} />
        ) : mode === 'general' ? (
          <GeneralView doc={doc} />
        ) : (
          <SOAPView 
            soap={doc} 
            cds={cds} 
            session={session} 
            isEditing={isEditing} 
            editedSoap={editedSoap} 
            setEditedSoap={setEditedSoap} 
          />
        )}

        {/* Printable disclaimer footer */}
        <div className="hidden print:block mt-8 pt-4 border-t border-slate-200 text-[10px] text-slate-500 text-center">
          <p className="font-semibold text-slate-700">“Doctor must review and sign off before clinical use”</p>
          <p className="mt-1">Generated by Lipi on {new Date(session.created_at).toLocaleString('en-IN')}</p>
          <p className="mt-1 text-[8px]">This is an AI-assisted draft documentation. The physician retains final authority and accountability.</p>
        </div>

        {/* Doctor Review & Feedback Controls */}
        {doc && mode === 'health' && (
          <section className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm mt-6 print:hidden">
            <h2 className="text-sm font-bold text-text-dark font-serif uppercase tracking-wider mb-4 pb-2 border-b border-slate-100 flex items-center gap-2">
              <svg className="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              Doctor Review & Feedback
            </h2>

            {feedbackSubmitted ? (
              <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-4 rounded-lg text-sm font-semibold flex items-center gap-2">
                <svg className="w-5 h-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {feedbackMessage}
              </div>
            ) : (
              <div className="space-y-4">
                {isEditing ? (
                  <p className="text-xs text-slate-500">
                    Make direct changes in the note sections above, select any correction categories, and save your feedback.
                  </p>
                ) : (
                  <p className="text-xs text-slate-500">
                    Review the generated draft note. You can Accept, Edit, or Reject it to save clinical metrics.
                  </p>
                )}

                <div className="flex flex-wrap gap-3">
                  {!isEditing && (
                    <button
                      onClick={handleAccept}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg transition-colors cursor-pointer"
                    >
                      Accept & Save
                    </button>
                  )}
                  
                  <button
                    onClick={handleEditToggle}
                    className={`px-4 py-2 text-xs font-bold rounded-lg transition-colors cursor-pointer ${
                      isEditing 
                        ? 'bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300' 
                        : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                    }`}
                  >
                    {isEditing ? 'Cancel Edit' : 'Edit & Save'}
                  </button>

                  {!isEditing && (
                    <button
                      onClick={() => {
                        setRejectMode(true);
                        setIsEditing(false);
                      }}
                      className="px-4 py-2 bg-slate-100 hover:bg-red-50 hover:text-red-700 text-slate-700 border border-slate-300 text-xs font-bold rounded-lg transition-colors cursor-pointer"
                    >
                      Reject Note
                    </button>
                  )}
                </div>

                {(isEditing || rejectMode) && (
                  <div className="pt-4 border-t border-slate-100 space-y-3">
                    <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider">
                      Correction Categories (Select all that apply)
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(CATEGORY_LABELS).map(([catKey, catLabel]) => {
                        const isSelected = selectedCategories.includes(catKey);
                        return (
                          <button
                            key={catKey}
                            onClick={() => toggleCategory(catKey)}
                            className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all cursor-pointer ${
                              isSelected 
                                ? 'bg-indigo-50 border-indigo-300 text-indigo-700'
                                : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                            }`}
                          >
                            {catLabel}
                          </button>
                        );
                      })}
                    </div>

                    <div className="pt-2 flex justify-end gap-2">
                      {rejectMode && (
                        <button
                          onClick={() => {
                            setRejectMode(false);
                            setSelectedCategories([]);
                          }}
                          className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-lg transition-colors cursor-pointer"
                        >
                          Cancel
                        </button>
                      )}
                      <button
                        onClick={submitFeedback}
                        className="px-5 py-2 bg-primary hover:bg-primary-dark text-white text-xs font-bold rounded-lg shadow-sm transition-colors cursor-pointer"
                      >
                        {rejectMode ? 'Submit Rejection' : 'Submit Edits & Feedback'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
