import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { listSessions } from '../lib/api';
import type { ConsultationSession } from '../types/clinical';
import { MODE_COLORS } from '../types/clinical';

function initialsOf(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '?';
  return (parts[0][0] + (parts.length > 1 ? parts[parts.length - 1][0] : '')).toUpperCase();
}

function diagnosisOf(s: ConsultationSession): string | null {
  const soap = s.soap_note as any;
  return soap?.A?.match(/:\s*([^;.\n]+)/)?.[1]?.trim() || soap?.A?.split('.')[0]?.trim() || null;
}

function factsOf(s: ConsultationSession) {
  const soap = s.soap_note as any;
  const facts = s.clinical_facts as any;
  const d = facts && !Array.isArray(facts) ? facts : {};
  return {
    symptoms: (d.symptoms ?? soap?.S?.split(/[,;]/).map((x: string) => x.trim()).filter(Boolean) ?? []) as string[],
    medications: (d.medications ?? []) as { name: string; dosage?: string }[],
    vitals: (d.vitals ?? []) as string[],
    allergies: (d.allergies ?? []) as string[],
    investigations: (d.investigations ?? []) as string[],
  };
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

function RedFlagBadge({ text }: { text: string }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-red-50 text-red-700 border border-red-100">
      <span className="w-1.5 h-1.5 rounded-full bg-red-500 shrink-0" />
      {text}
    </span>
  );
}

