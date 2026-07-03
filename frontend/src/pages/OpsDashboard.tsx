import { useEffect, useState } from 'react';
import api from '../lib/api';

interface PeriodStats {
  total: number;
  signed: number;
  delivered: number;
}

interface OpsStats {
  hold_mode: boolean;
  today: PeriodStats;
  week: PeriodStats;
  month: PeriodStats;
  sla: {
    avg_seconds_24h: number | null;
    breach_count_24h: number;
    sample_count: number;
    target_seconds: number;
  };
  quality: {
    approved_this_week: number;
    rejected_this_week: number;
    approval_rate: number | null;
  };
  queue: {
    held: number;
  };
}

function fmtSecs(s: number | null) {
  if (s === null) return '—';
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return m > 0 ? `${m}m ${sec}s` : `${sec}s`;
}

function StatCard({ label, value, sub, accent }: { label: string; value: string | number; sub?: string; accent?: boolean }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 flex flex-col gap-1">
      <p className="text-xs text-slate-500">{label}</p>
      <p className={`text-2xl font-bold ${accent ? 'text-red-600' : 'text-slate-800'}`}>{value}</p>
      {sub && <p className="text-xs text-slate-400">{sub}</p>}
    </div>
  );
}

function PeriodBlock({ label, data }: { label: string; data: PeriodStats }) {
  const signedPct = data.total ? Math.round((data.signed / data.total) * 100) : 0;
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4">
      <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">{label}</p>
      <div className="grid grid-cols-3 gap-3 text-center">
        <div>
          <p className="text-lg font-bold text-slate-800">{data.total}</p>
          <p className="text-xs text-slate-500">notes</p>
        </div>
        <div>
          <p className="text-lg font-bold text-slate-800">{data.delivered}</p>
          <p className="text-xs text-slate-500">sent to dr</p>
        </div>
        <div>
          <p className={`text-lg font-bold ${signedPct > 80 ? 'text-emerald-700' : 'text-slate-800'}`}>{signedPct}%</p>
          <p className="text-xs text-slate-500">signed</p>
        </div>
      </div>
      {data.total > 0 && (
        <div className="mt-3 bg-slate-100 rounded-full h-1.5 overflow-hidden">
          <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${signedPct}%` }} />
        </div>
      )}
    </div>
  );
}

export default function OpsDashboard() {
  const [stats, setStats] = useState<OpsStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function load() {
    setLoading(true);
    setError('');
    try {
      const r = await api.get('/internal/ops-stats');
      setStats(r.data);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail || 'Failed to load stats');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-800">Ops Dashboard</h1>
          <p className="text-sm text-slate-500">WhatsApp pipeline metrics</p>
        </div>
        <div className="flex items-center gap-3">
          {stats && (
            <span className={`text-xs font-medium rounded-full px-2.5 py-1 border ${stats.hold_mode ? 'bg-amber-50 border-amber-200 text-amber-800' : 'bg-slate-50 border-slate-200 text-slate-500'}`}>
              {stats.hold_mode ? 'HOLD MODE' : 'Auto-send'}
            </span>
          )}
          <button onClick={load} className="text-sm text-blue-600 hover:underline">Refresh</button>
        </div>
      </div>

      {loading && <div className="text-slate-400 text-sm">Loading...</div>}
      {error && <div className="text-red-600 text-sm bg-red-50 rounded-xl px-4 py-3">{error}</div>}

      {stats && (
        <div className="space-y-4">
          {/* SLA */}
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">SLA (last 24h)</p>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className={`text-2xl font-bold ${stats.sla.avg_seconds_24h !== null && stats.sla.avg_seconds_24h > stats.sla.target_seconds ? 'text-red-600' : 'text-emerald-700'}`}>
                  {fmtSecs(stats.sla.avg_seconds_24h)}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">avg delivery</p>
                <p className="text-[10px] text-slate-400">target {fmtSecs(stats.sla.target_seconds)}</p>
              </div>
              <div>
                <p className={`text-2xl font-bold ${stats.sla.breach_count_24h > 0 ? 'text-amber-600' : 'text-emerald-700'}`}>
                  {stats.sla.breach_count_24h}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">SLA breaches</p>
                <p className="text-[10px] text-slate-400">&gt;5 min delivery</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-800">{stats.sla.sample_count}</p>
                <p className="text-xs text-slate-500 mt-0.5">sessions tracked</p>
              </div>
            </div>
          </div>

          {/* Periods */}
          <div className="grid grid-cols-3 gap-4">
            <PeriodBlock label="Today" data={stats.today} />
            <PeriodBlock label="This Week" data={stats.week} />
            <PeriodBlock label="This Month" data={stats.month} />
          </div>

          {/* Queue + Quality */}
          <div className="grid grid-cols-2 gap-4">
            <StatCard
              label="Notes held in queue"
              value={stats.queue.held}
              sub={stats.hold_mode ? 'Awaiting reviewer action' : 'Hold mode is off'}
              accent={stats.queue.held > 0 && stats.hold_mode}
            />
            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Quality (this week)</p>
              <div className="flex gap-4">
                <div className="text-center">
                  <p className="text-xl font-bold text-emerald-700">{stats.quality.approved_this_week}</p>
                  <p className="text-xs text-slate-500">approved</p>
                </div>
                <div className="text-center">
                  <p className="text-xl font-bold text-red-600">{stats.quality.rejected_this_week}</p>
                  <p className="text-xs text-slate-500">rejected</p>
                </div>
                <div className="text-center">
                  <p className="text-xl font-bold text-slate-800">
                    {stats.quality.approval_rate !== null ? `${Math.round(stats.quality.approval_rate * 100)}%` : '—'}
                  </p>
                  <p className="text-xs text-slate-500">approval rate</p>
                </div>
              </div>
            </div>
          </div>

          {/* Quick links */}
          <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 flex gap-4">
            <a href="/internal/review-queue" className="text-sm text-blue-600 hover:underline">→ Review Queue</a>
            <a href="/internal/invoices" className="text-sm text-blue-600 hover:underline">→ Invoice View</a>
          </div>
        </div>
      )}
    </div>
  );
}
