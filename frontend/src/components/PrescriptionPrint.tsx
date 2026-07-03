import { useRef, useState } from 'react';
import { useReactToPrint } from 'react-to-print';
import type { ProcessClinicalResponse } from '../types/clinical';

interface Props {
  results: ProcessClinicalResponse;
  patientName?: string;
  doctorName?: string;
}

interface DoctorProfile {
  nmc: string;
  qualification: string;
  smc: string;
  clinicName: string;
}

const PROFILE_KEY = 'lipi_doctor_profile';

function loadProfile(): DoctorProfile {
  try {
    return { nmc: '', qualification: 'MBBS', smc: '', clinicName: '', ...JSON.parse(localStorage.getItem(PROFILE_KEY) || '{}') };
  } catch {
    return { nmc: '', qualification: 'MBBS', smc: '', clinicName: '' };
  }
}

function saveProfile(p: DoctorProfile) {
  localStorage.setItem(PROFILE_KEY, JSON.stringify(p));
}

// English frequency → Indian abbreviation
const FREQ_TABLE: Array<[string, string]> = [
  ['once daily', 'OD'], ['once a day', 'OD'],
  ['twice daily', 'BD'], ['twice a day', 'BD'], ['two times', 'BD'],
  ['three times', 'TDS'], ['thrice', 'TDS'], ['tds', 'TDS'],
  ['four times', 'QID'], ['qid', 'QID'],
  ['as needed', 'SOS'], ['when required', 'SOS'], ['sos', 'SOS'],
  ['before meals', 'AC'], ['after meals', 'PC'],
  ['at bedtime', 'HS'], ['night', 'HS'],
  ['morning', 'AM'],
];

function toIndianFreq(freq: string): string {
  const lower = (freq || '').toLowerCase();
  for (const [pattern, abbr] of FREQ_TABLE) {
    if (lower.includes(pattern)) return abbr;
  }
  return freq || '—';
}

