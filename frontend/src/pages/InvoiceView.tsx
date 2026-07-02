import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';

interface BillingRow {
  id: string;
  session_id: string;
  amount_inr: number;
  notes: string;
  date: string;
  patient_name: string;
  doctor_name: string;
  signed: boolean;
}

interface Summary {
  month: string;
  month_key: string;
  total_inr: number;
  consultation_count: number;
  rows: BillingRow[];
}

function monthOptions() {
  const opts = [];
  const now = new Date();
  for (let i = 0; i < 6; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    const label = d.toLocaleString('default', { month: 'long', year: 'numeric' });
    opts.push({ key, label });
  }
  return opts;
}

export default function InvoiceView() {
  const navigate = useNavigate();
  const options = monthOptions();
  const [selectedMonth, setSelectedMonth] = useState(options[0].key);
  const [data, setData] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    setError('');
    api.get(`/internal/billing/summary?month=${selectedMonth}`)
      .then(r => setData(r.data))
      .catch(e => setError(e.response?.data?.detail || 'Failed to load billing data'))
      .finally(() => setLoading(false));
  }, [selectedMonth]);

  function copyInvoiceText() {
    if (!data) return;
    const lines = [
      `Lipi — ${data.month} Invoice`,
      `Consultations: ${data.consultation_count}`,
      `Total: ₹${data.total_inr.toLocaleString('en-IN')}`,
      '',
      ...data.rows.map(r =>
        `${r.date}  ${r.patient_name.padEnd(18)} ${r.doctor_name.padEnd(18)} ₹${r.amount_inr}`
      ),
    ];
    navigator.clipboard.writeText(lines.join('\n'))
      .then(() => alert('Invoice text copied to clipboard'))
      .catch(() => {});
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <button
              onClick={() => navigate('/dashboard')}
              className="text-xs text-slate-500 hover:text-slate-700 mb-1 block"
            >
              ← Dashboard
            </button>
            <h1 className="text-xl font-bold text-slate-800">Billing Invoices</h1>
            <p className="text-sm text-slate-500">Per-consultation billing — WhatsApp consultations</p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={selectedMonth}
              onChange={e => setSelectedMonth(e.target.value)}
              className="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {options.map(o => (
                <option key={o.key} value={o.key}>{o.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Summary cards */}
        {data && (
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 text-center">
              <p className="text-3xl font-bold text-slate-800">{data.consultation_count}</p>
              <p className="text-xs text-slate-500 mt-1">Consultations</p>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 text-center">
              <p className="text-3xl font-bold text-emerald-700">
                ₹{data.total_inr.toLocaleString('en-IN')}
              </p>
              <p className="text-xs text-slate-500 mt-1">Total billed</p>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 text-center">
              <p className="text-3xl font-bold text-slate-800">
                {data.consultation_count > 0
                  ? `₹${Math.round(data.total_inr / data.consultation_count)}`
                  : '—'}
              </p>
              <p className="text-xs text-slate-500 mt-1">Avg per consult</p>
            </div>
          </div>
        )}

        {/* Action bar */}
        {data && data.rows.length > 0 && (
          <div className="flex justify-end mb-3">
            <button
              onClick={copyInvoiceText}
              className="text-sm text-slate-600 hover:text-slate-900 bg-white border border-slate-200 rounded-lg px-4 py-2 shadow-sm"
            >
              Copy invoice text
            </button>
          </div>
        )}

        {/* Table */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          {loading ? (
            <div className="py-16 text-center text-slate-400 text-sm">Loading...</div>
          ) : error ? (
            <div className="py-16 text-center text-red-500 text-sm">{error}</div>
          ) : !data || data.rows.length === 0 ? (
            <div className="py-16 text-center text-slate-400 text-sm">
              No consultations billed in {data?.month || selectedMonth}
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left text-xs font-semibold text-slate-500 px-4 py-3">Date</th>
                  <th className="text-left text-xs font-semibold text-slate-500 px-4 py-3">Patient</th>
                  <th className="text-left text-xs font-semibold text-slate-500 px-4 py-3">Doctor</th>
                  <th className="text-left text-xs font-semibold text-slate-500 px-4 py-3">Type</th>
                  <th className="text-left text-xs font-semibold text-slate-500 px-4 py-3">Signed</th>
                  <th className="text-right text-xs font-semibold text-slate-500 px-4 py-3">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.rows.map(row => (
                  <tr key={row.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 text-slate-600 whitespace-nowrap">{row.date}</td>
                    <td className="px-4 py-3 text-slate-800">{row.patient_name}</td>
                    <td className="px-4 py-3 text-slate-600">{row.doctor_name}</td>
                    <td className="px-4 py-3 text-slate-500 text-xs">{row.notes}</td>
                    <td className="px-4 py-3">
                      {row.signed ? (
                        <span className="text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-2 py-0.5">Signed</span>
                      ) : (
                        <span className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-full px-2 py-0.5">Pending</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-slate-800">
                      ₹{row.amount_inr}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="border-t-2 border-slate-200 bg-slate-50">
                <tr>
                  <td colSpan={5} className="px-4 py-3 text-sm font-semibold text-slate-700">
                    Total — {data.consultation_count} consultations
                  </td>
                  <td className="px-4 py-3 text-right text-base font-bold text-emerald-700">
                    ₹{data.total_inr.toLocaleString('en-IN')}
                  </td>
                </tr>
              </tfoot>
            </table>
          )}
        </div>

        <p className="text-center text-xs text-slate-400 mt-6">
          Internal view · WhatsApp-originated consultations only · {data?.month}
        </p>
      </div>
    </div>
  );
}
