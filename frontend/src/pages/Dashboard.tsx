import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createSession, listSessions } from '../lib/api';
import type { ConsultationSession, SessionMode } from '../types/clinical';
import { MODE_LABELS, MODE_COLORS } from '../types/clinical';

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

const MODE_ICONS: Record<SessionMode, React.ReactNode> = {
  health: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
    </svg>
  ),
  government: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  legal: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
    </svg>
  ),
  general: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  ),
};

const MODE_DESCS: Record<SessionMode, string> = {
  health:     'Doctor-patient consultation → SOAP note',
  government: 'Police dictation → FIR report',
  legal:      'Legal proceedings → Affidavit / Petition',
  general:    'Any audio → Transcript + summary',
};

export default function Dashboard() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<ConsultationSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showModeModal, setShowModeModal] = useState(false);
  const [selectedMode, setSelectedMode] = useState<SessionMode>('health');

  useEffect(() => {
    listSessions()
      .then(setSessions)
      .catch(() => setError('Failed to load consultations'))
      .finally(() => setLoading(false));
  }, []);

  async function handleNewConsultation() {
    setCreating(true);
    setShowModeModal(false);
    setError(null);
    try {
      const session = await createSession({ cloud_ai_consent: false, mode: selectedMode });
      navigate(`/consultation/${session.id}`);
    } catch {
      setError('Failed to initialize a new session. Is the backend service running?');
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
              <span className="font-bold text-primary text-base">श</span>
              <span className="text-sm font-bold text-text-dark tracking-tight">Lipi</span>
            </div>
            <div className="h-4 w-px bg-slate-200"></div>
            <button
              onClick={() => navigate('/analytics')}
              className="text-xs text-slate-500 hover:text-primary transition-colors font-medium flex items-center gap-1 cursor-pointer"
            >
              <svg className="w-3.5 h-3.5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              AI Ops Overview
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
              Lipi Workspace
            </span>
            <button
              onClick={() => setShowModeModal(true)}
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
          <span className="font-semibold">Audio is transcribed via Sarvam AI (India). Transcript identifiers are scrubbed before storage. Raw audio is deleted after note generation.</span>
        </div>

        {error && (
          <div className="mb-6 rounded bg-red-50 text-alert-critical px-4 py-3 text-sm border border-red-100">
            {error}
          </div>
        )}

        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest">
            Sessions ({sessions.length})
          </h2>
        </div>

        {loading && (
          <div className="text-center py-20 border border-slate-200/80 rounded-lg bg-white shadow-sm flex flex-col items-center justify-center">
            <span className="text-slate-400 text-sm animate-pulse font-medium">Loading session list...</span>
          </div>
        )}

        {!loading && sessions.length === 0 && (
          <div className="text-center py-20 border border-slate-200 border-dashed rounded-lg bg-white shadow-sm">
            <p className="text-sm font-semibold text-slate-600">No sessions yet</p>
            <p className="text-xs text-slate-400 mt-1">Click "+ New Session" to start — health, government, or legal.</p>
          </div>
        )}

        {!loading && sessions.length > 0 && (
          <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-xs uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-4 font-semibold">Name / Subject</th>
                    <th className="px-6 py-4 font-semibold">Professional</th>
                    <th className="px-6 py-4 font-semibold">Date & Time</th>
                    <th className="px-6 py-4 font-semibold">Mode</th>
                    <th className="px-6 py-4 font-semibold">Status</th>
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
                        {s.patient_name ?? 'Anonymous'}
                      </td>
                      <td className="px-6 py-4 text-slate-600">
                        {s.doctor_name || '—'}
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
                        <span className={`px-1.5 py-0.5 rounded border text-[10px] font-bold uppercase tracking-wide ${MODE_COLORS[s.mode || 'health']}`}>
                          {(s.mode || 'health').charAt(0).toUpperCase() + (s.mode || 'health').slice(1)}
                        </span>
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

      {/* Mode Selection Modal */}
      {showModeModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md border border-slate-200">
            <div className="p-6 border-b border-slate-100">
              <h2 className="text-base font-bold text-slate-800">New Session — Select Mode</h2>
              <p className="text-xs text-slate-400 mt-1">Choose how Lipi should process this recording.</p>
            </div>
            <div className="p-4 space-y-2">
              {(Object.keys(MODE_LABELS) as SessionMode[]).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setSelectedMode(mode)}
                  className={`w-full flex items-center gap-4 p-4 rounded-lg border-2 text-left transition-all cursor-pointer ${
                    selectedMode === mode
                      ? 'border-primary bg-primary/5'
                      : 'border-slate-200 hover:border-slate-300 bg-white'
                  }`}
                >
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
                    selectedMode === mode ? 'bg-primary text-white' : 'bg-slate-100 text-slate-500'
                  }`}>
                    {MODE_ICONS[mode]}
                  </div>
                  <div>
                    <p className={`text-sm font-bold ${selectedMode === mode ? 'text-primary' : 'text-slate-700'}`}>
                      {MODE_LABELS[mode]}
                    </p>
                    <p className="text-xs text-slate-400 mt-0.5">{MODE_DESCS[mode]}</p>
                  </div>
                  {selectedMode === mode && (
                    <svg className="w-4 h-4 text-primary ml-auto shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  )}
                </button>
              ))}
            </div>
            <div className="p-4 border-t border-slate-100 flex gap-3 justify-end">
              <button
                onClick={() => setShowModeModal(false)}
                className="px-4 py-2 text-sm text-slate-500 hover:text-slate-700 font-medium transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleNewConsultation}
                className="px-5 py-2 bg-primary hover:bg-primary-dark text-white text-sm font-semibold rounded-lg transition-all shadow-sm cursor-pointer"
              >
                Start Session →
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
