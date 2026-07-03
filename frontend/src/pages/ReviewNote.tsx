import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api, { getSession } from '../lib/api';
import type { ConsultationSession } from '../types/clinical';
import { MODE_LABELS, MODE_COLORS } from '../types/clinical';
import { motion } from 'framer-motion';

function ReferralModal({ sessionId }: { sessionId: string }) {
  const [open, setOpen] = useState(false);
  const [toDoctor, setToDoctor] = useState('');
  const [specialty, setSpecialty] = useState('');
  const [reason, setReason] = useState('');
  const [urgency, setUrgency] = useState<'routine' | 'urgent'>('routine');
  const [loading, setLoading] = useState(false);

  async function generate() {
    if (!toDoctor.trim()) return;
    setLoading(true);
    try {
      const resp = await api.post(`/sessions/${sessionId}/referral`,
        { to_doctor: toDoctor, to_specialty: specialty, reason, urgency },
        { responseType: 'blob' }
      );
      const url = URL.createObjectURL(new Blob([resp.data], { type: 'application/pdf' }));
      const a = document.createElement('a');
      a.href = url; a.download = `referral-${sessionId.slice(0, 8)}.pdf`; a.click();
      URL.revokeObjectURL(url);
      setOpen(false);
    } catch { alert('Could not generate referral letter.'); }
    finally { setLoading(false); }
  }

  return (
    <>
      <button onClick={() => setOpen(true)}
        className="border border-violet-300 hover:bg-violet-50 text-violet-700 text-xs font-semibold px-3 py-1.5 rounded transition-all flex items-center gap-1.5 cursor-pointer print:hidden">
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
        Refer
      </button>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-md mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[14px] font-bold text-slate-900">Referral Letter</h3>
              <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-slate-600">✕</button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-500 mb-1">Refer to Doctor *</label>
                <input value={toDoctor} onChange={e => setToDoctor(e.target.value)}
                  placeholder="Dr. Sharma"
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-400" />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-500 mb-1">Specialty</label>
                <input value={specialty} onChange={e => setSpecialty(e.target.value)}
                  placeholder="Cardiology, Neurology…"
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-400" />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-500 mb-1">Reason for referral</label>
                <textarea value={reason} onChange={e => setReason(e.target.value)}
                  rows={2} placeholder="Further evaluation of…"
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-400 resize-none" />
              </div>
              <div className="flex items-center gap-3">
                {(['routine', 'urgent'] as const).map(u => (
                  <button key={u} onClick={() => setUrgency(u)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${urgency === u ? (u === 'urgent' ? 'bg-red-50 border-red-300 text-red-700' : 'bg-violet-50 border-violet-300 text-violet-700') : 'border-slate-200 text-slate-500'}`}>
                    {u.charAt(0).toUpperCase() + u.slice(1)}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex gap-2 mt-5">
              <button onClick={() => setOpen(false)} className="flex-1 border border-slate-200 text-slate-600 text-sm font-semibold py-2 rounded-lg hover:bg-slate-50">Cancel</button>
              <button onClick={generate} disabled={loading || !toDoctor.trim()}
                className="flex-1 bg-violet-600 hover:bg-violet-700 disabled:opacity-40 text-white text-sm font-semibold py-2 rounded-lg transition-all">
                {loading ? 'Generating…' : 'Download PDF'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function TpaClaimModal({ sessionId }: { sessionId: string }) {
  const [open, setOpen] = useState(false);
  const [policy, setPolicy] = useState('');
  const [insurer, setInsurer] = useState('');
  const [tpa, setTpa] = useState('');
  const [loading, setLoading] = useState(false);

  async function generate() {
    setLoading(true);
    try {
      const resp = await api.post(`/sessions/${sessionId}/tpa-claim`,
        { policy_number: policy, insurer_name: insurer, tpa_name: tpa },
        { responseType: 'blob' }
      );
      const url = URL.createObjectURL(new Blob([resp.data], { type: 'application/pdf' }));
      const a = document.createElement('a');
      a.href = url; a.download = `tpa-claim-${sessionId.slice(0, 8)}.pdf`; a.click();
      URL.revokeObjectURL(url);
      setOpen(false);
    } catch { alert('Could not generate TPA claim.'); }
    finally { setLoading(false); }
  }

  return (
    <>
      <button onClick={() => setOpen(true)}
        className="border border-blue-300 hover:bg-blue-50 text-blue-700 text-xs font-semibold px-3 py-1.5 rounded transition-all flex items-center gap-1.5 cursor-pointer print:hidden">
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z" />
        </svg>
        TPA Claim
      </button>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-md mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[14px] font-bold text-slate-900">Insurance / TPA Claim</h3>
              <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-slate-600">✕</button>
            </div>
            <p className="text-[12px] text-slate-500 mb-4">Fill patient's insurance details. Leave blank if unknown — PDF will have fields for manual entry.</p>
            <div className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-500 mb-1">Policy Number</label>
                <input value={policy} onChange={e => setPolicy(e.target.value)}
                  placeholder="POL-XXXXXXXXXX"
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-blue-400" />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-500 mb-1">Insurer</label>
                <input value={insurer} onChange={e => setInsurer(e.target.value)}
                  placeholder="Star Health, HDFC ERGO, PMJAY…"
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-500 mb-1">TPA Name</label>
                <input value={tpa} onChange={e => setTpa(e.target.value)}
                  placeholder="Medi Assist, MD India…"
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
              </div>
            </div>
            <div className="flex gap-2 mt-5">
              <button onClick={() => setOpen(false)} className="flex-1 border border-slate-200 text-slate-600 text-sm font-semibold py-2 rounded-lg hover:bg-slate-50">Cancel</button>
              <button onClick={generate} disabled={loading}
                className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white text-sm font-semibold py-2 rounded-lg transition-all">
                {loading ? 'Generating…' : 'Download Claim PDF'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

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

const SOAP_SECTION_COLORS: Record<string, string> = {
  'S — Subjective': 'border-l-blue-400 bg-blue-50/30',
  'O — Objective':  'border-l-purple-400 bg-purple-50/30',
  'A — Assessment': 'border-l-red-400 bg-red-50/30',
  'P — Plan':       'border-l-green-400 bg-green-50/30',
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  const accent = SOAP_SECTION_COLORS[title];
  return (
    <div className={`border border-slate-200 rounded-lg overflow-hidden bg-white shadow-sm ${accent ? 'border-l-4 ' + accent.split(' ')[0] : ''}`}>
      <div className={`px-5 py-3 border-b border-slate-200 ${accent ? accent.split(' ')[1] : 'bg-slate-50'}`}>
        <h3 className="text-xs font-bold text-slate-600 uppercase tracking-widest">{title}</h3>
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
  const [extractedFacts, setExtractedFacts] = useState<any[]>([]);
  const [confirmingFactId, setConfirmingFactId] = useState<string | null>(null);
  const [editingFactId, setEditingFactId] = useState<string | null>(null);
  const [editingValue, setEditingValue] = useState('');
  const [showAddFact, setShowAddFact] = useState(false);
  const [addFactCategory, setAddFactCategory] = useState('symptom');
  const [addFactValue, setAddFactValue] = useState('');
  const [addingFact, setAddingFact] = useState(false);
  const [showTranscript, setShowTranscript] = useState(false);
  const [inlineError, setInlineError] = useState<string | null>(null);

  const loadSession = async () => {
    if (!id) return;
    const s = await getSession(id);
    setSession(s);
    const facts = (s.memory_state as any)?._extracted_facts || [];
    setExtractedFacts(facts);
    if (s.soap_note) {
      const soap = s.soap_note as any;
      setEditedSoap({ S: soap.S || '', O: soap.O || '', A: soap.A || '', P: soap.P || '' });
    }
  };

  useEffect(() => {
    loadSession().catch(() => setError('Session not found'));
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

  const handleFactAction = async (factId: string, action: 'accept' | 'reject') => {
    if (!id) return;
    setConfirmingFactId(factId);
    try {
      await api.put(`/sessions/${id}/facts/${factId}`, { action });
      await loadSession();
    } catch (e) {
      console.error(e);
    } finally {
      setConfirmingFactId(null);
    }
  };

  const handleFactEdit = async (factId: string, newValue: string) => {
    if (!id || !newValue.trim()) { setEditingFactId(null); return; }
    setConfirmingFactId(factId);
    try {
      await api.put(`/sessions/${id}/facts/${factId}`, { action: 'edit', normalized_value: newValue.trim() });
      await loadSession();
    } catch (e) {
      console.error(e);
    } finally {
      setConfirmingFactId(null);
      setEditingFactId(null);
    }
  };

  const handleAddFact = async () => {
    if (!id || !addFactValue.trim()) return;
    setAddingFact(true);
    try {
      await api.post(`/sessions/${id}/facts`, { category: addFactCategory, normalized_value: addFactValue.trim() });
      await loadSession();
      setAddFactValue('');
      setShowAddFact(false);
    } catch (e) {
      console.error(e);
    } finally {
      setAddingFact(false);
    }
  };

  const handleViewInvestigationOrder = async () => {
    if (!id) return;
    try {
      const resp = await api.get(`/sessions/${id}/investigation-order`, {
        responseType: 'text',
        headers: { Accept: 'text/html' },
      });
      const blob = new Blob([resp.data as string], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      const win = window.open(url, '_blank');
      if (win) setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (e: any) {
      if (e.response?.status === 409) {
        setInlineError('No investigations ordered in this session.');
        setTimeout(() => setInlineError(null), 4000);
      } else if (e.response?.status === 404) {
        setInlineError('No investigations found for this session.');
        setTimeout(() => setInlineError(null), 4000);
      } else {
        setInlineError('Failed to generate investigation order.');
        setTimeout(() => setInlineError(null), 4000);
      }
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
        <div className={`${mode === 'health' ? 'max-w-7xl' : 'max-w-3xl'} mx-auto px-6 h-14 flex items-center justify-between`}>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="font-bold text-primary text-base">श</span>
              <span className="text-sm font-bold text-text-dark font-sans">Lipi</span>
            </div>
            {mode === 'health' ? (
              <nav className="flex items-center ml-2">
                <button
                  onClick={() => navigate('/')}
                  className="px-4 h-14 text-xs font-semibold text-slate-400 hover:text-slate-700 transition-colors cursor-pointer border-b-2 border-transparent"
                >
                  DASHBOARD
                </button>
                <button className="px-4 h-14 text-xs font-semibold text-emerald-700 border-b-2 border-emerald-600 cursor-pointer">
                  FACT REVIEW
                </button>
                <button
                  onClick={() => navigate('/')}
                  className="px-4 h-14 text-xs font-semibold text-slate-400 hover:text-slate-700 transition-colors cursor-pointer border-b-2 border-transparent"
                >
                  PATIENT LIST
                </button>
              </nav>
            ) : (
              <>
                <div className="h-4 w-px bg-slate-200" />
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
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide border ${MODE_COLORS[mode]}`}>
                  {MODE_LABELS[mode]}
                </span>
              </>
            )}
          </div>
          <div className="flex items-center gap-3">
            {session?.transcript && !session.transcript.startsWith('[Chief complaint:') && mode === 'health' && (
              <button
                onClick={() => setShowTranscript(v => !v)}
                className={`border text-xs font-semibold px-3 py-1.5 rounded transition-all flex items-center gap-1.5 cursor-pointer print:hidden ${
                  showTranscript
                    ? 'bg-primary/10 border-primary/30 text-primary'
                    : 'border-slate-300 hover:bg-slate-50 text-slate-600'
                }`}
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                {showTranscript ? 'Hide source' : 'View source'}
              </button>
            )}
            {doc && mode === 'health' && (
              <button
                onClick={handleViewInvestigationOrder}
                className="border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold px-3 py-1.5 rounded transition-all flex items-center gap-1.5 cursor-pointer"
              >
                Investigation Order
              </button>
            )}
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
            {session?.status === 'complete' && (
              <button
                onClick={async () => {
                  try {
                    const resp = await api.get(`/sessions/${id}/legal-export`, { responseType: 'blob' });
                    const url = URL.createObjectURL(new Blob([resp.data], { type: 'application/pdf' }));
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `lipi-legal-${(id || '').slice(0, 8)}.pdf`;
                    a.click();
                    URL.revokeObjectURL(url);
                  } catch {
                    alert('Legal export failed — session may not be complete yet.');
                  }
                }}
                className="border border-slate-300 hover:bg-amber-50 hover:border-amber-300 text-slate-700 hover:text-amber-700 text-xs font-semibold px-3 py-1.5 rounded transition-all flex items-center gap-1.5 cursor-pointer print:hidden"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
                </svg>
                Legal PDF
              </button>
            )}
            {session?.status === 'complete' && (
              <button
                onClick={async () => {
                  try {
                    const resp = await api.get(`/sessions/${id}/prescription`, { responseType: 'blob' });
                    const url = URL.createObjectURL(new Blob([resp.data], { type: 'application/pdf' }));
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `prescription-${(id || '').slice(0, 8)}.pdf`;
                    a.click();
                    URL.revokeObjectURL(url);
                  } catch {
                    alert('Could not generate prescription.');
                  }
                }}
                className="border border-emerald-300 hover:bg-emerald-50 text-emerald-700 text-xs font-semibold px-3 py-1.5 rounded transition-all flex items-center gap-1.5 cursor-pointer print:hidden"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Prescription
              </button>
            )}
            {session?.status === 'complete' && (
              <ReferralModal sessionId={id || ''} />
            )}
            {session?.status === 'complete' && (
              <TpaClaimModal sessionId={id || ''} />
            )}
            {session?.status === 'complete' && (
              <a
                href={`/internal/tpa/${id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="border border-emerald-300 hover:bg-emerald-50 text-emerald-700 text-xs font-semibold px-3 py-1.5 rounded transition-all flex items-center gap-1.5 print:hidden"
              >
                Insurance Claim →
              </a>
            )}
            <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">
              {session.status.replace(/_/g, ' ')}
            </span>
          </div>
        </div>
      </header>

      {inlineError && (
        <div className="fixed top-4 right-4 z-50 bg-red-50 border border-red-200 text-red-700 text-xs font-semibold px-4 py-2 rounded shadow-md">
          {inlineError}
        </div>
      )}

      <main className={`${mode === 'health' ? 'max-w-7xl' : 'max-w-3xl'} mx-auto px-6 py-6`}>

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

        {/* ── Transcript Evidence Panel ─────────────────────── */}
        {showTranscript && session?.transcript && !session.transcript.startsWith('[Chief complaint:') && (
          <div className="mb-6 bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden print:hidden">
            <div className="flex items-center gap-2 px-5 py-3 border-b border-slate-100 bg-slate-50/60">
              <svg className="w-3.5 h-3.5 text-primary shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
              <span className="text-[11px] font-bold text-primary uppercase tracking-widest">Source transcript — every fact traces to a line below</span>
            </div>
            <div className="px-5 py-4 space-y-1.5 max-h-64 overflow-y-auto">
              {(() => {
                const rawText = session.transcript || '';
                const sentences = rawText
                  .split(/(?<=[.!?])\s+|(?=\[)|\n+/)
                  .map(s => s.trim())
                  .filter(s => s.length > 3);

                // Keywords from all confirmed facts (for highlighting)
                const factKeywords = (extractedFacts || [])
                  .flatMap((f: any) => (f.normalized_value || '').toLowerCase().split(/\s+/))
                  .filter((w: string) => w.length > 3);

                const soapText = [
                  (session.soap_note as any)?.S,
                  (session.soap_note as any)?.O,
                  (session.soap_note as any)?.A,
                  (session.soap_note as any)?.P,
                ].filter(Boolean).join(' ').toLowerCase();

                return sentences.map((sentence, i) => {
                  const lower = sentence.toLowerCase();
                  // Highlight if this sentence contains a keyword from facts or SOAP
                  const isEvidence = factKeywords.some((kw: string) => lower.includes(kw)) ||
                    lower.split(/\s+/).some((w: string) => w.length > 4 && soapText.includes(w));
                  return (
                    <div key={i} className={`flex items-start gap-2.5 rounded-lg px-3 py-2 transition-colors ${
                      isEvidence ? 'bg-primary/5 border border-primary/15' : 'hover:bg-slate-50'
                    }`}>
                      <span className="text-[10px] font-mono text-slate-300 tabular-nums shrink-0 mt-0.5">{String(i + 1).padStart(2, '0')}</span>
                      <p className={`text-[12.5px] leading-relaxed ${isEvidence ? 'text-slate-800 font-medium' : 'text-slate-500'}`}>
                        {sentence}
                      </p>
                      {isEvidence && (
                        <span className="shrink-0 mt-0.5 text-[9px] font-bold text-primary uppercase tracking-wider bg-primary/10 px-1.5 py-0.5 rounded-full">
                          cited
                        </span>
                      )}
                    </div>
                  );
                });
              })()}
            </div>
          </div>
        )}

        {mode === 'health' ? (
          /* ── Two-column health review layout ── */
          <div className="flex gap-6 items-start print:block">

            {/* LEFT — title + progress + facts grid */}
            <div className="flex-1 min-w-0">

              {/* Title row */}
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h1 className="text-xl font-bold text-slate-800">Clinical Fact Review</h1>
                  <p className="text-xs text-slate-400 mt-0.5">Review and verify information extracted from the consultation.</p>
                </div>
                {extractedFacts.length > 0 && (
                  <span className="shrink-0 ml-4 mt-1 border border-amber-300 text-amber-700 bg-amber-50 px-3 py-1 rounded text-[11px] font-bold uppercase tracking-wider">
                    {extractedFacts.filter((f: any) => f.review_status === 'candidate').length} FACTS · NEEDS REVIEW
                  </span>
                )}
              </div>

              {/* Progress bar */}
              {extractedFacts.length > 0 && (() => {
                const total = extractedFacts.length;
                const removed = extractedFacts.filter((f: any) => f.review_status === 'rejected').length;
                const remaining = extractedFacts.filter((f: any) => f.review_status === 'candidate').length;
                const pct = total > 0 ? Math.round((removed / total) * 100) : 0;
                return (
                  <div className="mb-5 print:hidden">
                    <div className="flex justify-between text-[11px] text-slate-400 mb-1.5">
                      <span>{removed} removed · {remaining} remaining</span>
                      <span>{pct}%</span>
                    </div>
                    <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-1.5 bg-emerald-500 rounded-full transition-all duration-300" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })()}

              {/* Facts grid */}
              {extractedFacts.length > 0 && (() => {
                const pending = extractedFacts.filter((f: any) => f.review_status === 'candidate');
                const CATEGORY_META: Record<string, { label: string; border: string; badge: string; labelColor: string }> = {
                  symptom:       { label: 'Symptom',       border: 'border-l-blue-400',   badge: 'bg-blue-50 text-blue-600 border-blue-200',     labelColor: 'text-blue-600' },
                  vital:         { label: 'Vital',         border: 'border-l-purple-400', badge: 'bg-purple-50 text-purple-600 border-purple-200', labelColor: 'text-purple-600' },
                  medication:    { label: 'Medication',    border: 'border-l-green-400',  badge: 'bg-green-50 text-green-700 border-green-200',   labelColor: 'text-green-700' },
                  investigation: { label: 'Investigation', border: 'border-l-amber-400',  badge: 'bg-amber-50 text-amber-700 border-amber-200',   labelColor: 'text-amber-700' },
                  diagnosis:     { label: 'Diagnosis',     border: 'border-l-red-400',    badge: 'bg-red-50 text-red-600 border-red-200',         labelColor: 'text-red-600' },
                  allergy:       { label: 'Allergy',       border: 'border-l-rose-400',   badge: 'bg-rose-50 text-rose-600 border-rose-200',      labelColor: 'text-rose-600' },
                  follow_up:     { label: 'Follow-up',     border: 'border-l-teal-400',   badge: 'bg-teal-50 text-teal-700 border-teal-200',      labelColor: 'text-teal-700' },
                };
                const DEFAULT_META = { label: 'Fact', border: 'border-l-slate-300', badge: 'bg-slate-50 text-slate-500 border-slate-200', labelColor: 'text-slate-500' };
                if (pending.length === 0) return (
                  <div className="text-center py-12 border border-dashed border-emerald-200 rounded-lg bg-emerald-50/30">
                    <p className="text-sm font-semibold text-emerald-700">All facts reviewed</p>
                    <p className="text-xs text-slate-400 mt-1">Click "Sign & Finalize" in the sidebar to complete.</p>
                  </div>
                );
                return (
                  <>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 print:hidden">
                      {pending.map((fact: any) => {
                        const meta = CATEGORY_META[fact.category] || DEFAULT_META;
                        const isEditingThis = editingFactId === fact.id;
                        return (
                          <div
                            key={fact.id}
                            className={`relative flex flex-col gap-1.5 pl-3 pr-8 py-3 rounded-md border border-slate-200 border-l-4 ${meta.border} bg-white`}
                          >
                            <span className={`text-[10px] font-bold uppercase tracking-widest ${meta.labelColor}`}>{meta.label}</span>
                            {isEditingThis ? (
                              <input
                                autoFocus
                                value={editingValue}
                                onChange={e => setEditingValue(e.target.value)}
                                onBlur={() => handleFactEdit(fact.id, editingValue)}
                                onKeyDown={e => {
                                  if (e.key === 'Enter') handleFactEdit(fact.id, editingValue);
                                  if (e.key === 'Escape') setEditingFactId(null);
                                }}
                                className="text-sm font-semibold text-slate-800 border-b border-slate-300 focus:border-emerald-500 outline-none bg-transparent w-full pb-0.5"
                              />
                            ) : (
                              <span
                                className="text-sm font-semibold text-slate-800 leading-snug cursor-text hover:text-emerald-700 group"
                                title="Click to edit"
                                onClick={() => { setEditingFactId(fact.id); setEditingValue(fact.normalized_value); }}
                              >
                                {fact.normalized_value}
                                <span className="opacity-0 group-hover:opacity-100 ml-1 text-[10px] text-slate-400 font-normal">✎</span>
                              </span>
                            )}
                            {fact.source_sentence && !isEditingThis && (
                              <p className="text-[11px] text-slate-400 italic leading-snug line-clamp-2" title={fact.source_sentence}>
                                * {fact.source_sentence}
                              </p>
                            )}
                            <button
                              onClick={() => handleFactAction(fact.id, 'reject')}
                              disabled={confirmingFactId === fact.id}
                              className="absolute top-2.5 right-2.5 w-5 h-5 rounded-full flex items-center justify-center bg-slate-100 hover:bg-red-50 hover:text-red-500 text-slate-400 transition-colors disabled:opacity-40 cursor-pointer text-[11px] font-bold"
                              title="Remove this fact from SOAP"
                            >✕</button>
                          </div>
                        );
                      })}

                      {/* Add Fact card */}
                      {showAddFact ? (
                        <div className="flex flex-col gap-2 pl-3 pr-3 py-3 rounded-md border border-emerald-300 border-l-4 border-l-emerald-400 bg-emerald-50/30">
                          <select
                            value={addFactCategory}
                            onChange={e => setAddFactCategory(e.target.value)}
                            className="text-[10px] font-bold uppercase tracking-widest bg-transparent border-none outline-none text-emerald-700 cursor-pointer"
                          >
                            {Object.entries(CATEGORY_META).map(([k, v]) => (
                              <option key={k} value={k}>{v.label}</option>
                            ))}
                          </select>
                          <input
                            autoFocus
                            value={addFactValue}
                            onChange={e => setAddFactValue(e.target.value)}
                            onKeyDown={e => { if (e.key === 'Enter') handleAddFact(); if (e.key === 'Escape') setShowAddFact(false); }}
                            placeholder="Enter value…"
                            className="text-sm font-semibold text-slate-800 border-b border-emerald-300 focus:border-emerald-500 outline-none bg-transparent w-full pb-0.5 placeholder:font-normal placeholder:text-slate-400"
                          />
                          <div className="flex gap-2 mt-1">
                            <button
                              onClick={handleAddFact}
                              disabled={addingFact || !addFactValue.trim()}
                              className="text-[11px] font-bold text-white bg-emerald-600 hover:bg-emerald-700 px-2.5 py-1 rounded disabled:opacity-50 cursor-pointer"
                            >
                              {addingFact ? '…' : 'Add'}
                            </button>
                            <button
                              onClick={() => { setShowAddFact(false); setAddFactValue(''); }}
                              className="text-[11px] font-bold text-slate-500 hover:text-slate-700 cursor-pointer"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <button
                          onClick={() => setShowAddFact(true)}
                          className="flex items-center justify-center gap-1.5 pl-3 pr-3 py-3 rounded-md border border-dashed border-slate-300 hover:border-emerald-400 hover:bg-emerald-50/30 text-slate-400 hover:text-emerald-600 text-xs font-semibold transition-colors cursor-pointer"
                        >
                          <span className="text-base leading-none">+</span> Add Fact
                        </button>
                      )}
                    </div>
                  </>
                );
              })()}

              {/* No doc yet */}
              {!doc && (
                <div className="text-center py-20 border border-dashed border-slate-200 rounded-lg bg-white mt-4 print:hidden">
                  <svg className="w-10 h-10 mx-auto mb-4 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="text-sm font-semibold text-slate-500">No document generated yet</p>
                  <p className="text-xs text-slate-400 mt-1">Go back to the consultation and run "Begin Documentation".</p>
                  <button onClick={() => navigate(`/consultation/${id}`)} className="mt-4 bg-primary hover:bg-primary-dark text-white text-xs font-semibold px-4 py-2 rounded transition-all shadow-sm cursor-pointer">
                    Go to Consultation →
                  </button>
                </div>
              )}

              {/* Consent audit (compact, below facts) */}
              {session.cloud_ai_consent && (
                <div className="mt-4 border border-slate-100 rounded-lg p-3 bg-slate-50/50 text-[11px] text-slate-500 print:hidden flex items-center gap-3 flex-wrap">
                  <svg className="w-3.5 h-3.5 text-emerald-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  <span className="font-semibold text-emerald-700">Consent ✓</span>
                  <span className="text-slate-400">·</span>
                  <span>Mode: {session.consent_log?.consent_mode || 'verbal'}</span>
                  <span className="text-slate-400">·</span>
                  <span>{session.consent_log?.timestamp ? new Date(session.consent_log.timestamp).toLocaleString('en-IN', { hour12: true }) : new Date(session.created_at).toLocaleString('en-IN', { hour12: true })}</span>
                  {session.consent_log?.consent_hash && (
                    <span className="font-mono text-[10px] text-slate-400 truncate">#{session.consent_log.consent_hash.slice(0, 8)}</span>
                  )}
                </div>
              )}
            </div>

            {/* RIGHT SIDEBAR — patient + SOAP + sign */}
            <div className="w-72 shrink-0 sticky top-16 print:hidden">
              {/* Patient header */}
              <div className="bg-white border border-slate-200 border-b-0 rounded-t-lg px-4 py-3 flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-emerald-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
                  {(session.patient_name || 'P').split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-800">{session.patient_name || 'Anonymous Patient'}</p>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-amber-600">DRAFT · NEEDS REVIEW</p>
                </div>
              </div>

              {/* SOAP sections */}
              {doc && (() => {
                const soap = doc as any;
                const simpleSOAP = 'S' in soap || 'O' in soap;
                if (!simpleSOAP) return null;
                const sections = [
                  { key: 'S', label: 'Subjective', accent: 'border-l-blue-400',   color: 'text-blue-600' },
                  { key: 'O', label: 'Objective',  accent: 'border-l-purple-400', color: 'text-purple-600' },
                  { key: 'A', label: 'Assessment', accent: 'border-l-red-400',    color: 'text-red-600' },
                  { key: 'P', label: 'Plan',       accent: 'border-l-green-400',  color: 'text-green-700' },
                ];
                return (
                  <div className="bg-white border border-slate-200 border-t-0 border-b-0 divide-y divide-slate-100">
                    {sections.map(s => (
                      <div key={s.key} className={`px-4 py-3 border-l-2 ${s.accent}`}>
                        <p className={`text-[10px] font-bold uppercase tracking-widest mb-1.5 ${s.color}`}>{s.label}</p>
                        {isEditing ? (
                          <textarea
                            value={(editedSoap as any)[s.key] || ''}
                            onChange={e => setEditedSoap({ ...editedSoap, [s.key]: e.target.value })}
                            rows={3}
                            className="w-full text-[12px] text-slate-700 leading-relaxed resize-none border border-slate-200 rounded px-2 py-1.5 focus:outline-none focus:border-emerald-400 bg-slate-50"
                          />
                        ) : (
                          <p className="text-[12px] text-slate-600 leading-relaxed">{(doc as any)[s.key] || 'Not specified'}</p>
                        )}
                      </div>
                    ))}
                    {/* CDS alerts compact */}
                    {cds && cds.length > 0 && !isEditing && (
                      <div className="px-4 py-3">
                        {cds.slice(0, 2).map((alert: any, i: number) => (
                          <div key={i} className={`text-[11px] font-semibold mb-1 ${alert.urgency === 'critical' ? 'text-red-600' : 'text-amber-600'}`}>
                            ⚠ {alert.suggestion}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })()}

              {/* Sign & Finalize — or Save Edits when editing */}
              {isEditing ? (
                <div className="flex gap-0 border border-slate-200 border-t-0 rounded-b-lg overflow-hidden">
                  <button
                    onClick={submitFeedback}
                    className="flex-1 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold py-3.5 tracking-wider uppercase transition-colors cursor-pointer"
                  >
                    Save Edits
                  </button>
                  <button
                    onClick={() => { setIsEditing(false); }}
                    className="px-4 bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs font-semibold transition-colors cursor-pointer border-l border-slate-200"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  onClick={handleAccept}
                  disabled={feedbackSubmitted}
                  className="w-full bg-emerald-700 hover:bg-emerald-800 disabled:bg-emerald-400 text-white text-xs font-bold py-3.5 rounded-b-lg tracking-wider uppercase transition-colors cursor-pointer"
                >
                  {feedbackSubmitted ? '✓ Signed' : 'Sign & Finalize'}
                </button>
              )}

              {feedbackSubmitted && (
                <p className="text-[11px] text-emerald-700 text-center mt-2">{feedbackMessage}</p>
              )}

              {/* Edit / Reject links */}
              {doc && !feedbackSubmitted && !isEditing && (
                <div className="mt-3 flex justify-center gap-4 text-[11px]">
                  <button onClick={handleEditToggle} className="text-slate-500 hover:text-slate-700 cursor-pointer">
                    Edit Note
                  </button>
                  <span className="text-slate-300">·</span>
                  <button onClick={() => { setRejectMode(true); setIsEditing(false); }} className="text-slate-500 hover:text-red-600 cursor-pointer">
                    Reject
                  </button>
                  <span className="text-slate-300">·</span>
                  <button onClick={() => window.print()} className="text-slate-500 hover:text-slate-700 cursor-pointer">
                    Print
                  </button>
                </div>
              )}
            </div>

          </div>
        ) : (
          /* ── Non-health modes (FIR / Legal / General) — single column ── */
          <>
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
          </>
        )}

        {/* PRINT-ONLY CLINICAL NOTE */}
        {doc && mode === 'health' && (
          <div className="hidden print:block mt-6 space-y-6">
            {/* Patient info row */}
            <div className="flex justify-between items-start border-b border-slate-200 pb-3">
              <div>
                <p className="text-sm font-bold text-slate-900">{session.patient_name || 'Anonymous Patient'}</p>
                {session.abha_number && <p className="text-[10px] text-slate-500 mt-0.5">ABHA: {session.abha_number}</p>}
              </div>
              <div className="text-right text-[10px] text-slate-500">
                <p>{session.doctor_name ? ('Dr. ' + session.doctor_name) : ''}</p>
                <p>{new Date(session.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}</p>
              </div>
            </div>

            {/* SOAP Note */}
            {(() => {
              const soap = (doc as any);
              const sections = [
                { key: 'S', label: 'Subjective (Symptoms, History)', value: soap.S || soap.subjective },
                { key: 'O', label: 'Objective (Vitals, Observations)', value: soap.O || soap.objective },
                { key: 'A', label: 'Assessment (Clinical Impression)', value: soap.A || soap.assessment },
                { key: 'P', label: 'Plan (Medications, Orders, Follow-Up)', value: soap.P || soap.plan },
              ].filter(s => s.value);
              return (
                <div className="space-y-3">
                  <h2 className="text-xs font-bold uppercase tracking-widest text-slate-600 border-b border-slate-100 pb-1">SOAP Clinical Note</h2>
                  {sections.map(({ key, label, value }) => (
                    <div key={key}>
                      <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-0.5">{key}. {label}</p>
                      <p className="text-sm text-slate-800 leading-relaxed whitespace-pre-wrap">{value}</p>
                    </div>
                  ))}
                </div>
              );
            })()}

            {/* Extracted Facts table */}
            {extractedFacts.length > 0 && (
              <div>
                <h2 className="text-xs font-bold uppercase tracking-widest text-slate-600 border-b border-slate-100 pb-1 mb-2">Extracted Clinical Facts</h2>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px' }}>
                  <thead>
                    <tr style={{ background: '#f8fafc' }}>
                      <th style={{ textAlign: 'left', padding: '4px 8px', borderBottom: '1px solid #e2e8f0', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', fontSize: '9px' }}>Category</th>
                      <th style={{ textAlign: 'left', padding: '4px 8px', borderBottom: '1px solid #e2e8f0', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', fontSize: '9px' }}>Value</th>
                      <th style={{ textAlign: 'left', padding: '4px 8px', borderBottom: '1px solid #e2e8f0', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', fontSize: '9px' }}>Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {extractedFacts.filter((f: any) => f.review_status !== 'rejected').map((f: any, i: number) => (
                      <tr key={f.id} style={{ background: i % 2 === 0 ? '#fff' : '#f8fafc' }}>
                        <td style={{ padding: '4px 8px', borderBottom: '1px solid #f1f5f9', color: '#475569', textTransform: 'capitalize' }}>{f.category?.replace('_', ' ')}</td>
                        <td style={{ padding: '4px 8px', borderBottom: '1px solid #f1f5f9', color: '#1e293b', fontWeight: 600 }}>{f.normalized_value}</td>
                        <td style={{ padding: '4px 8px', borderBottom: '1px solid #f1f5f9', color: '#94a3b8', fontStyle: 'italic', fontSize: '10px' }}>{f.source_sentence?.slice(0, 60)}{f.source_sentence?.length > 60 ? '...' : ''}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Consent */}
            {session.cloud_ai_consent && (
              <p className="text-[10px] text-slate-500 border-t border-slate-100 pt-2">
                <span className="font-semibold text-emerald-700">Consent ✓</span>
                {' · '}Mode: {session.consent_log?.consent_mode || 'verbal'}
                {' · '}{session.consent_log?.timestamp ? new Date(session.consent_log.timestamp).toLocaleString('en-IN', { hour12: true }) : new Date(session.created_at).toLocaleString('en-IN', { hour12: true })}
              </p>
            )}
          </div>
        )}

        {/* Printable disclaimer footer */}
        <div className="hidden print:block mt-8 pt-4 border-t border-slate-200 text-[10px] text-slate-500 text-center">
          <p className="font-semibold text-slate-700">"Doctor must review and sign off before clinical use"</p>
          <p className="mt-1">Generated by Lipi on {new Date(session.created_at).toLocaleString('en-IN')}</p>
          <p className="mt-1 text-[8px]">This is an AI-assisted draft documentation. The physician retains final authority and accountability.</p>
        </div>

        {/* Expanded feedback form — only shown when doctor clicks Edit or Reject from sidebar */}
        {doc && mode === 'health' && (isEditing || rejectMode) && !feedbackSubmitted && (
          <section className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm mt-4 print:hidden">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
              {isEditing ? 'Edit Note' : 'Reject Note'} — Correction Categories
            </h2>
            <div className="flex flex-wrap gap-2 mb-4">
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
            <div className="flex justify-end gap-2">
              <button
                onClick={() => { setRejectMode(false); setIsEditing(false); setSelectedCategories([]); }}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-lg transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={submitFeedback}
                className="px-5 py-2 bg-primary hover:bg-primary-dark text-white text-xs font-bold rounded-lg shadow-sm transition-colors cursor-pointer"
              >
                {rejectMode ? 'Submit Rejection' : 'Submit Edits & Feedback'}
              </button>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