export default function PatientProfile() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const [allSessions, setAllSessions] = useState<ConsultationSession[]>([]);
  const [loading, setLoading] = useState(true);

  const decodedName = decodeURIComponent(name ?? '');

  useEffect(() => {
    listSessions()
      .then(setAllSessions)
      .finally(() => setLoading(false));
  }, []);

  const sessions = useMemo(
    () =>
      allSessions
        .filter(s => (s.patient_name ?? '').toLowerCase() === decodedName.toLowerCase())
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()),
    [allSessions, decodedName]
  );

  // Aggregate across all sessions
  const profile = useMemo(() => {
    const diagnosisCount: Record<string, number> = {};
    const medCount: Record<string, number> = {};
    const allergySet = new Set<string>();
    const vitalsList: { date: string; values: string[] }[] = [];
    const investigationSet = new Set<string>();
    const symptomCount: Record<string, number> = {};

    for (const s of sessions) {
      const f = factsOf(s);
      const diag = diagnosisOf(s);
      if (diag) diagnosisCount[diag] = (diagnosisCount[diag] ?? 0) + 1;
      f.medications.forEach(m => { medCount[m.name] = (medCount[m.name] ?? 0) + 1; });
      f.allergies.forEach(a => allergySet.add(a));
      if (f.vitals.length) vitalsList.push({ date: formatDate(s.created_at), values: f.vitals });
      f.investigations.forEach(i => investigationSet.add(i));
      f.symptoms.forEach(sym => { symptomCount[sym] = (symptomCount[sym] ?? 0) + 1; });
    }

    const topDiagnoses = Object.entries(diagnosisCount).sort((a, b) => b[1] - a[1]).slice(0, 5);
    const recurringMeds = Object.entries(medCount).filter(([, c]) => c > 1).sort((a, b) => b[1] - a[1]);
    const allMeds = Object.entries(medCount).sort((a, b) => b[1] - a[1]);
    const recurringSymptoms = Object.entries(symptomCount).filter(([, c]) => c >= 2).sort((a, b) => b[1] - a[1]);

    return {
      topDiagnoses,
      recurringMeds,
      allMeds,
      allergies: Array.from(allergySet),
      vitalsList: vitalsList.slice(0, 5),
      investigations: Array.from(investigationSet),
      recurringSymptoms,
    };
  }, [sessions]);

  const lastSeen = sessions[0] ? formatDate(sessions[0].created_at) : null;
  const firstSeen = sessions[sessions.length - 1] ? formatDate(sessions[sessions.length - 1].created_at) : null;

  return (
    <div className="min-h-screen bg-bg-warm font-sans text-text-dark">
      {/* Header */}
      <header className="border-b border-slate-200/80 sticky top-0 bg-white/90 backdrop-blur-md z-20 h-14 flex items-center gap-4 px-6">
        <button
          onClick={() => navigate('/dashboard')}
          className="flex items-center gap-1.5 text-slate-400 hover:text-primary transition-colors text-[13px] font-medium cursor-pointer"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Dashboard
        </button>
        <div className="h-5 w-px bg-slate-200" />
        <button onClick={() => navigate('/')} className="flex items-center gap-2 group cursor-pointer">
          <span className="grid place-items-center w-7 h-7 rounded-lg bg-primary/10 text-primary font-bold text-sm">श</span>
          <span className="text-[15px] font-bold tracking-tight text-text-dark hidden sm:inline">Lipi</span>
        </button>
        <div className="h-5 w-px bg-slate-200" />
        <h1 className="text-[15px] font-semibold text-text-dark truncate">{decodedName || 'Patient Profile'}</h1>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map(i => <div key={i} className="h-24 bg-white rounded-2xl border border-slate-200 animate-pulse" />)}
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-slate-500 text-sm">No sessions found for <strong>{decodedName}</strong>.</p>
            <button onClick={() => navigate('/dashboard')} className="mt-4 text-primary text-sm underline cursor-pointer">Back to dashboard</button>
          </div>
        ) : (
          <>
            {/* Patient hero card */}
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm mb-6 flex flex-wrap gap-6 items-center">
              <div className="grid place-items-center w-16 h-16 rounded-2xl bg-primary/10 text-primary font-bold text-2xl shrink-0">
                {initialsOf(decodedName)}
              </div>
              <div className="flex-1 min-w-0">
                <h2 className="text-xl font-bold text-text-dark">{decodedName}</h2>
                <p className="text-[13px] text-slate-500 mt-0.5">
                  {sessions.length} visit{sessions.length !== 1 ? 's' : ''} &nbsp;·&nbsp; First seen {firstSeen} &nbsp;·&nbsp; Last seen {lastSeen}
                </p>
              </div>
              {profile.allergies.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {profile.allergies.map(a => <RedFlagBadge key={a} text={`Allergy: ${a}`} />)}
                </div>
              )}
            </div>

            <div className="grid md:grid-cols-2 gap-5 mb-6">
              {/* Diagnoses */}
              {profile.topDiagnoses.length > 0 && (
                <Section title="Diagnosis history" icon={diagnosisIcon}>
                  <ul className="space-y-2">
                    {profile.topDiagnoses.map(([diag, count]) => (
                      <li key={diag} className="flex items-center justify-between gap-3">
                        <span className="text-[13px] text-slate-700 leading-snug">{diag}</span>
                        {count > 1 && (
                          <span className="shrink-0 text-[11px] font-semibold text-amber-700 bg-amber-50 border border-amber-200/70 px-2 py-0.5 rounded-full">×{count}</span>
                        )}
                      </li>
                    ))}
                  </ul>
                </Section>
              )}

              {/* Medications */}
              {profile.allMeds.length > 0 && (
                <Section title="Medications prescribed" icon={medIcon}>
                  <ul className="space-y-2">
                    {profile.allMeds.map(([med, count]) => (
                      <li key={med} className="flex items-center justify-between gap-3">
                        <span className="text-[13px] text-slate-700">{med}</span>
                        <div className="flex items-center gap-1.5 shrink-0">
                          {count > 1 && (
                            <span className="text-[11px] font-semibold text-primary bg-primary/8 border border-primary/15 px-2 py-0.5 rounded-full">×{count}</span>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </Section>
              )}

              {/* Recurring symptoms (watch out for) */}
              {profile.recurringSymptoms.length > 0 && (
                <Section title="Watch out for — recurring symptoms" icon={warnIcon} accent>
                  <ul className="space-y-1.5">
                    {profile.recurringSymptoms.map(([sym, count]) => (
                      <li key={sym} className="flex items-center justify-between gap-3">
                        <span className="text-[13px] text-slate-700">{sym}</span>
                        <span className="text-[11px] font-semibold text-red-700 bg-red-50 border border-red-100 px-2 py-0.5 rounded-full shrink-0">×{count} visits</span>
                      </li>
                    ))}
                  </ul>
                </Section>
              )}

              {/* Investigations */}
              {profile.investigations.length > 0 && (
                <Section title="Investigations ordered" icon={labIcon}>
                  <div className="flex flex-wrap gap-1.5">
                    {profile.investigations.map(inv => (
                      <span key={inv} className="text-[12px] bg-slate-100 text-slate-600 border border-slate-200 px-2.5 py-1 rounded-lg">{inv}</span>
                    ))}
                  </div>
                </Section>
              )}

              {/* Vitals trend */}
              {profile.vitalsList.length > 0 && (
                <Section title="Vitals across visits" icon={vitalsIcon} className="md:col-span-2">
                  <div className="space-y-2">
                    {profile.vitalsList.map((v, i) => (
                      <div key={i} className="flex items-start gap-3 text-[13px]">
                        <span className="text-slate-400 shrink-0 w-28">{v.date}</span>
                        <span className="text-slate-700">{v.values.join(' · ')}</span>
                      </div>
                    ))}
                  </div>
                </Section>
              )}
            </div>

            {/* Visit timeline */}
            <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-100 flex items-center gap-2">
                {clockIcon}
                <h3 className="text-[13px] font-semibold text-text-dark">Visit timeline</h3>
                <span className="ml-auto text-[12px] text-slate-400">{sessions.length} visit{sessions.length !== 1 ? 's' : ''}</span>
              </div>
              <ul className="divide-y divide-slate-100">
                {sessions.map(s => {
                  const diag = diagnosisOf(s);
                  return (
                    <li
                      key={s.id}
                      onClick={() => navigate(`/consultation/${s.id}`)}
                      className="px-6 py-4 flex items-center gap-4 hover:bg-slate-50 cursor-pointer transition-colors group"
                    >
                      <div className="flex flex-col items-center gap-1 shrink-0 w-24">
                        <span className="text-[12px] font-medium text-slate-500">{formatDate(s.created_at)}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-[13px] font-medium text-text-dark truncate">{diag ?? 'Consultation'}</p>
                        {s.doctor_name && <p className="text-[11px] text-slate-400 mt-0.5">{s.doctor_name}</p>}
                      </div>
                      <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-md border ${MODE_COLORS[s.mode ?? 'health']}`}>
                        {(s.mode ?? 'health').toUpperCase()}
                      </span>
                      <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-md border capitalize ${s.status === 'complete' ? 'bg-primary/10 text-primary border-primary/20' : 'bg-slate-100 text-slate-600 border-slate-200'}`}>
                        {s.status.replace(/_/g, ' ')}
                      </span>
                      <svg className="w-4 h-4 text-slate-300 group-hover:text-primary transition-colors shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </li>
                  );
                })}
              </ul>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

function Section({ title, icon, children, accent, className }: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  accent?: boolean;
  className?: string;
}) {
  return (
    <div className={`bg-white border ${accent ? 'border-red-100' : 'border-slate-200'} rounded-2xl shadow-sm overflow-hidden ${className ?? ''}`}>
      <div className={`px-5 py-3.5 border-b ${accent ? 'border-red-100 bg-red-50/40' : 'border-slate-100'} flex items-center gap-2`}>
        {icon}
        <h3 className={`text-[13px] font-semibold ${accent ? 'text-red-800' : 'text-text-dark'}`}>{title}</h3>
      </div>
      <div className="px-5 py-4">{children}</div>
    </div>
  );
}

const diagnosisIcon = (
  <svg className="w-4 h-4 text-primary shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
  </svg>
);
const medIcon = (
  <svg className="w-4 h-4 text-primary shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
  </svg>
);
const warnIcon = (
  <svg className="w-4 h-4 text-red-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
  </svg>
);
const labIcon = (
  <svg className="w-4 h-4 text-primary shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
  </svg>
);
const vitalsIcon = (
  <svg className="w-4 h-4 text-primary shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
  </svg>
);
const clockIcon = (
  <svg className="w-4 h-4 text-slate-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);