export default function PrescriptionPrint({ results, patientName, doctorName }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const [profile, setProfile] = useState<DoctorProfile>(loadProfile);
  const [editingProfile, setEditingProfile] = useState(false);
  const [draft, setDraft] = useState<DoctorProfile>(loadProfile);

  const handlePrint = useReactToPrint({
    contentRef: ref,
    documentTitle: `Rx_${patientName ?? 'Patient'}_${new Date().toLocaleDateString('en-IN')}`,
  });

  function openProfileEdit() {
    setDraft(loadProfile());
    setEditingProfile(true);
  }

  function saveAndPrint() {
    saveProfile(draft);
    setProfile(draft);
    setEditingProfile(false);
    setTimeout(() => handlePrint(), 100);
  }

  const { facts } = results;
  const meds = facts?.medications ?? [];
  const investigations = facts?.investigations ?? [];
  const followUp = (facts as any)?.follow_up ?? [];
  const allergies = facts?.allergies ?? [];
  const today = new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' });
  const nmcLine = profile.nmc ? `Reg. No. ${profile.nmc}` : null;
  const qualLine = profile.qualification || 'MBBS';

  return (
    <>
      <button
        onClick={() => profile.nmc ? handlePrint() : openProfileEdit()}
        className="flex items-center gap-1.5 text-xs font-medium text-green-700 hover:text-green-900 border border-green-200 hover:border-green-400 bg-green-50 hover:bg-green-100 rounded px-3 py-1.5 transition-all"
        title="Print Indian Prescription (Rx)"
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
        </svg>
        Print Rx
      </button>

      {/* Doctor profile setup modal — appears on first print */}
      {editingProfile && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm border border-slate-200">
            <div className="p-5 border-b border-slate-100">
              <h2 className="font-bold text-slate-800 text-base">Doctor Profile</h2>
              <p className="text-xs text-slate-400 mt-0.5">Saved once — appears on every prescription you print</p>
            </div>
            <div className="p-5 space-y-3">
              {[
                { label: 'NMC / MCI Registration No.', key: 'nmc', placeholder: 'e.g. 12345' },
                { label: 'Qualification', key: 'qualification', placeholder: 'e.g. MBBS, MD Medicine' },
                { label: 'State Medical Council', key: 'smc', placeholder: 'e.g. Maharashtra Medical Council' },
                { label: 'Clinic / Hospital Name', key: 'clinicName', placeholder: 'e.g. City Health Clinic' },
              ].map(({ label, key, placeholder }) => (
                <div key={key}>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">{label}</label>
                  <input
                    type="text"
                    value={draft[key as keyof DoctorProfile]}
                    onChange={e => setDraft({ ...draft, [key]: e.target.value })}
                    placeholder={placeholder}
                    className="w-full border border-slate-200 rounded px-3 py-2 text-sm text-slate-800 outline-none focus:border-primary transition-colors"
                  />
                </div>
              ))}
            </div>
            <div className="p-4 border-t border-slate-100 flex gap-2 justify-end">
              <button
                onClick={() => setEditingProfile(false)}
                className="px-4 py-2 text-sm text-slate-500 hover:text-slate-700 font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={saveAndPrint}
                className="px-5 py-2 bg-primary hover:bg-primary-dark text-white text-sm font-semibold rounded-lg transition-all shadow-sm"
              >
                Save & Print →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Hidden printable area */}
      <div className="hidden">
        <div ref={ref} style={{ fontFamily: 'Arial, sans-serif', padding: '28px 36px', maxWidth: '720px', margin: '0 auto', fontSize: '13px', color: '#111' }}>

          {/* Header */}
          <div style={{ borderBottom: '3px solid #059669', paddingBottom: '14px', marginBottom: '18px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              {profile.clinicName && (
                <p style={{ fontSize: '13px', fontWeight: 'bold', color: '#064e3b', margin: '0 0 3px' }}>{profile.clinicName}</p>
              )}
              <h1 style={{ fontSize: '18px', fontWeight: 'bold', color: '#064e3b', margin: 0 }}>
                {doctorName ? `Dr. ${doctorName}` : 'Physician'}
              </h1>
              <p style={{ fontSize: '11px', color: '#6b7280', margin: '3px 0 0' }}>
                {qualLine}{nmcLine ? ` · ${nmcLine}` : ''}
              </p>
              {profile.smc && (
                <p style={{ fontSize: '10px', color: '#9ca3af', margin: '2px 0 0' }}>{profile.smc}</p>
              )}
            </div>
            <div style={{ textAlign: 'right' }}>
              <p style={{ fontSize: '12px', color: '#374151', margin: 0 }}>Date: <strong>{today}</strong></p>
              <p style={{ fontSize: '12px', color: '#374151', margin: '4px 0 0' }}>
                Patient: <strong>{patientName ?? 'Anonymous'}</strong>
              </p>
            </div>
          </div>

          {/* Rx symbol */}
          <div style={{ fontSize: '30px', fontWeight: 'bold', color: '#059669', marginBottom: '10px', lineHeight: 1 }}>℞</div>

          {/* Allergy warning */}
          {allergies.length > 0 && (
            <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', padding: '8px 12px', marginBottom: '14px' }}>
              <p style={{ margin: 0, color: '#dc2626', fontWeight: 'bold', fontSize: '11px' }}>
                ⚠ ALLERGY: {allergies.map(a => a.toUpperCase()).join(', ')}
              </p>
            </div>
          )}

          {/* Medications — Indian format with OD/BD/TDS */}
          {meds.length > 0 ? (
            <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px' }}>
              <thead>
                <tr style={{ background: '#f0fdf4', borderBottom: '2px solid #059669' }}>
                  {['Medicine (Generic Name)', 'Dose', 'Freq.', 'Route', 'Instructions'].map(h => (
                    <th key={h} style={{ padding: '8px 10px', textAlign: 'left', fontSize: '10px', color: '#065f46', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {meds.map((m, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #e5e7eb', background: i % 2 === 0 ? '#fff' : '#f9fafb' }}>
                    <td style={{ padding: '10px', fontWeight: 'bold', color: '#111827', textTransform: 'capitalize' }}>
                      {m.name}
                      <span style={{ display: 'block', fontSize: '10px', color: '#6b7280', fontWeight: 'normal', fontStyle: 'italic' }}>Tab.</span>
                    </td>
                    <td style={{ padding: '10px', color: '#374151' }}>{m.dosage || '—'}</td>
                    <td style={{ padding: '10px', color: '#111', fontWeight: 'bold' }}>{toIndianFreq(m.frequency || '')}</td>
                    <td style={{ padding: '10px', color: '#374151' }}>Oral</td>
                    <td style={{ padding: '10px', color: '#374151', fontSize: '11px' }}>After meals</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p style={{ color: '#6b7280', fontStyle: 'italic', marginBottom: '20px' }}>No medications recorded.</p>
          )}

          {/* Investigations */}
          {investigations.length > 0 && (
            <div style={{ marginBottom: '12px' }}>
              <p style={{ fontWeight: 'bold', color: '#1e3a5f', marginBottom: '4px', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Investigations</p>
              <p style={{ margin: 0, color: '#374151' }}>{investigations.join(', ')}</p>
            </div>
          )}

          {/* Follow up */}
          {followUp.length > 0 && (
            <div style={{ marginBottom: '12px' }}>
              <p style={{ fontWeight: 'bold', color: '#1e3a5f', marginBottom: '4px', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Follow Up</p>
              <p style={{ margin: 0, color: '#374151' }}>{Array.isArray(followUp) ? followUp.join(', ') : followUp}</p>
            </div>
          )}

          {/* Advice */}
          <div style={{ marginBottom: '12px', fontSize: '12px' }}>
            <p style={{ fontWeight: 'bold', color: '#1e3a5f', marginBottom: '4px', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Advice</p>
            <p style={{ margin: 0, color: '#374151' }}>Adequate rest · Plenty of fluids (8–10 glasses/day) · Avoid self-medication · Return if symptoms worsen</p>
          </div>

          {/* Signature + stamp row */}
          <div style={{ marginTop: '40px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
            <div style={{ border: '1px dashed #d1d5db', borderRadius: '4px', width: '130px', height: '80px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ fontSize: '10px', color: '#9ca3af' }}>Clinic Stamp</span>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ height: '48px' }} />
              <div style={{ borderTop: '1px solid #374151', paddingTop: '4px', minWidth: '180px' }}>
                <p style={{ margin: 0, fontSize: '12px', color: '#374151', fontWeight: 'bold' }}>
                  {doctorName ? `Dr. ${doctorName}` : "Doctor's Signature"}
                </p>
                {nmcLine && <p style={{ margin: '2px 0 0', fontSize: '10px', color: '#6b7280' }}>{nmcLine}</p>}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div style={{ marginTop: '18px', borderTop: '1px solid #e5e7eb', paddingTop: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <p style={{ margin: 0, fontSize: '9px', color: '#9ca3af' }}>
              For Medical Use Only · Valid for 30 days · Not valid without doctor's signature and stamp
            </p>
            <p style={{ margin: 0, fontSize: '9px', color: '#9ca3af' }}>Lipi Health</p>
          </div>

        </div>
      </div>
    </>
  );
}
