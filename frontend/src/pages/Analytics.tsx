import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, Legend
} from 'recharts';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiPath } from '../lib/api';

interface AnalyticsData {
  overview: {
    total_sessions: number;
    sessions_this_week: number;
    completed_sessions: number;
    cloud_ai_sessions: number;
    edge_sessions: number;
  };
  top_symptoms: Array<{ name: string; count: number }>;
  top_medications: Array<{ name: string; count: number }>;
  top_allergies: Array<{ name: string; count: number }>;
  sessions_by_day: Array<{ date: string; consultations: number }>;
}

const CHART_COLORS = ['#1B5E3B', '#F4A435', '#C0392B', '#8B5CF6', '#10B981', '#3B82F6', '#EC4899', '#06B6D4'];

export default function Analytics() {
  const navigate = useNavigate();
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(apiPath('/analytics/dashboard'))
      .then((r) => r.json())
      .then(setData)
      .catch(() => setError('Failed to load analytics data. Ensure backend service is running.'))
      .finally(() => setLoading(false));
  }, []);

  const aiSplitData = data ? [
    { name: 'Optional Cloud Formatting Logged', value: data.overview.cloud_ai_sessions },
    { name: 'Local Clinical Processing', value: data.overview.edge_sessions },
  ] : [];

  return (
    <div className="min-h-screen bg-bg-warm font-sans text-text-dark pb-20">
      <header className="border-b border-slate-200/80 sticky top-0 bg-white/90 backdrop-blur-md z-10 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => navigate('/dashboard')} 
              className="text-slate-400 hover:text-primary transition-colors flex items-center text-xs font-semibold cursor-pointer"
            >
              <svg className="w-4 h-4 mr-1 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Dashboard
            </button>
            <div className="h-4 w-px bg-slate-200" />
            <div className="flex items-center gap-2">
              <span className="font-bold text-primary text-base">श</span>
              <span className="text-sm font-bold text-text-dark tracking-tight">Lipi</span>
            </div>
            <div className="h-4 w-px bg-slate-200" />
            <h1 className="text-sm font-bold text-text-dark">Clinical Ops Dashboard</h1>
          </div>
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Clinical AI Telemetry</span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        {/* Local Processing Banner */}
        <div className="rounded bg-primary/10 border border-primary/20 text-primary px-4 py-3 text-xs flex items-center gap-2.5 shadow-sm">
          <svg className="w-4.5 h-4.5 shrink-0 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <span className="font-semibold">Clinical extraction, documentation drafting, and CDS alerts run through the local Lipi engine for privacy-preserving clinic use.</span>
        </div>

        {loading && (
          <div className="flex items-center justify-center h-64">
            <p className="text-slate-400 text-sm animate-pulse font-medium">Loading telemetry metrics...</p>
          </div>
        )}
        {error && (
          <div className="rounded bg-red-50 text-alert-critical border border-red-100 px-4 py-3 text-sm">{error}</div>
        )}

        {data && (
          <>
            {/* Overview Cards */}
            <section>
              <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Clinical Ops Telemetry</h2>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {[
                  { label: 'Active Consultations', value: data.overview.total_sessions, color: 'text-text-dark border-l-4 border-l-primary' },
                  { label: 'Weekly Ingestions', value: data.overview.sessions_this_week, color: 'text-primary border-l-4 border-l-primary' },
                  { label: 'Completed Records', value: data.overview.completed_sessions, color: 'text-primary border-l-4 border-l-accent' },
                  { label: 'Optional Cloud Formatting', value: data.overview.cloud_ai_sessions, color: 'text-accent-dark border-l-4 border-l-purple-500' },
                ].map(({ label, value, color }) => (
                  <div key={label} className={`border border-slate-200 rounded p-4 bg-white shadow-sm ${color}`}>
                    <p className="text-[10px] uppercase font-bold text-slate-500 mb-1">{label}</p>
                    <p className="text-3xl font-bold font-mono">{value}</p>
                  </div>
                ))}
              </div>
            </section>

            {/* Sessions Over Time */}
            <section>
              <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Consultations Documented (Last 7 Days)</h2>
              <div className="border border-slate-200 rounded-lg p-6 bg-white shadow-sm">
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={data.sessions_by_day}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#94a3b8' }} />
                    <Tooltip 
                      formatter={(val) => [val, 'Consultations']}
                      contentStyle={{ fontSize: '11px', borderRadius: '4px', border: '1px solid #e2e8f0' }} 
                    />
                    <Line 
                      type="monotone" 
                      dataKey="consultations" 
                      name="Consultations Documented" 
                      stroke="#1B5E3B" 
                      strokeWidth={2.5} 
                      dot={{ r: 4, fill: '#1B5E3B' }} 
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </section>

            <div className="grid lg:grid-cols-2 gap-8">
              {/* Top Symptoms */}
              {data.top_symptoms.length > 0 && (
                <section>
                  <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Common Symptom Trends</h2>
                  <div className="border border-slate-200 rounded-lg p-6 bg-white shadow-sm">
                    <ResponsiveContainer width="100%" height={240}>
                      <BarChart data={data.top_symptoms} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                        <XAxis type="number" tick={{ fontSize: 11, fill: '#94a3b8' }} allowDecimals={false} />
                        <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 11, fill: '#334155' }} />
                        <Tooltip contentStyle={{ fontSize: '11px', borderRadius: '4px', border: '1px solid #e2e8f0' }} />
                        <Bar dataKey="count" fill="#1B5E3B" radius={[0, 4, 4, 0]}>
                          {data.top_symptoms.map((_, i) => (
                            <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </section>
              )}

              {/* Top Medications */}
              {data.top_medications.length > 0 && (
                <section>
                  <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Prescribed Medication Distributions</h2>
                  <div className="border border-slate-200 rounded-lg p-6 bg-white shadow-sm">
                    <ResponsiveContainer width="100%" height={240}>
                      <BarChart data={data.top_medications} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                        <XAxis type="number" tick={{ fontSize: 11, fill: '#94a3b8' }} allowDecimals={false} />
                        <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 11, fill: '#334155' }} />
                        <Tooltip contentStyle={{ fontSize: '11px', borderRadius: '4px', border: '1px solid #e2e8f0' }} />
                        <Bar dataKey="count" fill="#F4A435" radius={[0, 4, 4, 0]}>
                          {data.top_medications.map((_, i) => (
                            <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </section>
              )}
            </div>

              {/* Local privacy split */}
            <div className="grid lg:grid-cols-2 gap-8">
              <section>
                <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Local Processing Governance</h2>
                <div className="border border-slate-200 rounded-lg p-6 bg-white shadow-sm flex items-center justify-center">
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie 
                        data={aiSplitData} 
                        cx="50%" 
                        cy="50%" 
                        outerRadius={75} 
                        dataKey="value" 
                        label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`} 
                        labelLine={true}
                      >
                        {aiSplitData.map((_, i) => (
                          <Cell key={i} fill={i === 0 ? '#F4A435' : '#1B5E3B'} />
                        ))}
                      </Pie>
                      <Legend formatter={(value) => <span style={{ fontSize: '11px', color: '#1A1A1A', fontWeight: 600 }}>{value}</span>} />
                      <Tooltip contentStyle={{ fontSize: '11px', borderRadius: '4px', border: '1px solid #e2e8f0' }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </section>

              {/* Top Allergies */}
              {data.top_allergies.length > 0 && (
                <section>
                  <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Patient Reported Allergies</h2>
                  <div className="border border-slate-200 rounded-lg p-6 bg-white shadow-sm">
                    <div className="space-y-4">
                      {data.top_allergies.map(({ name, count }) => (
                        <div key={name} className="flex items-center justify-between">
                          <span className="text-xs font-semibold text-slate-700 capitalize">{name}</span>
                          <div className="flex items-center gap-3">
                            <div className="w-24 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-alert-critical rounded-full"
                                style={{ width: `${(count / (data.top_allergies[0]?.count || 1)) * 100}%` }}
                              />
                            </div>
                            <span className="text-xs font-bold text-slate-500 w-4 text-right font-mono">{count}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </section>
              )}
            </div>

            {data.overview.total_sessions === 0 && (
              <div className="text-center py-20 border border-dashed border-slate-200 rounded-lg bg-white shadow-sm">
                <p className="text-slate-500 text-sm font-medium">No clinical telemetry registered</p>
                <p className="text-slate-400 text-xs mt-1">Initiate consultation sessions to generate metadata insights.</p>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
