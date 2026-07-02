import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { motion } from 'framer-motion';

interface InboxSession {
  id: string;
  patient_name: string;
  patient_phone: string;
  assigned_doctor_name: string;
  assigned_doctor_id: string;
  status: string;
  created_at: string;
  soap_snippet: string;
}

interface Doctor {
  id: string;
  name: string;
  specialization: string;
  role: string;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

const STATUS_COLORS: Record<string, string> = {
  complete: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  transcribed: 'bg-amber-50 text-amber-700 border-amber-200',
  extracted: 'bg-amber-50 text-amber-700 border-amber-200',
  soap_ready: 'bg-violet-50 text-violet-700 border-violet-200',
  created: 'bg-slate-50 text-slate-500 border-slate-200',
};

export default function ClinicInbox() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<InboxSession[]>([]);
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState(true);
  const [assigning, setAssigning] = useState<string | null>(null);
  const [selectedDoctor, setSelectedDoctor] = useState<Record<string, string>>({});
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.get('/clinic/inbox'),
      api.get('/clinic/doctors'),
    ]).then(([inboxRes, docRes]) => {
      setSessions(inboxRes.data.sessions || []);
      setDoctors(docRes.data.doctors || []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  async function assign(sessionId: string) {
    const doctorId = selectedDoctor[sessionId];
    if (!doctorId) return;
    const doctor = doctors.find(d => d.id === doctorId);
    setAssigning(sessionId);
    try {
      await api.post(`/clinic/sessions/${sessionId}/assign`, {
        doctor_user_id: doctorId,
        doctor_name: doctor?.name || '',
      });
      setSessions(prev => prev.map(s =>
        s.id === sessionId
          ? { ...s, assigned_doctor_name: doctor?.name || '', assigned_doctor_id: doctorId }
          : s
      ));
      setToast(`Assigned to ${doctor?.name}`);
      setTimeout(() => setToast(null), 3000);
    } catch {
      setToast('Assignment failed');
      setTimeout(() => setToast(null), 3000);
    } finally {
      setAssigning(null);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Toast */}
      {toast && (
        <div className="fixed top-4 right-4 z-50 bg-slate-800 text-white text-sm font-medium px-4 py-2 rounded-lg shadow-lg">
          {toast}
        </div>
      )}

      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-slate-400 hover:text-slate-700 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </button>
          <div>
            <h1 className="text-[15px] font-bold text-slate-900 leading-tight">WhatsApp Inbox</h1>
            <p className="text-[11px] text-slate-400">Triage incoming patient consultations</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="bg-violet-100 text-violet-700 text-[11px] font-bold px-2 py-0.5 rounded-full border border-violet-200">
            {sessions.length} sessions
          </span>
          <button
            onClick={() => { setLoading(true); api.get('/clinic/inbox').then(r => setSessions(r.data.sessions || [])).finally(() => setLoading(false)); }}
            className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6">
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="bg-white rounded-2xl border border-slate-200 p-5 animate-pulse">
                <div className="h-4 bg-slate-100 rounded w-1/3 mb-3" />
                <div className="h-3 bg-slate-100 rounded w-2/3 mb-2" />
                <div className="h-3 bg-slate-100 rounded w-1/2" />
              </div>
            ))}
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-20">
            <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto mb-4">
              <svg className="w-7 h-7 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <p className="text-slate-500 text-sm font-medium">No WhatsApp sessions yet</p>
            <p className="text-slate-400 text-xs mt-1">Sessions appear here when patients message your clinic's WhatsApp number</p>
          </div>
        ) : (
          <div className="space-y-3">
            {sessions.map((s, i) => {
              const statusColor = STATUS_COLORS[s.status] ?? STATUS_COLORS.created;
              const isAssigned = !!s.assigned_doctor_name;
              return (
                <motion.div
                  key={s.id}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04, duration: 0.25 }}
                  className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
                >
                  <div className="p-5">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        {/* Patient info */}
                        <div className="flex items-center gap-2 mb-1">
                          <div className="w-7 h-7 rounded-lg bg-violet-100 flex items-center justify-center shrink-0">
                            <svg className="w-3.5 h-3.5 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                          </div>
                          <span className="text-[13px] font-semibold text-slate-900 truncate">
                            {s.patient_name !== 'Unknown' ? s.patient_name : `Patient +${s.patient_phone}`}
                          </span>
                          {s.patient_phone && (
                            <span className="text-[11px] text-slate-400 font-mono shrink-0">
                              {s.patient_phone.slice(-10)}
                            </span>
                          )}
                        </div>

                        {/* SOAP snippet */}
                        {s.soap_snippet && (
                          <p className="text-[12px] text-slate-500 leading-relaxed line-clamp-2 mb-2 pl-9">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mr-1">AI:</span>
                            {s.soap_snippet}
                          </p>
                        )}

                        {/* Meta row */}
                        <div className="flex items-center gap-2 pl-9">
                          <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border capitalize ${statusColor}`}>
                            {s.status.replace(/_/g, ' ')}
                          </span>
                          <span className="text-[11px] text-slate-400">{timeAgo(s.created_at)}</span>
                          {isAssigned && (
                            <span className="text-[11px] text-emerald-600 font-medium">
                              → {s.assigned_doctor_name}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          onClick={() => navigate(`/review/${s.id}`)}
                          className="text-[11px] font-semibold text-slate-500 hover:text-slate-700 border border-slate-200 hover:border-slate-300 px-2.5 py-1.5 rounded-lg transition-all"
                        >
                          View
                        </button>
                        <div className="flex items-center gap-1.5">
                          <select
                            value={selectedDoctor[s.id] || ''}
                            onChange={e => setSelectedDoctor(p => ({ ...p, [s.id]: e.target.value }))}
                            className="text-[11px] border border-slate-200 rounded-lg px-2 py-1.5 bg-white text-slate-700 focus:outline-none focus:border-violet-400 min-w-[130px]"
                          >
                            <option value="">Assign to…</option>
                            {doctors.map(d => (
                              <option key={d.id} value={d.id}>
                                {d.name}{d.specialization ? ` · ${d.specialization}` : ''}
                              </option>
                            ))}
                          </select>
                          <button
                            onClick={() => assign(s.id)}
                            disabled={!selectedDoctor[s.id] || assigning === s.id}
                            className="text-[11px] font-semibold bg-violet-600 hover:bg-violet-700 disabled:opacity-40 disabled:cursor-not-allowed text-white px-3 py-1.5 rounded-lg transition-all"
                          >
                            {assigning === s.id ? '…' : 'Assign'}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
