import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createSession, listSessions } from '../lib/api';
import type { ConsultationSession } from '../types/clinical';

const STATUS_COLORS: Record<string, string> = {
  created: 'bg-slate-100 text-slate-600 border border-slate-200',
  audio_uploaded: 'bg-blue-50 text-blue-700 border border-blue-100',
  transcribed: 'bg-indigo-50 text-indigo-700 border border-indigo-100',
  extracted: 'bg-purple-50 text-purple-700 border border-purple-100',
  memory_resolved: 'bg-amber-50 text-amber-700 border border-amber-100',
  soap_ready: 'bg-orange-50 text-orange-700 border border-orange-100',
  complete: 'bg-emerald-50 text-primary border border-primary/20',
};

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] ?? 'bg-slate-100 text-slate-600';
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${color}`}>
      {status.replace(/_/g, ' ')}
    </span>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<ConsultationSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cloudConsent = false;

  useEffect(() => {
    listSessions()
      .then(setSessions)
      .catch(() => setError('Failed to load consultations'))
      .finally(() => setLoading(false));
  }, []);

  async function handleNewConsultation() {
    setCreating(true);
    setError(null);
    try {
      const session = await createSession({ cloud_ai_consent: cloudConsent });
      navigate(`/consultation/${session.id}`);
    } catch {
      setError('Failed to initialize a new consultation session. Is the backend service running?');
      setCreating(false);
    }
  }

  return (
    <div className="min-h-screen bg-bg-warm font-sans text-text-dark">
      <header className="border-b border-slate-200/80 sticky top-0 bg-white/90 backdrop-blur-md z-10 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/')}
              className="text-slate-400 hover:text-primary transition-colors flex items-center text-xs font-semibold cursor-pointer"
            >
              <svg className="w-4 h-4 mr-1 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Home
            </button>
            <div className="h-4 w-px bg-slate-200"></div>
            <div className="flex items-center gap-2">
              <span className="font-serif font-bold text-primary text-base">श</span>
              <span className="text-sm font-bold text-text-dark tracking-tight">SHRUTI</span>
            </div>
            <div className="h-4 w-px bg-slate-200"></div>
            <button
              onClick={() => navigate('/analytics')}
              className="text-xs text-slate-500 hover:text-primary transition-colors font-medium flex items-center gap-1 cursor-pointer"
            >
              <svg className="w-3.5 h-3.5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Field Impact Overview
            </button>
            <div className="h-4 w-px bg-slate-200"></div>
            <button
              onClick={() => navigate('/about')}
              className="text-xs text-slate-500 hover:text-primary transition-colors font-medium cursor-pointer"
            >
              Methodology
            </button>
          </div>
          <div className="flex items-center gap-4">
            <span className="bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider hidden sm:inline-block">
              Venture Field Console
            </span>
            <span
              className="bg-emerald-50 text-primary border border-primary/20 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider hidden sm:inline-block"
              title="Clinical extraction, memory resolution, SOAP drafting, and CDS alerts run locally."
            >
              Local Clinical AI
            </span>
            <button
              onClick={handleNewConsultation}
              disabled={creating}
              className="bg-primary hover:bg-primary-dark disabled:opacity-50 text-white text-xs font-semibold px-3 py-1.5 rounded transition-all shadow-sm flex items-center gap-1.5 cursor-pointer"
            >
              {creating ? 'Initializing...' : '+ New Session'}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Local Processing Banner */}
        <div className="mb-6 rounded bg-primary/10 border border-primary/20 text-primary px-4 py-3 text-xs flex items-center gap-2.5">
          <svg className="w-4.5 h-4.5 shrink-0 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <span className="font-semibold">All consultation audio is processed locally. Personal Health Information (PHI) is scrubbed at the edge to maintain strict safety and data governance protocols.</span>
        </div>

        {error && (
          <div className="mb-6 rounded bg-red-50 text-alert-critical px-4 py-3 text-sm border border-red-100">
            {error}
          </div>
        )}

        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest">
            Recorded Consultations ({sessions.length})
          </h2>
        </div>

        {loading && (
          <div className="text-center py-20 border border-slate-200/80 rounded-lg bg-white shadow-sm flex flex-col items-center justify-center">
            <span className="text-slate-400 text-sm animate-pulse font-medium">Loading session list...</span>
          </div>
        )}

        {!loading && sessions.length === 0 && (
          <div className="text-center py-20 border border-slate-200 border-dashed rounded-lg bg-white shadow-sm">
            <p className="text-sm font-semibold text-slate-600">No consultation sessions found</p>
            <p className="text-xs text-slate-400 mt-1">Click "+ New Session" to begin recording.</p>
          </div>
        )}

        {!loading && sessions.length > 0 && (
          <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-xs uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-4 font-semibold">Patient Name</th>
                    <th className="px-6 py-4 font-semibold">Attending Doctor</th>
                    <th className="px-6 py-4 font-semibold">Date & Time</th>
                    <th className="px-6 py-4 font-semibold">Clinical AI Mode</th>
                    <th className="px-6 py-4 font-semibold">Processing Status</th>
                    <th className="px-6 py-4 text-right font-semibold">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {sessions.map((s) => (
                    <tr
                      key={s.id}
                      onClick={() => navigate(`/consultation/${s.id}`)}
                      className="hover:bg-slate-50/50 cursor-pointer transition-colors group"
                    >
                      <td className="px-6 py-4 text-slate-900 font-semibold">
                        {s.patient_name ?? 'Anonymous Patient'}
                      </td>
                      <td className="px-6 py-4 text-slate-600">
                        {s.doctor_name ? `Dr. ${s.doctor_name}` : '—'}
                      </td>
                      <td className="px-6 py-4 text-slate-500 text-xs">
                        {new Date(s.created_at).toLocaleDateString(undefined, { 
                          month: 'short', 
                          day: 'numeric', 
                          year: 'numeric',
                          hour: 'numeric', 
                          minute: '2-digit' 
                        })}
                      </td>
                      <td className="px-6 py-4 text-xs font-semibold">
                        <span className="text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">Local Only</span>
                      </td>
                      <td className="px-6 py-4">
                        <StatusBadge status={s.status} />
                      </td>
                      <td className="px-6 py-4 text-right">
                        <span className="text-primary group-hover:text-primary-dark font-semibold text-xs transition-colors flex items-center justify-end gap-1">
                          Open Session
                          <svg className="w-3.5 h-3.5 transform group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
                          </svg>
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
