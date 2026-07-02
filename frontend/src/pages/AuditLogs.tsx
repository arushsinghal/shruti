import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAuditLogs, type AuditLogEntry } from '../lib/api';

const EVENT_LABELS: Record<string, { label: string; color: string }> = {
  data_accessed: { label: 'Data Accessed', color: 'bg-blue-50 text-blue-700 border-blue-200' },
  session_created: { label: 'Session Created', color: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  session_deleted: { label: 'Session Deleted', color: 'bg-red-50 text-red-700 border-red-200' },
  consent_granted: { label: 'Consent Given', color: 'bg-amber-50 text-amber-700 border-amber-200' },
  phi_erased: { label: 'PHI Erased', color: 'bg-purple-50 text-purple-700 border-purple-200' },
  prescription_viewed: { label: 'Rx Viewed', color: 'bg-cyan-50 text-cyan-700 border-cyan-200' },
  fhir_exported: { label: 'FHIR Export', color: 'bg-indigo-50 text-indigo-700 border-indigo-200' },
};

function formatTs(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  } catch {
    return ts;
  }
}

export default function AuditLogs() {
  const navigate = useNavigate();
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const PAGE_SIZE = 50;

  useEffect(() => {
    setLoading(true);
    getAuditLogs(PAGE_SIZE, page * PAGE_SIZE)
      .then(data => { setEntries(data.entries); setTotal(data.total); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [page]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-text-dark">
      <header className="border-b border-slate-200/80 sticky top-0 bg-white/90 backdrop-blur-md z-10 shadow-sm">
        <div className="max-w-5xl mx-auto px-3 sm:px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2 sm:gap-4">
            <button onClick={() => navigate('/dashboard')} className="text-slate-500 hover:text-indigo-600 transition-colors flex items-center text-xs font-semibold cursor-pointer">
              <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Dashboard
            </button>
            <div className="h-4 w-px bg-slate-200" />
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-gradient-to-br from-indigo-600 to-cyan-500 rounded-md flex items-center justify-center shadow-sm">
                <span className="font-bold text-white text-[10px]">श</span>
              </div>
              <span className="text-sm font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-700 to-cyan-700">Lipi</span>
            </div>
            <div className="h-4 w-px bg-slate-200" />
            <h1 className="text-sm font-bold text-slate-800">Audit Trail</h1>
          </div>
          <span className="text-xs text-slate-400 font-semibold">{total} events</span>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-3 sm:px-6 py-6">
        <div className="mb-4">
          <p className="text-xs text-slate-500">
            Complete log of data access, exports, and consent events for compliance. All times in IST.
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <svg className="animate-spin h-6 w-6 text-indigo-400" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        ) : entries.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-sm text-slate-400">No audit events recorded yet.</p>
          </div>
        ) : (
          <>
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200">
                    <th className="px-4 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Time</th>
                    <th className="px-4 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Event</th>
                    <th className="px-4 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest hidden sm:table-cell">Resource</th>
                    <th className="px-4 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest hidden md:table-cell">Details</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((e, i) => {
                    const ev = EVENT_LABELS[e.event_type] ?? { label: e.event_type, color: 'bg-slate-50 text-slate-600 border-slate-200' };
                    return (
                      <tr key={i} className="border-b border-slate-100 last:border-0 hover:bg-slate-50/50 transition-colors">
                        <td className="px-4 py-3 text-xs text-slate-500 whitespace-nowrap">{formatTs(e.timestamp)}</td>
                        <td className="px-4 py-3">
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${ev.color}`}>{ev.label}</span>
                        </td>
                        <td className="px-4 py-3 text-xs text-slate-600 hidden sm:table-cell">
                          <span className="font-mono text-[11px]">{e.resource_type}</span>
                          {e.resource_id && (
                            <span className="text-slate-400 ml-1 font-mono text-[10px]">#{e.resource_id.slice(0, 8)}</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-xs text-slate-400 hidden md:table-cell truncate max-w-[200px]">{e.details || '—'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-4">
                <button
                  onClick={() => setPage(p => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 disabled:text-slate-300 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <span className="text-xs text-slate-400">Page {page + 1} of {totalPages}</span>
                <button
                  onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                  disabled={page >= totalPages - 1}
                  className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 disabled:text-slate-300 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
