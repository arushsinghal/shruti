import { useState, useRef } from 'react';
import { useReactToPrint } from 'react-to-print';
import type { ProcessClinicalResponse } from '../types/clinical';

interface Props {
  results: ProcessClinicalResponse;
  patientName?: string;
  doctorName?: string;
}

interface DischargeSummaryForm {
  admissionDate: string;
  dischargeDate: string;
  conditionAtDischarge: string;
  ward: string;
  bedNo: string;
}

export default function DischargeSummary({ results, patientName, doctorName }: Props) {
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<DischargeSummaryForm>({
    admissionDate: new Date().toISOString().split('T')[0],
    dischargeDate: new Date().toISOString().split('T')[0],
    conditionAtDischarge: 'Stable',
    ward: '',
    bedNo: '',
  });
  const printRef = useRef<HTMLDivElement>(null);

  const handlePrint = useReactToPrint({ contentRef: printRef });

  const { facts, soap } = results;
  const meds = facts?.medications ?? [];
  const vitals = facts?.vitals ?? [];
  const investigations = facts?.investigations ?? [];
  const allergies = facts?.allergies ?? [];
  const followUpRaw = (facts as any)?.follow_up;
  const followUp = Array.isArray(followUpRaw) ? followUpRaw : followUpRaw ? [followUpRaw] : [];

  const diagnosis = soap?.A?.split('.')[0]?.trim() || '—';
  const printDate = new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' });

  return (
    <>
      <button
        onClick={() => setShowModal(true)}
        className="flex items-center gap-1.5 text-xs font-medium text-rose-700 hover:text-rose-900 border border-rose-200 hover:border-rose-400 bg-rose-50 hover:bg-rose-100 rounded px-3 py-1.5 transition-all"
        title="Generate Discharge Summary"
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
        Discharge
      </button>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg border border-slate-200 overflow-hidden">
            <div className="px-6 pt-6 pb-4 border-b border-slate-100">
              <h2 className="text-base font-bold text-slate-900">Discharge Summary</h2>
              <p className="text-xs text-slate-400 mt-0.5">Fill in discharge details — clinical data auto-filled from session</p>
            </div>

            <div className="px-6 py-5 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1.5">Admission Date</label>
                  <input
                    type="date"
                    value={form.admissionDate}
                    onChange={e => setForm(f => ({ ...f, admissionDate: e.target.value }))}
                    className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm text-slate-800 outline-none focus:border-primary focus:ring-1 focus:ring-primary/20"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1.5">Discharge Date</label>
                  <input
                    type="date"
                    value={form.dischargeDate}
                    onChange={e => setForm(f => ({ ...f, dischargeDate: e.target.value }))}
                    className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm text-slate-800 outline-none focus:border-primary focus:ring-1 focus:ring-primary/20"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1.5">Ward</label>
                  <input
                    type="text"
                    value={form.ward}
                    onChange={e => setForm(f => ({ ...f, ward: e.target.value }))}
                    placeholder="e.g. General Ward"
                    className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm text-slate-800 outline-none focus:border-primary focus:ring-1 focus:ring-primary/20"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1.5">Bed No.</label>
                  <input
                    type="text"
                    value={form.bedNo}
                    onChange={e => setForm(f => ({ ...f, bedNo: e.target.value }))}
                    placeholder="e.g. 12B"
                    className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm text-slate-800 outline-none focus:border-primary focus:ring-1 focus:ring-primary/20"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">Condition at Discharge</label>
                <select
                  value={form.conditionAtDischarge}
                  onChange={e => setForm(f => ({ ...f, conditionAtDischarge: e.target.value }))}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm text-slate-800 outline-none focus:border-primary focus:ring-1 focus:ring-primary/20"
                >
                  <option>Stable</option>
                  <option>Improved</option>
                  <option>Recovered</option>
                  <option>Guarded</option>
                  <option>Against Medical Advice</option>
                  <option>Referred</option>
                  <option>Expired</option>
                </select>
              </div>
            </div>

            <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex gap-3 justify-end">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 text-sm text-slate-500 hover:text-slate-700 font-medium transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={() => { setShowModal(false); setTimeout(() => handlePrint(), 100); }}
                className="px-6 py-2 bg-primary hover:bg-primary-dark text-white text-sm font-semibold rounded-lg transition-all shadow-sm cursor-pointer"
              >
                Print Discharge Summary
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Printable content — hidden from screen */}
      <div className="hidden">
        <div ref={printRef} style={{ fontFamily: 'Times New Roman, serif', padding: '32px', fontSize: '13px', color: '#000' }}>
          {/* Header */}
          <div style={{ textAlign: 'center', borderBottom: '2px solid #000', paddingBottom: '12px', marginBottom: '16px' }}>
            <p style={{ fontWeight: 'bold', fontSize: '18px', marginBottom: '2px' }}>DISCHARGE SUMMARY</p>
            <p style={{ fontSize: '12px', color: '#555' }}>Date: {printDate}</p>
          </div>

          {/* Patient Info */}
          <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '16px', fontSize: '12px' }}>
            <tbody>
              <tr>
                <td style={{ padding: '4px 8px', width: '50%', border: '1px solid #ddd' }}><strong>Patient Name:</strong> {patientName || '—'}</td>
                <td style={{ padding: '4px 8px', width: '50%', border: '1px solid #ddd' }}><strong>Treating Doctor:</strong> {doctorName || '—'}</td>
              </tr>
              <tr>
                <td style={{ padding: '4px 8px', border: '1px solid #ddd' }}><strong>Admission Date:</strong> {form.admissionDate ? new Date(form.admissionDate).toLocaleDateString('en-IN') : '—'}</td>
                <td style={{ padding: '4px 8px', border: '1px solid #ddd' }}><strong>Discharge Date:</strong> {form.dischargeDate ? new Date(form.dischargeDate).toLocaleDateString('en-IN') : '—'}</td>
              </tr>
              <tr>
                <td style={{ padding: '4px 8px', border: '1px solid #ddd' }}><strong>Ward:</strong> {form.ward || '—'}</td>
                <td style={{ padding: '4px 8px', border: '1px solid #ddd' }}><strong>Bed No.:</strong> {form.bedNo || '—'}</td>
              </tr>
              <tr>
                <td colSpan={2} style={{ padding: '4px 8px', border: '1px solid #ddd' }}><strong>Condition at Discharge:</strong> {form.conditionAtDischarge}</td>
              </tr>
            </tbody>
          </table>

          {/* Clinical Details */}
          <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '16px', fontSize: '12px' }}>
            <tbody>
              <tr style={{ background: '#f5f5f5' }}>
                <th style={{ padding: '6px 8px', border: '1px solid #ddd', textAlign: 'left', width: '30%' }}>Clinical Category</th>
                <th style={{ padding: '6px 8px', border: '1px solid #ddd', textAlign: 'left' }}>Details</th>
              </tr>
              <tr>
                <td style={{ padding: '6px 8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Diagnosis</td>
                <td style={{ padding: '6px 8px', border: '1px solid #ddd' }}>{diagnosis}</td>
              </tr>
              <tr>
                <td style={{ padding: '6px 8px', border: '1px solid #ddd', fontWeight: 'bold' }}>History & Presentation</td>
                <td style={{ padding: '6px 8px', border: '1px solid #ddd' }}>{soap?.S || '—'}</td>
              </tr>
              <tr>
                <td style={{ padding: '6px 8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Vitals on Admission</td>
                <td style={{ padding: '6px 8px', border: '1px solid #ddd' }}>{vitals.length > 0 ? vitals.join(', ') : '—'}</td>
              </tr>
              <tr>
                <td style={{ padding: '6px 8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Allergies</td>
                <td style={{ padding: '6px 8px', border: '1px solid #ddd', color: allergies.length > 0 ? '#c00' : 'inherit' }}>
                  {allergies.length > 0 ? allergies.join(', ') : 'None reported'}
                </td>
              </tr>
              <tr>
                <td style={{ padding: '6px 8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Investigations</td>
                <td style={{ padding: '6px 8px', border: '1px solid #ddd' }}>{investigations.length > 0 ? investigations.join(', ') : '—'}</td>
              </tr>
              <tr>
                <td style={{ padding: '6px 8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Treatment Given</td>
                <td style={{ padding: '6px 8px', border: '1px solid #ddd' }}>
                  {meds.length > 0
                    ? meds.map(m => `${m.name.charAt(0).toUpperCase() + m.name.slice(1)} ${m.dosage || ''} ${m.frequency || ''}`.trim()).join('; ')
                    : '—'}
                </td>
              </tr>
              <tr>
                <td style={{ padding: '6px 8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Discharge Medications</td>
                <td style={{ padding: '6px 8px', border: '1px solid #ddd' }}>
                  {meds.length > 0
                    ? meds.map(m => `${m.name.charAt(0).toUpperCase() + m.name.slice(1)} ${m.dosage || ''} — ${m.frequency || ''}`.trim()).join('\n')
                    : 'As per prescription'}
                </td>
              </tr>
              <tr>
                <td style={{ padding: '6px 8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Follow-up Instructions</td>
                <td style={{ padding: '6px 8px', border: '1px solid #ddd' }}>{followUp.length > 0 ? followUp.join('; ') : soap?.P?.split('.').find(s => s.toLowerCase().includes('follow')) || '—'}</td>
              </tr>
            </tbody>
          </table>

          {/* Clinical Note */}
          <div style={{ border: '1px solid #ddd', padding: '10px', marginBottom: '24px', fontSize: '12px' }}>
            <strong>Assessment & Clinical Notes:</strong>
            <p style={{ marginTop: '6px', lineHeight: '1.6' }}>{soap?.A || '—'}</p>
          </div>

          {/* Signature */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '32px' }}>
            <div style={{ textAlign: 'center', minWidth: '200px' }}>
              <div style={{ borderTop: '1px solid #000', paddingTop: '6px' }}>
                <p style={{ fontWeight: 'bold', fontSize: '12px' }}>{doctorName || 'Treating Physician'}</p>
                <p style={{ fontSize: '11px', color: '#555' }}>Signature & Stamp</p>
              </div>
            </div>
          </div>

          <p style={{ textAlign: 'center', fontSize: '10px', color: '#888', marginTop: '24px', borderTop: '1px solid #eee', paddingTop: '8px' }}>
            Generated by Lipi Health · For Medical Records Only · {printDate}
          </p>
        </div>
      </div>
    </>
  );
}
