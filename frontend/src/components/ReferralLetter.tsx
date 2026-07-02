import { useRef, useState } from 'react';
import { useReactToPrint } from 'react-to-print';
import type { ProcessClinicalResponse } from '../types/clinical';

interface Props {
  results: ProcessClinicalResponse;
  patientName?: string;
  doctorName?: string;
  abhaNumber?: string;
}

interface ReferralDetails {
  toDoctor: string;
  toDepartment: string;
  toHospital: string;
  reason: string;
}

function loadDoctorProfile() {
  try {
    return JSON.parse(localStorage.getItem('lipi_doctor_profile') || '{}');
  } catch { return {}; }
}

export default function ReferralLetter({ results, patientName, doctorName, abhaNumber }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [details, setDetails] = useState<ReferralDetails>({
    toDoctor: '',
    toDepartment: '',
    toHospital: '',
    reason: '',
  });

  const handlePrint = useReactToPrint({
    contentRef: ref,
    documentTitle: `Referral_${patientName ?? 'Patient'}_${new Date().toLocaleDateString('en-IN')}`,
  });

  const profile = loadDoctorProfile();
  const { facts, soap } = results;
  const meds = facts?.medications ?? [];
  const vitals = facts?.vitals ?? [];
  const allergies = facts?.allergies ?? [];

  // Extract diagnosis from Assessment
  const diagnosisRaw = soap?.A?.split('.')?.[0]?.replace(/^(Assessment|Diagnosis|Impression)[:\s]*/i, '').trim() || 'Pending evaluation';
  const today = new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' });

  function handlePrintClick() {
    setOpen(false);
    setTimeout(() => handlePrint(), 100);
  }

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-1.5 text-xs font-medium text-indigo-700 hover:text-indigo-900 border border-indigo-200 hover:border-indigo-400 bg-indigo-50 hover:bg-indigo-100 rounded px-3 py-1.5 transition-all"
        title="Generate Referral Letter"
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
        Referral
      </button>

      {/* Referral details modal */}
      {open && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm border border-slate-200">
            <div className="p-5 border-b border-slate-100">
              <h2 className="font-bold text-slate-800 text-base">Referral Letter</h2>
              <p className="text-xs text-slate-400 mt-0.5">Fill recipient details — SOAP data fills automatically</p>
            </div>
            <div className="p-5 space-y-3">
              {[
                { label: 'Referring To (Doctor / MO)', key: 'toDoctor', placeholder: 'e.g. Medical Officer' },
                { label: 'Department / Specialty', key: 'toDepartment', placeholder: 'e.g. Cardiology, Orthopaedics' },
                { label: 'Hospital / Centre', key: 'toHospital', placeholder: 'e.g. District Hospital, Mumbai' },
                { label: 'Reason for Referral', key: 'reason', placeholder: 'e.g. Further evaluation and management' },
              ].map(({ label, key, placeholder }) => (
                <div key={key}>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">{label}</label>
                  <input
                    type="text"
                    value={details[key as keyof ReferralDetails]}
                    onChange={e => setDetails({ ...details, [key]: e.target.value })}
                    placeholder={placeholder}
                    className="w-full border border-slate-200 rounded px-3 py-2 text-sm text-slate-800 outline-none focus:border-primary transition-colors"
                  />
                </div>
              ))}
            </div>
            <div className="p-4 border-t border-slate-100 flex gap-2 justify-end">
              <button onClick={() => setOpen(false)} className="px-4 py-2 text-sm text-slate-500 hover:text-slate-700 font-medium transition-colors">
                Cancel
              </button>
              <button
                onClick={handlePrintClick}
                className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-lg transition-all shadow-sm"
              >
                Print Letter →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Hidden printable referral */}
      <div className="hidden">
        <div ref={ref} style={{ fontFamily: 'Arial, sans-serif', padding: '36px 44px', maxWidth: '720px', margin: '0 auto', fontSize: '13px', color: '#111', lineHeight: '1.6' }}>

          {/* Letterhead */}
          <div style={{ borderBottom: '3px solid #4f46e5', paddingBottom: '14px', marginBottom: '24px', display: 'flex', justifyContent: 'space-between' }}>
            <div>
              {profile.clinicName && <p style={{ fontWeight: 'bold', fontSize: '14px', color: '#312e81', margin: '0 0 2px' }}>{profile.clinicName}</p>}
              <p style={{ fontWeight: 'bold', fontSize: '16px', margin: 0, color: '#1e1b4b' }}>
                {doctorName ? `Dr. ${doctorName}` : 'Physician'}
              </p>
              <p style={{ fontSize: '11px', color: '#6b7280', margin: '2px 0 0' }}>
                {profile.qualification || 'MBBS'}
                {profile.nmc ? ` · Reg. No. ${profile.nmc}` : ''}
              </p>
              {profile.smc && <p style={{ fontSize: '10px', color: '#9ca3af', margin: '1px 0 0' }}>{profile.smc}</p>}
            </div>
            <div style={{ textAlign: 'right', fontSize: '12px', color: '#374151' }}>
              <p style={{ margin: 0 }}>Date: <strong>{today}</strong></p>
              <p style={{ margin: '3px 0 0', fontSize: '11px', color: '#9ca3af' }}>Referral Letter</p>
            </div>
          </div>

          {/* Recipient */}
          <div style={{ marginBottom: '20px' }}>
            <p style={{ margin: 0 }}>To,</p>
            <p style={{ margin: '2px 0 0', fontWeight: 'bold' }}>{details.toDoctor || 'The Medical Officer'}</p>
            {details.toDepartment && <p style={{ margin: 0 }}>{details.toDepartment}</p>}
            <p style={{ margin: 0 }}>{details.toHospital || 'District Hospital'}</p>
          </div>

          {/* Subject */}
          <p style={{ marginBottom: '18px', fontWeight: 'bold', textDecoration: 'underline' }}>
            Subject: Referral of Patient <span style={{ textDecoration: 'none' }}>{patientName ?? '[Patient Name]'}</span> for further management
          </p>

          {/* Body */}
          <p style={{ marginBottom: '14px' }}>Dear Doctor,</p>

          <p style={{ marginBottom: '14px' }}>
            I am referring <strong>{patientName ?? 'the above-named patient'}</strong>
            {abhaNumber ? ` (ABHA: ${abhaNumber})` : ''} to your department for further evaluation and management.
            The clinical summary is as follows:
          </p>

          {/* Clinical summary table */}
          <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '18px', fontSize: '12px' }}>
            <tbody>
              {[
                ['Provisional Diagnosis', diagnosisRaw],
                ['Chief Complaints', facts?.symptoms?.slice(0, 4).join(', ') || soap?.S?.split('.')[0] || '—'],
                ['Vitals', vitals.length > 0 ? vitals.join(' · ') : '—'],
                ['Allergies', allergies.length > 0 ? allergies.join(', ') : 'None reported'],
                ['Treatment Given', meds.length > 0 ? meds.map(m => `${m.name}${m.dosage ? ' ' + m.dosage : ''}`).join(', ') : '—'],
                ['Reason for Referral', details.reason || 'Further evaluation and speciality management'],
              ].map(([label, value]) => (
                <tr key={label} style={{ borderBottom: '1px solid #f0f0f0' }}>
                  <td style={{ padding: '7px 10px', fontWeight: 'bold', color: '#374151', width: '38%', verticalAlign: 'top' }}>{label}</td>
                  <td style={{ padding: '7px 10px', color: '#111', verticalAlign: 'top' }}>{value}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <p style={{ marginBottom: '14px' }}>
            Kindly examine the patient and advise further management. Please send a copy of your report for our records.
          </p>

          <p style={{ marginBottom: '32px' }}>Thanking you,</p>

          {/* Signature */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
            <div style={{ border: '1px dashed #d1d5db', borderRadius: '4px', width: '120px', height: '70px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ fontSize: '10px', color: '#9ca3af' }}>Clinic Stamp</span>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ height: '42px' }} />
              <div style={{ borderTop: '1px solid #374151', paddingTop: '4px', minWidth: '180px', textAlign: 'right' }}>
                <p style={{ margin: 0, fontWeight: 'bold', fontSize: '13px' }}>{doctorName ? `Dr. ${doctorName}` : "Referring Doctor"}</p>
                {profile.nmc && <p style={{ margin: '1px 0 0', fontSize: '10px', color: '#6b7280' }}>Reg. No. {profile.nmc}</p>}
              </div>
            </div>
          </div>

          {/* Footer */}
          <p style={{ marginTop: '20px', fontSize: '9px', color: '#9ca3af', borderTop: '1px solid #e5e7eb', paddingTop: '8px' }}>
            Generated via Lipi Health · AI-assisted clinical documentation · All clinical decisions verified by physician
          </p>

        </div>
      </div>
    </>
  );
}
