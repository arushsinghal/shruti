import { useEffect, useState } from 'react';
import api from '../lib/api';

interface QueueSession {
  id: string;
  patient_name: string;
  doctor_name: string;
  created_at: string;
  received_at: string | null;
  delivered_at: string | null;
  signed_at: string | null;
  held: boolean;
  reviewer_action: string | null;
  status: string;
  sla_seconds: number | null;
}

interface SessionDetail {
  id: string;
  patient_name: string;
  doctor_name: string;
  transcript: string;
  facts: Record<string, unknown>;
  soap: Record<string, string>;
  diagnoses_annotated: Array<{ name: string; icd10: string | null }>;
  confidence: Record<string, number>;
  received_at: string | null;
  delivered_at: string | null;
  signed_at: string | null;
  held: boolean;
  reviewer_action: string | null;
  reviewer_note: string | null;
  patient_phone: string | null;
  status: string;
}

function SlaChip({ seconds }: { seconds: number | null }) {
  if (seconds === null) return <span className="text-xs text-slate-400">—</span>;
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  const label = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  const color = seconds > 300 ? 'text-red-600 bg-red-50 border-red-200'
    : seconds > 180 ? 'text-amber-600 bg-amber-50 border-amber-200'
    : 'text-emerald-700 bg-emerald-50 border-emerald-200';
  return (
    <span className={`text-xs font-semibold rounded-full px-2 py-0.5 border ${color}`}>{label}</span>
  );
}

function ConfidenceBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = score >= 0.85 ? 'bg-emerald-500' : score >= 0.70 ? 'bg-amber-400' : 'bg-red-400';
  return (
    <div className="flex items-center gap-1.5">
      <div className="flex-1 bg-slate-100 rounded-full h-1.5 overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-500 w-8 text-right">{pct}%</span>
    </div>
  );
}

