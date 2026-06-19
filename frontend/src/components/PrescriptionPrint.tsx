import { useRef } from 'react';
import { useReactToPrint } from 'react-to-print';
import type { ProcessClinicalResponse } from '../types/clinical';

interface Props {
  results: ProcessClinicalResponse;
  patientName?: string;
  doctorName?: string;
}

export default function PrescriptionPrint({ results, patientName, doctorName }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  const handlePrint = useReactToPrint({
    contentRef: ref,
    documentTitle: `Prescription_${patientName ?? 'Patient'}_${new Date().toLocaleDateString('en-IN')}`,
  });

  const { facts } = results;
  const meds = facts?.medications ?? [];
  const investigations = facts?.investigations ?? [];
  const followUp = (facts as any)?.follow_up ?? [];
  const allergies = facts?.allergies ?? [];
  const today = new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' });

  return (
    <>
      <button
        onClick={handlePrint}
        className="flex items-center gap-1.5 text-xs font-medium text-green-700 hover:text-green-900 border border-green-200 hover:border-green-400 bg-green-50 hover:bg-green-100 rounded px-3 py-1.5 transition-all"
        title="Print Prescription (Rx)"
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        Print Rx
      </button>

      <div className="hidden">
        <div ref={ref} style={{ fontFamily: 'Arial, sans-serif', padding: '32px', maxWidth: '680px', margin: '0 auto', fontSize: '13px' }}>
          {/* Header */}
          <div style={{ borderBottom: '3px solid #059669', paddingBottom: '12px', marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
            <div>
              <h1 style={{ fontSize: '20px', fontWeight: 'bold', color: '#064e3b', margin: 0 }}>
                {doctorName ? `Dr. ${doctorName}` : 'Physician'}
              </h1>
              <p style={{ fontSize: '11px', color: '#6b7280', margin: '2px 0 0' }}>MBBS | General Physician</p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <p style={{ fontSize: '12px', color: '#374151', margin: 0 }}>Date: {today}</p>
              <p style={{ fontSize: '12px', color: '#374151', margin: '2px 0 0' }}>
                Patient: <strong>{patientName ?? 'Anonymous'}</strong>
              </p>
            </div>
          </div>

          {/* Rx Symbol */}
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#059669', marginBottom: '12px' }}>℞</div>

          {/* Allergies warning */}
          {allergies.length > 0 && (
            <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', padding: '8px 12px', marginBottom: '16px' }}>
              <p style={{ margin: 0, color: '#dc2626', fontWeight: 'bold', fontSize: '12px' }}>
                ⚠ ALLERGY: {allergies.map(a => a.toUpperCase()).join(', ')}
              </p>
            </div>
          )}

          {/* Medications */}
          {meds.length > 0 ? (
            <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px' }}>
              <thead>
                <tr style={{ background: '#f0fdf4', borderBottom: '2px solid #059669' }}>
                  <th style={{ padding: '8px 10px', textAlign: 'left', fontSize: '11px', color: '#065f46', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Medicine</th>
                  <th style={{ padding: '8px 10px', textAlign: 'left', fontSize: '11px', color: '#065f46', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Dose</th>
                  <th style={{ padding: '8px 10px', textAlign: 'left', fontSize: '11px', color: '#065f46', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Frequency</th>
                  <th style={{ padding: '8px 10px', textAlign: 'left', fontSize: '11px', color: '#065f46', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Duration</th>
                </tr>
              </thead>
              <tbody>
                {meds.map((m, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #e5e7eb', background: i % 2 === 0 ? '#fff' : '#f9fafb' }}>
                    <td style={{ padding: '10px', fontWeight: 'bold', color: '#111827', textTransform: 'capitalize' }}>{m.name}</td>
                    <td style={{ padding: '10px', color: '#374151' }}>{m.dosage || '—'}</td>
                    <td style={{ padding: '10px', color: '#374151' }}>{m.frequency || '—'}</td>
                    <td style={{ padding: '10px', color: '#374151' }}>As directed</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p style={{ color: '#6b7280', fontStyle: 'italic', marginBottom: '20px' }}>No medications recorded.</p>
          )}

          {/* Investigations */}
          {investigations.length > 0 && (
            <div style={{ marginBottom: '16px' }}>
              <p style={{ fontWeight: 'bold', color: '#1e3a5f', marginBottom: '6px', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Investigations Ordered</p>
              <p style={{ margin: 0, color: '#374151' }}>{investigations.join(', ')}</p>
            </div>
          )}

          {/* Follow up */}
          {followUp.length > 0 && (
            <div style={{ marginBottom: '16px' }}>
              <p style={{ fontWeight: 'bold', color: '#1e3a5f', marginBottom: '6px', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Follow Up</p>
              <p style={{ margin: 0, color: '#374151' }}>{followUp.join(', ')}</p>
            </div>
          )}

          {/* Signature */}
          <div style={{ marginTop: '40px', borderTop: '1px solid #d1d5db', paddingTop: '16px', display: 'flex', justifyContent: 'flex-end' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ height: '40px' }} />
              <p style={{ margin: 0, borderTop: '1px solid #374151', paddingTop: '4px', fontSize: '12px', color: '#374151', minWidth: '160px' }}>
                {doctorName ? `Dr. ${doctorName}` : "Doctor's Signature"}
              </p>
            </div>
          </div>

          {/* Footer */}
          <p style={{ marginTop: '16px', fontSize: '10px', color: '#9ca3af', textAlign: 'center' }}>
            AI-assisted prescription — physician reviewed and signed · Lipi Health
          </p>
        </div>
      </div>
    </>
  );
}
