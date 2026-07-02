import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import client from '../lib/api';

// ── Types ────────────────────────────────────────────────────────────────────

interface TimelineVisit {
  session_id: string;
  date: string;
  doctor_name: string;
  specialty: string;
  symptoms: string[];
  medications: Array<{ name: string; dosage?: string; frequency?: string }>;
  vitals: string[];
  diagnoses: Array<{ text: string; code?: string; display?: string; system?: string }>;
  allergies: string[];
  investigations: string[];
  follow_up: string[];
  soap_summary: string;
}

interface PatientTimelineData {
  patient_name: string;
  total_visits: number;
  visits: TimelineVisit[];
  active_medications: Array<{ name: string; dosage?: string; frequency?: string; last_seen?: string }>;
  chronic_conditions: Array<{ text: string; code?: string; display?: string }>;
  allergies: string[];
}

async function getPatientTimeline(patientName: string): Promise<PatientTimelineData> {
  const res = await client.get<PatientTimelineData>(`/patients/${encodeURIComponent(patientName)}/timeline`);
  return res.data;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function IcdBadge({ code }: { code?: string }) {
  if (!code) return null;
  return (
    <span className="bg-blue-50 text-blue-700 text-[10px] font-mono px-1.5 py-0.5 rounded ml-1.5 whitespace-nowrap">
      {code}
    </span>
  );
}

function SpecialtyBadge({ specialty }: { specialty: string }) {
  if (!specialty) return null;
  return (
    <span className="bg-indigo-50 text-indigo-700 text-[10px] font-semibold px-2 py-0.5 rounded border border-indigo-100">
      {specialty.replace(/_/g, ' ')}
    </span>
  );
}

/** Parse BP readings from vitals strings across visits to show text trends */
function extractBpTrend(visits: TimelineVisit[]): Array<{ date: string; bp: string }> {
  const trend: Array<{ date: string; bp: string }> = [];
  for (const visit of visits) {
    for (const v of visit.vitals) {
      const match = v.match(/(?:BP|blood\s*pressure)[:\s]*(\d{2,3}\s*[/\\]\s*\d{2,3})/i);
      if (match) {
        const dateStr = new Date(visit.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
        trend.push({ date: dateStr, bp: match[1].replace(/\s/g, '') });
      }
    }
  }
  return trend.reverse(); // chronological order
}

// ── Component ────────────────────────────────────────────────────────────────

export default function PatientTimeline() {
  const navigate = useNavigate();
  const { patientName: urlPatientName } = useParams<{ patientName: string }>();
  const [searchInput, setSearchInput] = useState(urlPatientName ? decodeURIComponent(urlPatientName) : '');
  const [timeline, setTimeline] = useState<PatientTimelineData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedVisits, setExpandedVisits] = useState<Set<string>>(new Set());

  async function fetchTimeline(name: string) {
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    setTimeline(null);
    try {
      const data = await getPatientTimeline(name.trim());
      setTimeline(data);
    } catch (err: any) {
      const status = err?.response?.status;
      if (status === 404) {
        setError(`No records found for "${name.trim()}". Check the spelling or try a different name.`);
      } else {
        setError('Failed to load patient timeline. Is the backend running?');
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (urlPatientName) {
      fetchTimeline(decodeURIComponent(urlPatientName));
    }
  }, [urlPatientName]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!searchInput.trim()) return;
    // Update URL for bookmarkability
    navigate(`/patient/${encodeURIComponent(searchInput.trim())}`, { replace: true });
  }

  function toggleExpanded(sessionId: string) {
    setExpandedVisits((prev) => {
      const next = new Set(prev);
      if (next.has(sessionId)) next.delete(sessionId);
      else next.add(sessionId);
      return next;
    });
  }

  const bpTrend = timeline ? extractBpTrend(timeline.visits) : [];

  return (
    <div className="min-h-screen bg-bg-warm font-sans text-text-dark">
      {/* Header */}
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
            <div className="h-4 w-px bg-slate-200"></div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-primary text-base">श</span>
              <span className="text-sm font-bold text-text-dark tracking-tight">Lipi</span>
            </div>
            <div className="h-4 w-px bg-slate-200"></div>
            <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">Patient History</span>
          </div>
          <span className="bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider hidden sm:inline-block">
            Timeline View
          </span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Search bar */}
        <form onSubmit={handleSearch} className="mb-8">
          <div className="flex gap-3">
            <div className="relative flex-1">
              <svg className="w-4 h-4 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Enter patient name (e.g. Ramesh Kumar)"
                className="w-full pl-11 pr-4 py-3 text-sm border border-slate-200 rounded-lg outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 bg-white shadow-sm"
              />
            </div>
            <button
              type="submit"
              disabled={!searchInput.trim() || loading}
              className="bg-primary hover:bg-primary-dark disabled:opacity-50 text-white text-sm font-semibold px-6 py-3 rounded-lg transition-all shadow-sm flex items-center gap-2 cursor-pointer"
            >
              {loading ? (
                <>
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Searching...
                </>
              ) : (
                'Search'
              )}
            </button>
          </div>
        </form>

        {/* Error */}
        {error && (
          <div className="mb-6 rounded-lg bg-red-50 text-red-700 px-4 py-3 text-sm border border-red-100 shadow-sm">
            {error}
          </div>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div className="space-y-6">
            <div className="border border-slate-200 rounded-lg bg-white shadow-sm p-6 animate-pulse">
              <div className="h-6 bg-slate-200 rounded w-48 mb-4"></div>
              <div className="grid grid-cols-4 gap-4">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-16 bg-slate-100 rounded"></div>
                ))}
              </div>
            </div>
            {[1, 2, 3].map((i) => (
              <div key={i} className="border border-slate-200 rounded-lg bg-white shadow-sm p-6 animate-pulse">
                <div className="h-4 bg-slate-200 rounded w-32 mb-3"></div>
                <div className="h-3 bg-slate-100 rounded w-64 mb-2"></div>
                <div className="h-3 bg-slate-100 rounded w-48"></div>
              </div>
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && !timeline && !error && (
          <div className="text-center py-20 border border-slate-200 border-dashed rounded-lg bg-white shadow-sm">
            <svg className="w-12 h-12 text-slate-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm font-semibold text-slate-600">Search for a patient</p>
            <p className="text-xs text-slate-400 mt-1">Enter a patient name above to view their complete visit history.</p>
          </div>
        )}

        {/* Timeline content */}
        {timeline && (
          <div className="space-y-8">
            {/* Patient summary card */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="border border-slate-200 rounded-lg bg-white shadow-sm overflow-hidden"
            >
              <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-cyan-500 rounded-full flex items-center justify-center shadow-sm">
                    <span className="font-bold text-white text-sm">
                      {timeline.patient_name.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-slate-900">{timeline.patient_name}</h2>
                    <p className="text-xs text-slate-500">
                      {timeline.total_visits} visit{timeline.total_visits !== 1 ? 's' : ''} on record
                    </p>
                  </div>
                </div>
              </div>

              <div className="px-6 py-4 grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Total visits */}
                <div className="border border-slate-100 rounded-lg p-3 bg-slate-50/50">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Total Visits</p>
                  <p className="text-2xl font-bold text-primary">{timeline.total_visits}</p>
                </div>

                {/* Chronic conditions */}
                <div className="border border-slate-100 rounded-lg p-3 bg-slate-50/50">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Chronic Conditions</p>
                  {timeline.chronic_conditions.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5 mt-1">
                      {timeline.chronic_conditions.map((c, i) => (
                        <span key={i} className="text-xs text-slate-700">
                          {c.display || c.text}
                          <IcdBadge code={c.code} />
                          {i < timeline.chronic_conditions.length - 1 && ','}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400">None recorded</p>
                  )}
                </div>

                {/* Active medications */}
                <div className="border border-slate-100 rounded-lg p-3 bg-slate-50/50">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Active Medications</p>
                  {timeline.active_medications.length > 0 ? (
                    <div className="space-y-0.5 mt-1">
                      {timeline.active_medications.slice(0, 4).map((m, i) => (
                        <p key={i} className="text-xs text-slate-700 truncate">
                          {m.name}{m.dosage ? ` ${m.dosage}` : ''}{m.frequency ? ` ${m.frequency}` : ''}
                        </p>
                      ))}
                      {timeline.active_medications.length > 4 && (
                        <p className="text-[10px] text-slate-400 font-semibold">+{timeline.active_medications.length - 4} more</p>
                      )}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400">None recorded</p>
                  )}
                </div>

                {/* Allergies */}
                <div className="border border-slate-100 rounded-lg p-3 bg-slate-50/50">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Allergies</p>
                  {timeline.allergies.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5 mt-1">
                      {timeline.allergies.map((a, i) => (
                        <span key={i} className="bg-red-50 text-red-700 text-[11px] font-semibold px-2 py-0.5 rounded border border-red-100">
                          {a}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400">None recorded</p>
                  )}
                </div>
              </div>
            </motion.div>

            {/* BP Trend visualization */}
            {bpTrend.length >= 2 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.1 }}
                className="border border-slate-200 rounded-lg bg-white shadow-sm overflow-hidden"
              >
                <div className="px-6 py-3 bg-slate-50 border-b border-slate-200">
                  <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Blood Pressure Trend</h3>
                </div>
                <div className="px-6 py-4">
                  <div className="flex items-end gap-4 overflow-x-auto pb-2">
                    {bpTrend.map((reading, i) => {
                      const parts = reading.bp.split('/');
                      const systolic = parseInt(parts[0], 10);
                      const diastolic = parseInt(parts[1], 10);
                      const isElevated = systolic >= 140 || diastolic >= 90;
                      const isNormal = systolic < 120 && diastolic < 80;
                      return (
                        <div key={i} className="flex flex-col items-center min-w-[60px]">
                          <span className={`text-sm font-bold ${isElevated ? 'text-red-600' : isNormal ? 'text-emerald-600' : 'text-amber-600'}`}>
                            {reading.bp}
                          </span>
                          <div className={`w-2 rounded-full mt-1 ${isElevated ? 'bg-red-400' : isNormal ? 'bg-emerald-400' : 'bg-amber-400'}`}
                            style={{ height: `${Math.max(20, (systolic - 80) * 0.6)}px` }}
                          ></div>
                          <span className="text-[10px] text-slate-400 mt-1 whitespace-nowrap">{reading.date}</span>
                          {i < bpTrend.length - 1 && (
                            <span className="text-slate-300 text-xs mt-0.5">
                              {(() => {
                                const nextSystolic = parseInt(bpTrend[i + 1].bp.split('/')[0], 10);
                                if (nextSystolic > systolic) return '↗';
                                if (nextSystolic < systolic) return '↘';
                                return '→';
                              })()}
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                  <div className="flex gap-4 mt-3 text-[10px] text-slate-400">
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                      Normal (&lt;120/80)
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                      Elevated
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-red-400"></span>
                      High (&ge;140/90)
                    </span>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Visit timeline */}
            <div>
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">
                Visit Timeline ({timeline.visits.length})
              </h3>

              {timeline.visits.length === 0 && (
                <div className="text-center py-12 border border-slate-200 border-dashed rounded-lg bg-white shadow-sm">
                  <p className="text-sm text-slate-400">No visits recorded yet.</p>
                </div>
              )}

              <div className="relative">
                {/* Vertical line */}
                {timeline.visits.length > 1 && (
                  <div className="absolute left-[19px] top-6 bottom-6 w-px bg-slate-200"></div>
                )}

                <div className="space-y-4">
                  {timeline.visits.map((visit, i) => {
                    const isExpanded = expandedVisits.has(visit.session_id);
                    const visitDate = new Date(visit.date);
                    const dateStr = visitDate.toLocaleDateString('en-IN', {
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric',
                    });

                    return (
                      <motion.div
                        key={visit.session_id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.3, delay: i * 0.08 }}
                        className="flex gap-4"
                      >
                        {/* Timeline dot */}
                        <div className="flex flex-col items-center shrink-0 pt-5">
                          <div className={`w-[10px] h-[10px] rounded-full border-2 z-10 ${i === 0
                              ? 'border-primary bg-primary'
                              : 'border-slate-300 bg-white'
                            }`}></div>
                        </div>

                        {/* Visit card */}
                        <div className="flex-1 border border-slate-200 rounded-lg bg-white shadow-sm overflow-hidden">
                          {/* Card header */}
                          <div className="px-5 py-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between flex-wrap gap-2">
                            <div className="flex items-center gap-3">
                              <span className="text-sm font-bold text-slate-800">{dateStr}</span>
                              {visit.doctor_name && (
                                <>
                                  <div className="h-3 w-px bg-slate-200"></div>
                                  <span className="text-xs text-slate-500 font-medium">{visit.doctor_name}</span>
                                </>
                              )}
                              {visit.specialty && <SpecialtyBadge specialty={visit.specialty} />}
                            </div>
                            <button
                              onClick={() => navigate(`/consultation/${visit.session_id}`)}
                              className="text-[10px] text-primary hover:text-primary-dark font-semibold flex items-center gap-1 cursor-pointer"
                            >
                              Open session
                              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
                              </svg>
                            </button>
                          </div>

                          {/* Card body */}
                          <div className="px-5 py-4 space-y-3">
                            {/* Symptoms */}
                            {visit.symptoms.length > 0 && (
                              <div>
                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Symptoms</p>
                                <div className="flex flex-wrap gap-1.5">
                                  {visit.symptoms.map((s, j) => (
                                    <span key={j} className="bg-amber-50 text-amber-800 text-[11px] font-medium px-2 py-0.5 rounded border border-amber-100">
                                      {s}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Vitals */}
                            {visit.vitals.length > 0 && (
                              <div>
                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Vitals</p>
                                <div className="flex flex-wrap gap-1.5">
                                  {visit.vitals.map((v, j) => (
                                    <span key={j} className="bg-slate-50 text-slate-700 text-[11px] font-medium px-2 py-0.5 rounded border border-slate-200">
                                      {v}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Diagnoses */}
                            {visit.diagnoses.length > 0 && (
                              <div>
                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Diagnoses</p>
                                <div className="flex flex-wrap gap-1.5">
                                  {visit.diagnoses.map((d, j) => (
                                    <span key={j} className="text-xs text-slate-700">
                                      {d.display || d.text}
                                      <IcdBadge code={d.code} />
                                      {j < visit.diagnoses.length - 1 && (
                                        <span className="text-slate-300 ml-1">/</span>
                                      )}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Medications */}
                            {visit.medications.length > 0 && (
                              <div>
                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Medications</p>
                                <div className="space-y-0.5">
                                  {visit.medications.map((m, j) => (
                                    <p key={j} className="text-xs text-slate-600">
                                      <span className="font-semibold text-slate-800">{m.name}</span>
                                      {m.dosage && <span className="text-slate-500"> {m.dosage}</span>}
                                      {m.frequency && <span className="text-slate-400"> {m.frequency}</span>}
                                    </p>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Investigations */}
                            {visit.investigations.length > 0 && (
                              <div>
                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Investigations</p>
                                <div className="flex flex-wrap gap-1.5">
                                  {visit.investigations.map((inv, j) => (
                                    <span key={j} className="bg-cyan-50 text-cyan-700 text-[11px] font-medium px-2 py-0.5 rounded border border-cyan-100">
                                      {inv}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* SOAP summary */}
                            {visit.soap_summary && (
                              <div>
                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">SOAP Summary</p>
                                <p className={`text-xs text-slate-600 leading-relaxed ${!isExpanded ? 'line-clamp-3' : ''}`}>
                                  {visit.soap_summary}
                                </p>
                                {visit.soap_summary.length > 200 && (
                                  <button
                                    onClick={() => toggleExpanded(visit.session_id)}
                                    className="text-[10px] text-primary hover:text-primary-dark font-semibold mt-1 cursor-pointer"
                                  >
                                    {isExpanded ? 'Show less' : 'Show more'}
                                  </button>
                                )}
                              </div>
                            )}

                            {/* Follow-up */}
                            {visit.follow_up.length > 0 && (
                              <div className="border-t border-slate-100 pt-3">
                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Follow-up</p>
                                <div className="space-y-0.5">
                                  {visit.follow_up.map((f, j) => (
                                    <p key={j} className="text-xs text-slate-600 flex items-start gap-1.5">
                                      <svg className="w-3 h-3 text-primary mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                      </svg>
                                      {f}
                                    </p>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Allergies (if specific to this visit) */}
                            {visit.allergies.length > 0 && (
                              <div>
                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Allergies Noted</p>
                                <div className="flex flex-wrap gap-1.5">
                                  {visit.allergies.map((a, j) => (
                                    <span key={j} className="bg-red-50 text-red-700 text-[11px] font-semibold px-2 py-0.5 rounded border border-red-100">
                                      {a}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