export default function ReviewQueue() {
  const [sessions, setSessions] = useState<QueueSession[]>([]);
  const [holdMode, setHoldMode] = useState(false);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<SessionDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionResult, setActionResult] = useState<string | null>(null);

  async function loadQueue() {
    setLoading(true);
    try {
      const r = await api.get('/internal/review-queue');
      setSessions(r.data.sessions || []);
      setHoldMode(r.data.hold_mode || false);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function loadDetail(id: string) {
    setSelected(null);
    setDetailLoading(true);
    setActionResult(null);
    try {
      const r = await api.get(`/internal/review-queue/${id}`);
      setSelected(r.data);
    } catch (e) {
      console.error(e);
    } finally {
      setDetailLoading(false);
    }
  }

  async function approve(id: string) {
    setActionLoading(true);
    try {
      const r = await api.post(`/internal/review-queue/${id}/approve`, { reviewer_note: '' });
      setActionResult(r.data.whatsapp_sent ? 'Approved — sign link sent to doctor.' : 'Approved. (WhatsApp not sent — no phone on file.)');
      await loadQueue();
      setSelected(null);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setActionResult('Error: ' + (err.response?.data?.detail || 'Unknown error'));
    } finally {
      setActionLoading(false);
    }
  }

  async function reject(id: string) {
    setActionLoading(true);
    try {
      await api.post(`/internal/review-queue/${id}/reject`);
      setActionResult('Rejected — marked for re-transcription.');
      await loadQueue();
      setSelected(null);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setActionResult('Error: ' + (err.response?.data?.detail || 'Unknown error'));
    } finally {
      setActionLoading(false);
    }
  }

  useEffect(() => { loadQueue(); }, []);

  const statusBadge = (s: QueueSession) => {
    if (s.reviewer_action === 'approved') return <span className="text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-2 py-0.5">Approved</span>;
    if (s.reviewer_action === 'rejected') return <span className="text-xs text-red-700 bg-red-50 border border-red-200 rounded-full px-2 py-0.5">Rejected</span>;
    if (s.signed_at) return <span className="text-xs text-blue-700 bg-blue-50 border border-blue-200 rounded-full px-2 py-0.5">Signed</span>;
    if (s.held) return <span className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-full px-2 py-0.5">Held</span>;
    if (s.delivered_at) return <span className="text-xs text-slate-600 bg-slate-50 border border-slate-200 rounded-full px-2 py-0.5">Sent</span>;
    return <span className="text-xs text-slate-400 bg-slate-50 border border-slate-200 rounded-full px-2 py-0.5">Pending</span>;
  };

  return (
    <div className="flex h-screen bg-slate-50">
      {/* Queue list */}
      <div className="w-80 flex-shrink-0 bg-white border-r border-slate-200 flex flex-col">
        <div className="p-4 border-b border-slate-100">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-slate-800">Review Queue</h2>
            <button onClick={loadQueue} className="text-xs text-blue-600 hover:underline">Refresh</button>
          </div>
          <div className={`mt-2 text-xs font-medium rounded-full px-2 py-0.5 inline-block ${holdMode ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-500'}`}>
            {holdMode ? 'HOLD MODE ON' : 'Monitor mode'}
          </div>
        </div>

        {loading ? (
          <div className="flex-1 flex items-center justify-center text-sm text-slate-400">Loading...</div>
        ) : sessions.length === 0 ? (
          <div className="flex-1 flex items-center justify-center text-sm text-slate-400 p-4 text-center">
            {holdMode ? 'No notes held for review.' : 'No recent WhatsApp sessions.'}
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto">
            {sessions.map(s => (
              <button
                key={s.id}
                onClick={() => loadDetail(s.id)}
                className={`w-full text-left p-3 border-b border-slate-100 hover:bg-slate-50 transition-colors ${selected?.id === s.id ? 'bg-blue-50' : ''}`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-slate-800 truncate">{s.patient_name}</p>
                    <p className="text-xs text-slate-500 truncate">{s.doctor_name}</p>
                  </div>
                  {statusBadge(s)}
                </div>
                <div className="flex items-center gap-2 mt-1.5">
                  <span className="text-[11px] text-slate-400">
                    {new Date(s.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  <SlaChip seconds={s.sla_seconds} />
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Detail panel */}
      <div className="flex-1 overflow-y-auto p-6">
        {actionResult && (
          <div className="mb-4 bg-blue-50 border border-blue-200 rounded-xl px-4 py-3 text-sm text-blue-800 flex items-center justify-between">
            {actionResult}
            <button onClick={() => setActionResult(null)} className="text-blue-400 hover:text-blue-600 ml-4">✕</button>
          </div>
        )}

        {detailLoading ? (
          <div className="flex items-center justify-center h-64 text-slate-400 text-sm">Loading session...</div>
        ) : selected ? (
          <div className="max-w-2xl">
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div>
                <h1 className="text-xl font-semibold text-slate-800">{selected.patient_name}</h1>
                <p className="text-sm text-slate-500">{selected.doctor_name}</p>
                {selected.patient_phone && (
                  <p className="text-xs text-slate-400 mt-0.5">{selected.patient_phone}</p>
                )}
              </div>
              <div className="flex gap-2">
                {selected.held && (
                  <>
                    <button
                      onClick={() => reject(selected.id)}
                      disabled={actionLoading}
                      className="px-4 py-2 text-sm font-medium text-red-700 bg-red-50 border border-red-200 rounded-lg hover:bg-red-100 disabled:opacity-50"
                    >
                      Reject
                    </button>
                    <button
                      onClick={() => approve(selected.id)}
                      disabled={actionLoading}
                      className="px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50"
                    >
                      Approve & Send
                    </button>
                  </>
                )}
                {!selected.held && !selected.reviewer_action && (
                  <button
                    onClick={() => approve(selected.id)}
                    disabled={actionLoading}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    Re-send Sign Link
                  </button>
                )}
              </div>
            </div>

            {/* SLA timeline */}
            <div className="bg-white rounded-xl border border-slate-200 p-4 mb-4">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">SLA Timeline</p>
              <div className="grid grid-cols-3 gap-4 text-center">
                {[
                  { label: 'Received', ts: selected.received_at },
                  { label: 'Delivered', ts: selected.delivered_at },
                  { label: 'Signed', ts: selected.signed_at },
                ].map(({ label, ts }) => (
                  <div key={label}>
                    <p className="text-xs text-slate-500">{label}</p>
                    <p className="text-sm font-medium text-slate-800 mt-0.5">
                      {ts ? new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—'}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Diagnoses with ICD-10 */}
            {selected.diagnoses_annotated.length > 0 && (
              <div className="bg-white rounded-xl border border-slate-200 p-4 mb-4">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Diagnoses</p>
                <div className="space-y-2">
                  {selected.diagnoses_annotated.map((dx, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <span className="text-sm text-slate-800">{dx.name}</span>
                      {dx.icd10 ? (
                        <span className="font-mono text-xs text-slate-500 bg-slate-100 rounded px-2 py-0.5">{dx.icd10}</span>
                      ) : (
                        <span className="text-xs text-slate-300">no ICD-10</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Confidence scores */}
            {Object.keys(selected.confidence).length > 0 && (
              <div className="bg-white rounded-xl border border-slate-200 p-4 mb-4">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Extraction Confidence</p>
                <div className="space-y-2">
                  {Object.entries(selected.confidence).map(([key, score]) => (
                    <div key={key}>
                      <div className="flex justify-between mb-0.5">
                        <span className="text-xs text-slate-600 truncate max-w-xs">{key}</span>
                      </div>
                      <ConfidenceBar score={score} />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* SOAP */}
            {selected.soap && Object.keys(selected.soap).length > 0 && (
              <div className="bg-white rounded-xl border border-slate-200 p-4 mb-4">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">SOAP Note</p>
                {Object.entries(selected.soap).map(([k, v]) => v ? (
                  <div key={k} className="mb-3">
                    <p className="text-xs font-semibold text-slate-500 uppercase mb-1">{k}</p>
                    <p className="text-sm text-slate-800 whitespace-pre-wrap leading-relaxed">
                      {typeof v === 'string' ? v : JSON.stringify(v, null, 2)}
                    </p>
                  </div>
                ) : null)}
              </div>
            )}

            {/* Transcript */}
            {selected.transcript && (
              <div className="bg-white rounded-xl border border-slate-200 p-4 mb-4">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Transcript</p>
                <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">{selected.transcript}</p>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center h-64 text-slate-400 text-sm">
            Select a session from the queue
          </div>
        )}
      </div>
    </div>
  );
}
