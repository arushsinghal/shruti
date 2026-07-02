import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createSession, listSessions, getClinicInviteCode, getRevenueSummary } from '../lib/api';
import api from '../lib/api';
import type { RevenueSummary } from '../lib/api';
import type { ConsultationSession, SessionMode } from '../types/clinical';
import { MODE_COLORS } from '../types/clinical';
import OnboardingFlow from '../components/OnboardingFlow';
import ProfileModal from '../components/ProfileModal';
import { motion, useReducedMotion } from 'framer-motion';
import SupportModal from '../components/SupportModal';

function diagnosisOf(s: ConsultationSession): string | null {
  const soap = s.soap_note as any;
  const facts = s.clinical_facts as any;
  return (
    soap?.A?.match(/:\s*([^;.]+)/)?.[1]?.trim() ||
    (Array.isArray(facts) ? null : facts?.diagnoses?.[0]) ||
    null
  );
}

function initialsOf(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '•';
  const first = parts[0][0] ?? '';
  const last = parts.length > 1 ? parts[parts.length - 1][0] : '';
  return (first + last).toUpperCase();
}

// Pipeline status → brand-aligned semantic scale: neutral (start) → saffron (working) → green (done).
const STATUS_COLORS: Record<string, string> = {
  created: 'bg-slate-100 text-slate-600 border border-slate-200',
  audio_uploaded: 'bg-amber-50 text-amber-700 border border-amber-200/70',
  transcribed: 'bg-amber-50 text-amber-700 border border-amber-200/70',
  extracted: 'bg-amber-50 text-amber-700 border border-amber-200/70',
  memory_resolved: 'bg-amber-50 text-amber-700 border border-amber-200/70',
  soap_ready: 'bg-amber-100 text-amber-800 border border-amber-300/60',
  complete: 'bg-primary/10 text-primary border border-primary/20',
};

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] ?? 'bg-slate-100 text-slate-600 border border-slate-200';
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium capitalize ${color}`}>
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
  government: 'Special workflow',
  legal:      'Special workflow',
  general:    'Any audio → Transcript + summary',
};

const AVAILABLE_MODES: SessionMode[] = ['health', 'general'];

export default function Dashboard() {
  const navigate = useNavigate();
  const reduce = useReducedMotion();
  const [sessions, setSessions] = useState<ConsultationSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showModeModal, setShowModeModal] = useState(false);
  const [selectedMode, setSelectedMode] = useState<SessionMode>('health');
  const [showSupportModal, setShowSupportModal] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [profileComplete, setProfileComplete] = useState(true);
  const [search, setSearch] = useState('');
  const [sessionPatientName, setSessionPatientName] = useState('');
  const [sessionDoctorName, setSessionDoctorName] = useState('');
  const [sessionPatientPhone, setSessionPatientPhone] = useState('');
  const [inviteCode, setInviteCode] = useState<string | null>(null);
  const [inviteCopied, setInviteCopied] = useState(false);
  const [timelinePatient, setTimelinePatient] = useState<string | null>(null);
  const [revenue, setRevenue] = useState<RevenueSummary | null>(null);
  const [learningStats, setLearningStats] = useState<{total_learned: number; accuracy_pct: number; promoted_to_global: number} | null>(null);
  const [billing, setBilling] = useState<{plan: string; sessions_left: number | null; trial_sessions_used: number; trial_limit: number; can_create_session: boolean; razorpay_page_id: string; price_rupees: number} | null>(null);
  const [showPaywall, setShowPaywall] = useState(false);

  useEffect(() => {
    listSessions()
      .then(setSessions)
      .catch(() => setError('Failed to load consultations'))
      .finally(() => setLoading(false));

    api.get('/auth/doctor-profile').then(r => {
      setProfileComplete(!!r.data?.name);
    }).catch(() => setProfileComplete(false));

    getClinicInviteCode().then(r => setInviteCode(r.code)).catch(() => {});
    getRevenueSummary().then(setRevenue).catch(() => {});
    api.get('/learning/stats').then(r => setLearningStats(r.data)).catch(() => {});
    api.get('/billing/status').then(r => setBilling(r.data)).catch(() => {});
  }, []);

  const stats = useMemo(() => {
    const today = new Date().toDateString();
    const completed = sessions.filter((s) => s.status === 'complete').length;
    const todayCount = sessions.filter((s) => new Date(s.created_at).toDateString() === today).length;
    return {
      total: sessions.length,
      completed,
      inProgress: sessions.length - completed,
      today: todayCount,
    };
  }, [sessions]);

  function handleExportOpdRegister() {
    const today = new Date().toLocaleDateString('en-IN', { day: '2-digit', month: '2-digit', year: 'numeric' });
    const header = ['Date', 'Patient Name', 'Doctor', 'Mode', 'Diagnosis', 'Status', 'ABHA No', 'PMJAY'];
    const rows = sessions.map(s => {
      const soap = s.soap_note as any;
      const diagnosis = soap?.A?.match(/:\s*([^;.]+)/)?.[1]?.trim() || soap?.A?.split('.')[0]?.trim() || '';
      const date = new Date(s.created_at).toLocaleDateString('en-IN');
      return [
        date,
        s.patient_name || '',
        s.doctor_name || '',
        s.mode || 'health',
        diagnosis,
        s.status,
        s.abha_number || '',
        s.pmjay_beneficiary ? 'Yes' : 'No',
      ].map(v => `"${String(v).replace(/"/g, '""')}"`).join(',');
    });
    const csv = [header.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `OPD_Register_${today.replace(/\//g, '-')}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function handleNewConsultation() {
    // Check billing before opening the mode modal
    if (billing && !billing.can_create_session) {
      setShowModeModal(false);
      setShowPaywall(true);
      return;
    }
    setCreating(true);
    setShowModeModal(false);
    setError(null);
    try {
      const session = await createSession({
        cloud_ai_consent: false,
        mode: selectedMode,
        patient_name: sessionPatientName.trim() || undefined,
        doctor_name: sessionDoctorName.trim() || undefined,
        patient_phone: sessionPatientPhone.trim() || undefined,
      });
      // Refresh billing counter after creating session
      api.get('/billing/status').then(r => setBilling(r.data)).catch(() => {});
      navigate(`/consultation/${session.id}`);
    } catch (err: any) {
      if (err?.response?.status === 402) {
        setShowPaywall(true);
        setBilling(b => b ? { ...b, can_create_session: false } : b);
      } else {
        setError('Failed to initialize a new session. Is the backend service running?');
      }
      setCreating(false);
    }
  }

  const q = search.toLowerCase().trim();
  const filteredSessions = q
    ? sessions.filter(s =>
        (s.patient_name || '').toLowerCase().includes(q) ||
        (s.doctor_name || '').toLowerCase().includes(q) ||
        (s.mode || '').toLowerCase().includes(q)
      )
    : sessions;

  // Unique patients matching the search query (only when searching by name)
  const matchedPatients = useMemo(() => {
    if (!q) return [];
    const map = new Map<string, number>();
    for (const s of sessions) {
      const pn = s.patient_name?.trim();
      if (pn && pn.toLowerCase().includes(q)) {
        map.set(pn, (map.get(pn) ?? 0) + 1);
      }
    }
    return Array.from(map.entries()).sort((a, b) => b[1] - a[1]);
  }, [sessions, q]);

  const navLinkCls = 'px-3 py-1.5 rounded-lg text-[13px] font-medium text-slate-500 hover:text-primary hover:bg-primary/5 transition-colors cursor-pointer';
  const [showExportMenu, setShowExportMenu] = useState(false);

  const trialPct = billing ? Math.min(100, (billing.trial_sessions_used / billing.trial_limit) * 100) : 0;

  return (
    <div className="min-h-screen bg-bg-warm font-sans text-text-dark">
      <OnboardingFlow />
      <SupportModal isOpen={showSupportModal} onClose={() => setShowSupportModal(false)} />
      <ProfileModal
        isOpen={showProfileModal}
        onClose={() => setShowProfileModal(false)}
        onSaved={() => setProfileComplete(true)}
      />

      {/* ── Paywall modal ── */}
      {showPaywall && billing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-sm mx-4 p-7">
            <div className="text-center mb-5">
              <div className="w-14 h-14 rounded-full bg-amber-50 flex items-center justify-center mx-auto mb-4">
                <svg className="w-7 h-7 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-slate-900">Trial complete</h3>
              <p className="text-slate-500 text-sm mt-1.5">
                You've used all {billing.trial_limit} free sessions. Upgrade to continue.
              </p>
            </div>
            <div className="bg-slate-50 rounded-xl p-4 mb-5 space-y-2 text-sm">
              {['Unlimited sessions', 'All document types (Rx, Referral, TPA)', 'WhatsApp intake', 'AI learning engine'].map(f => (
                <div key={f} className="flex items-center gap-2 text-slate-700">
                  <svg className="w-4 h-4 text-emerald-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                  {f}
                </div>
              ))}
            </div>
            <button
              onClick={() => {
                const user = JSON.parse(localStorage.getItem('user') || '{}');
                const base = `https://pages.razorpay.com/${billing.razorpay_page_id}`;
                const params = new URLSearchParams();
                if (user.email) params.set('prefill[email]', user.email);
                if (user.name) params.set('prefill[name]', user.name);
                window.open(`${base}?${params}`, '_blank');
              }}
              className="w-full bg-primary hover:bg-primary-dark text-white font-bold py-3.5 rounded-xl transition-all active:scale-[0.98] text-[15px]"
            >
              Upgrade for ₹{billing.price_rupees}/month
            </button>
            <button onClick={() => setShowPaywall(false)} className="w-full mt-2 text-slate-400 text-sm py-2 hover:text-slate-600 transition-colors">
              Maybe later
            </button>
          </div>
        </div>
      )}

      {/* ── Header ───────────────────────────────────────────── */}
      <header className="border-b border-slate-200/80 sticky top-0 bg-white/85 backdrop-blur-md z-20">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-5">
            <button onClick={() => navigate('/')} className="flex items-center gap-2.5 group cursor-pointer">
              <span className="grid place-items-center w-8 h-8 rounded-xl bg-primary/10 text-primary font-bold text-base group-hover:bg-primary/15 transition-colors">श</span>
              <span className="text-[15px] font-bold tracking-tight text-text-dark">Lipi</span>
            </button>
            <div className="h-5 w-px bg-slate-200 hidden md:block" />
            <nav className="hidden md:flex items-center gap-0.5">
              <button onClick={() => navigate('/analytics')} className={navLinkCls}>Overview</button>
              <button onClick={() => navigate('/appointments')} className={navLinkCls}>Appointments</button>
              <button onClick={() => navigate('/about')} className={navLinkCls}>Methodology</button>
              <button onClick={() => navigate('/internal/review-queue')} className={navLinkCls}>Review Queue</button>
              <button onClick={() => navigate('/internal/ops')} className={navLinkCls}>Ops</button>
              <button onClick={() => navigate('/internal/invoices')} className={navLinkCls}>Invoices</button>
              <button onClick={() => navigate('/clinic-inbox')} className={`${navLinkCls} flex items-center gap-1`}>
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                WA Inbox
              </button>
              <button onClick={() => navigate('/billing')} className={`${navLinkCls} flex items-center gap-1`}>
                {billing && billing.plan === 'trial' && (
                  <span className="w-2 h-2 rounded-full bg-amber-400 flex-shrink-0" />
                )}
                {billing?.plan === 'paid' ? 'Pro' : 'Upgrade'}
              </button>
              <button onClick={() => setShowSupportModal(true)} className={navLinkCls}>Help</button>
            </nav>
          </div>

          <div className="flex items-center gap-2.5">
            <span className="hidden lg:inline-flex items-center text-[11px] font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full">
              Workspace
            </span>
            <button
              onClick={() => setShowProfileModal(true)}
              title="Doctor profile"
              className="relative grid place-items-center w-9 h-9 rounded-lg border border-slate-200 hover:border-primary/30 hover:bg-slate-50 text-slate-500 hover:text-primary transition-all cursor-pointer"
            >
              <svg className="w-4.5 h-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
              </svg>
              {!profileComplete && (
                <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-amber-400 border-2 border-white" />
              )}
            </button>
            <div className="relative hidden sm:block">
              <button
                onClick={() => setShowExportMenu(v => !v)}
                disabled={sessions.length === 0}
                title="Download today's OPD register"
                className="text-[13px] font-medium text-slate-600 hover:text-primary border border-slate-200 hover:border-primary/30 bg-white px-3 py-2 rounded-lg transition-all disabled:opacity-40 disabled:hover:text-slate-600 disabled:hover:border-slate-200 inline-flex items-center gap-1.5 cursor-pointer"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                OPD Register
                <svg className="w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {showExportMenu && (
                <>
                  <div className="fixed inset-0 z-20" onClick={() => setShowExportMenu(false)} />
                  <div className="absolute right-0 mt-1.5 w-44 bg-white border border-slate-200 rounded-lg shadow-lg z-30 py-1">
                    <button
                      onClick={() => { setShowExportMenu(false); handleExportOpdRegister(); }}
                      title="Download OPD register as a spreadsheet"
                      className="w-full text-left px-3 py-2 text-[13px] font-medium text-slate-600 hover:bg-slate-50 hover:text-primary transition-colors cursor-pointer"
                    >
                      Export as CSV
                    </button>
                    <button
                      onClick={async () => {
                        setShowExportMenu(false);
                        try {
                          const today = new Date().toISOString().slice(0, 10);
                          const resp = await api.get(`/clinic/opd-register?date=${today}`, { responseType: 'blob' });
                          const url = URL.createObjectURL(new Blob([resp.data], { type: 'application/pdf' }));
                          const a = document.createElement('a');
                          a.href = url; a.download = `OPD-Register-${today}.pdf`; a.click();
                          URL.revokeObjectURL(url);
                        } catch { alert('Could not generate OPD Register PDF.'); }
                      }}
                      title="Download today's OPD register as an MCI-format PDF"
                      className="w-full text-left px-3 py-2 text-[13px] font-medium text-slate-600 hover:bg-slate-50 hover:text-violet-700 transition-colors cursor-pointer"
                    >
                      Export as PDF
                    </button>
                  </div>
                </>
              )}
            </div>
            <button
              onClick={() => setShowModeModal(true)}
              disabled={creating}
              className="bg-primary hover:bg-primary-dark disabled:opacity-50 text-white text-[13px] font-semibold px-4 py-2 rounded-lg transition-all shadow-sm active:scale-[0.98] flex items-center gap-1.5 cursor-pointer"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              {creating ? 'Initializing…' : 'New session'}
            </button>
          </div>
        </div>
      </header>

      {/* ── Compliance strip ─────────────────────────────────── */}
      <div className="border-b border-slate-200/70 bg-primary/[0.04]">
        <div className="max-w-7xl mx-auto px-6 py-2 flex items-center gap-2 text-[11.5px] leading-snug text-primary/90">
          <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <p>
            Audio is transcribed on-shore by an India-based speech recognition service. Transcript identifiers are scrubbed before storage. Raw audio is deleted after successful transcription; incomplete sessions may be retained up to 48 hours.
          </p>
        </div>
      </div>

      {/* ── Profile incomplete banner ────────────────────────── */}
      {!profileComplete && (
        <div className="bg-amber-50 border-b border-amber-200/70">
          <div className="max-w-7xl mx-auto px-6 py-2.5 flex items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-[13px] text-amber-800">
              <svg className="w-4 h-4 shrink-0 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              </svg>
              <span>Complete your profile to enable prescription headers and lab order letterheads.</span>
            </div>
            <button
              onClick={() => setShowProfileModal(true)}
              className="shrink-0 text-[12px] font-semibold text-amber-800 bg-amber-100 hover:bg-amber-200 border border-amber-300/60 px-3 py-1.5 rounded-lg transition-all cursor-pointer"
            >
              Set up now →
            </button>
          </div>
        </div>
      )}

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* ── Title ──────────────────────────────────────────── */}
        <div className="mb-7">
          <h1 className="text-2xl font-bold tracking-tight text-text-dark">Consultations</h1>
          <p className="text-sm text-slate-500 mt-1">Every session transcribed locally, evidence-checked, and ready for your review.</p>
        </div>

        {/* ── Stats ──────────────────────────────────────────── */}
        <motion.div
          initial={reduce ? false : { opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
          className="grid grid-cols-2 md:grid-cols-4 rounded-2xl border border-slate-200/70 bg-white shadow-sm overflow-hidden divide-x divide-y md:divide-y-0 divide-slate-100 mb-8"
        >
          {[
            { label: 'Total sessions', value: stats.total, dot: null as string | null },
            { label: 'In progress', value: stats.inProgress, dot: 'bg-amber-400' },
            { label: 'Completed', value: stats.completed, dot: 'bg-primary' },
            { label: 'Today', value: stats.today, dot: null as string | null },
          ].map((tile) => (
            <div key={tile.label} className="px-5 py-4">
              <div className="flex items-center gap-1.5">
                {tile.dot && <span className={`w-1.5 h-1.5 rounded-full ${tile.dot}`} />}
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">{tile.label}</span>
              </div>
              <p className="mt-1.5 text-[28px] leading-none font-bold tracking-tight text-text-dark tabular-nums">{tile.value}</p>
            </div>
          ))}
        </motion.div>

        {/* ── Trial / billing banner ─────────────────────────────── */}
        {billing && billing.plan === 'trial' && (
          <div
            className={`mb-6 rounded-2xl border px-5 py-4 flex items-center justify-between gap-4 cursor-pointer transition-all hover:shadow-sm ${billing.can_create_session ? 'bg-amber-50/60 border-amber-200/80' : 'bg-red-50 border-red-200'}`}
            onClick={() => navigate('/billing')}
          >
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <span className={`text-[11px] font-bold uppercase tracking-widest ${billing.can_create_session ? 'text-amber-700' : 'text-red-700'}`}>
                  {billing.can_create_session ? `Free trial — ${billing.sessions_left} session${billing.sessions_left === 1 ? '' : 's'} left` : 'Trial ended'}
                </span>
              </div>
              <div className="w-full h-1.5 bg-amber-100 rounded-full overflow-hidden">
                <div
                  className={`h-1.5 rounded-full transition-all ${trialPct >= 80 ? 'bg-red-500' : 'bg-amber-500'}`}
                  style={{ width: `${trialPct}%` }}
                />
              </div>
              <p className="text-[11px] text-amber-700/70 mt-1.5">
                {billing.trial_sessions_used} of {billing.trial_limit} sessions used
              </p>
            </div>
            <button
              onClick={e => { e.stopPropagation(); navigate('/billing'); }}
              className="flex-shrink-0 bg-primary hover:bg-primary-dark text-white text-[12px] font-bold px-4 py-2 rounded-lg transition-all whitespace-nowrap"
            >
              Upgrade ₹999/mo
            </button>
          </div>
        )}

        {/* ── Revenue strip ─────────────────────────────────────── */}
        {revenue && (
          <div className="mb-8 grid grid-cols-3 rounded-2xl border border-emerald-200/80 bg-emerald-50/60 overflow-hidden divide-x divide-emerald-200/60">
            <div className="px-5 py-3.5">
              <p className="text-[10.5px] font-bold uppercase tracking-wider text-emerald-700/70">DHIS income this month</p>
              <p className="mt-1 text-[1.6rem] font-bold tracking-tight text-emerald-700 leading-none">
                ₹{(revenue.dhis_clinic_amount + revenue.dhis_dsc_amount).toLocaleString('en-IN')}
              </p>
              <p className="text-[11px] text-emerald-600/70 mt-0.5">{revenue.dhis_transactions} records filed</p>
            </div>
            <div className="px-5 py-3.5">
              <p className="text-[10.5px] font-bold uppercase tracking-wider text-emerald-700/70">Lab orders sent</p>
              <p className="mt-1 text-[1.6rem] font-bold tracking-tight text-emerald-700 leading-none">{revenue.lab_dispatches_sent}</p>
              <p className="text-[11px] text-emerald-600/70 mt-0.5">to patients this month</p>
            </div>
            <div className="px-5 py-3.5">
              <p className="text-[10.5px] font-bold uppercase tracking-wider text-emerald-700/70">Follow-ups confirmed</p>
              <p className="mt-1 text-[1.6rem] font-bold tracking-tight text-emerald-700 leading-none">{revenue.follow_ups_confirmed}</p>
              <p className="text-[11px] text-emerald-600/70 mt-0.5">{revenue.follow_ups_sent} reminders sent</p>
            </div>
          </div>
        )}

        {/* ── Per-doctor learning counter ───────────────────────── */}
        {learningStats && learningStats.total_learned > 0 && (
          <div className="mb-8 grid grid-cols-3 rounded-2xl border border-violet-200/80 bg-violet-50/50 overflow-hidden divide-x divide-violet-200/60">
            <div className="px-5 py-3.5">
              <p className="text-[10.5px] font-bold uppercase tracking-wider text-violet-700/70">Patterns learned</p>
              <p className="mt-1 text-[1.6rem] font-bold tracking-tight text-violet-700 leading-none">{learningStats.total_learned}</p>
              <p className="text-[11px] text-violet-600/70 mt-0.5">from your corrections</p>
            </div>
            <div className="px-5 py-3.5">
              <p className="text-[10.5px] font-bold uppercase tracking-wider text-violet-700/70">Accuracy</p>
              <p className="mt-1 text-[1.6rem] font-bold tracking-tight text-violet-700 leading-none">{learningStats.accuracy_pct}%</p>
              <p className="text-[11px] text-violet-600/70 mt-0.5">confirm vs reject rate</p>
            </div>
            <div className="px-5 py-3.5">
              <p className="text-[10.5px] font-bold uppercase tracking-wider text-violet-700/70">Promoted globally</p>
              <p className="mt-1 text-[1.6rem] font-bold tracking-tight text-violet-700 leading-none">{learningStats.promoted_to_global}</p>
              <p className="text-[11px] text-violet-600/70 mt-0.5">shared across all doctors</p>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-6 rounded-xl bg-red-50 text-alert-critical px-4 py-3 text-sm border border-red-100">
            {error}
          </div>
        )}

        {/* ── Invite assistant strip (always visible) ──────────── */}
        {inviteCode && (
          <div className="mb-6 rounded-xl border border-slate-200/80 bg-white shadow-sm overflow-hidden">
            <div className="px-5 py-4">
              <div className="flex items-center gap-2.5 mb-3">
                <div className="w-7 h-7 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                  <svg className="w-3.5 h-3.5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                  </svg>
                </div>
                <span className="text-[13px] font-semibold text-text-dark">Your clinic code</span>
                <span className="text-[11px] text-slate-400 ml-auto">Share with your assistant</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-4 py-2.5 font-mono text-[22px] font-bold tracking-[0.15em] text-text-dark">
                  {inviteCode}
                </div>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(inviteCode);
                    setInviteCopied(true);
                    setTimeout(() => setInviteCopied(false), 2000);
                  }}
                  className="shrink-0 flex items-center gap-1.5 text-[13px] font-semibold text-white bg-primary hover:bg-primary-dark px-4 py-2.5 rounded-lg transition-all active:scale-[0.97] cursor-pointer"
                >
                  {inviteCopied ? (
                    <>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                      Copied!
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      Copy
                    </>
                  )}
                </button>
              </div>
              <p className="text-[11px] text-slate-400 mt-2">
                Assistant logs in → "Enter clinic code" → <strong>{inviteCode}</strong> → done.
              </p>
            </div>
          </div>
        )}

        {/* ── Waiting Room (patients registered by assistant) ── */}
        {(() => {
          const waiting = sessions.filter(s => s.initiated_by === 'assistant' && s.status === 'created');
          if (!waiting.length) return null;
          return (
            <div className="mb-8">
              <div className="flex items-center gap-2 mb-3">
                <span className="flex items-center justify-center w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                <h2 className="text-[13px] font-bold text-text-dark uppercase tracking-wider">Waiting room</h2>
                <span className="text-[11px] text-slate-400">{waiting.length} patient{waiting.length > 1 ? 's' : ''} registered by assistant</span>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {waiting.map(s => (
                  <div key={s.id} className="bg-amber-50 border border-amber-200/70 rounded-xl p-4 flex items-start gap-3">
                    <div className="w-9 h-9 rounded-xl bg-amber-100 border border-amber-200 flex items-center justify-center shrink-0">
                      <svg className="w-4.5 h-4.5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[14px] font-semibold text-text-dark truncate">{s.patient_name || 'Patient'}</p>
                      <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                        {s.patient_age && <span className="text-[11px] text-slate-500">{s.patient_age}y</span>}
                        {s.patient_sex && <span className="text-[11px] text-slate-500">{s.patient_sex}</span>}
                        {s.patient_phone && (
                          <span className="text-[11px] text-emerald-600 font-medium flex items-center gap-0.5">
                            <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413z"/></svg>
                            {s.patient_phone}
                          </span>
                        )}
                      </div>
                      {s.transcript?.startsWith('[Chief complaint:') && (
                        <p className="text-[11px] text-amber-700 mt-1 truncate">{s.transcript.replace('[Chief complaint:', '').replace(']', '').trim()}</p>
                      )}
                    </div>
                    <button
                      onClick={() => navigate(`/consultation/${s.id}`)}
                      className="shrink-0 text-[12px] font-semibold text-white bg-primary hover:bg-primary-dark px-3 py-1.5 rounded-lg transition-all active:scale-[0.97] cursor-pointer whitespace-nowrap"
                    >
                      Start →
                    </button>
                  </div>
                ))}
              </div>
            </div>
          );
        })()}

        {/* ── Sessions toolbar ───────────────────────────────── */}
        <div className="flex items-center justify-between mb-4 gap-4">
          <h2 className="text-sm font-semibold text-text-dark shrink-0">
            Recent sessions{' '}
            <span className="text-slate-400 font-normal tabular-nums">
              ({filteredSessions.length}{search ? ` of ${sessions.length}` : ''})
            </span>
          </h2>
          <div className="relative max-w-xs w-full">
            <svg className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search patient or doctor…"
              className="w-full pl-9 pr-8 py-2 text-[13px] border border-slate-200 rounded-lg outline-none focus:border-primary focus:ring-2 focus:ring-primary/15 bg-white transition-all placeholder:text-slate-400"
            />
            {search && (
              <button onClick={() => setSearch('')} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>

        {/* ── Patient chips (shown when search matches patient names) ── */}
        {matchedPatients.length > 0 && (
          <div className="mb-4 flex flex-wrap gap-2">
            {matchedPatients.map(([name, count]) => (
              <button
                key={name}
                onClick={() => navigate(`/patient/${encodeURIComponent(name)}`)}
                className="flex items-center gap-2.5 bg-white border border-primary/25 hover:border-primary/50 hover:bg-primary/5 px-3.5 py-2 rounded-xl transition-all text-left group cursor-pointer shadow-sm active:scale-[0.98]"
              >
                <span className="grid place-items-center w-7 h-7 rounded-lg bg-primary/10 text-primary font-bold text-xs shrink-0">
                  {(name.trim().split(/\s+/)[0]?.[0] ?? '').toUpperCase() + (name.trim().split(/\s+/).slice(-1)[0]?.[0] ?? '').toUpperCase()}
                </span>
                <span className="flex flex-col">
                  <span className="text-[13px] font-semibold text-text-dark group-hover:text-primary transition-colors leading-tight">{name}</span>
                  <span className="text-[11px] text-slate-400">{count} visit{count !== 1 ? 's' : ''} · View history</span>
                </span>
                <svg className="w-3.5 h-3.5 text-slate-300 group-hover:text-primary transition-colors ml-1 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            ))}
          </div>
        )}

        {/* ── Loading ────────────────────────────────────────── */}
        {loading && (
          <div className="border border-slate-200/70 rounded-2xl overflow-hidden bg-white shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead className="bg-slate-50/70 border-b border-slate-100">
                  <tr>
                    {[1, 2, 3, 4, 5, 6].map(i => (
                      <th key={i} className="px-6 py-3.5"><div className="h-3.5 bg-slate-200 rounded w-20 animate-pulse" /></th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <tr key={i}>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-xl bg-slate-200 animate-pulse shrink-0" />
                          <div className="h-4 bg-slate-200 rounded w-40 animate-pulse" />
                        </div>
                      </td>
                      <td className="px-6 py-4"><div className="h-3.5 bg-slate-200 rounded w-24 animate-pulse" /></td>
                      <td className="px-6 py-4"><div className="h-3.5 bg-slate-200 rounded w-32 animate-pulse" /></td>
                      <td className="px-6 py-4"><div className="h-5 bg-slate-200 rounded w-16 animate-pulse" /></td>
                      <td className="px-6 py-4"><div className="h-5 bg-slate-200 rounded w-24 animate-pulse" /></td>
                      <td className="px-6 py-4 flex justify-end"><div className="h-4 bg-slate-200 rounded w-20 animate-pulse" /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── Empty ──────────────────────────────────────────── */}
        {!loading && sessions.length === 0 && (
          <div className="text-center py-16 border border-slate-200 border-dashed rounded-2xl bg-white">
            <div className="grid place-items-center w-12 h-12 rounded-2xl bg-primary/10 text-primary mx-auto mb-4">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <p className="text-sm font-semibold text-slate-700">No sessions yet</p>
            <p className="text-[13px] text-slate-400 mt-1">Start your first consultation to see it appear here.</p>
            <button
              onClick={() => setShowModeModal(true)}
              className="mt-5 inline-flex items-center gap-1.5 bg-primary hover:bg-primary-dark text-white text-[13px] font-semibold px-4 py-2 rounded-lg transition-all shadow-sm active:scale-[0.98] cursor-pointer"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New session
            </button>
          </div>
        )}

        {/* ── Table ──────────────────────────────────────────── */}
        {!loading && sessions.length > 0 && (
          <div className="border border-slate-200/70 rounded-2xl overflow-hidden bg-white shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead className="bg-slate-50/70 border-b border-slate-100 text-[11px] uppercase tracking-wider text-slate-400">
                  <tr>
                    <th className="px-6 py-3.5 font-semibold">Name / Subject</th>
                    <th className="px-6 py-3.5 font-semibold">Professional</th>
                    <th className="px-6 py-3.5 font-semibold">Date &amp; Time</th>
                    <th className="px-6 py-3.5 font-semibold">Mode</th>
                    <th className="px-6 py-3.5 font-semibold">Status</th>
                    <th className="px-6 py-3.5 text-right font-semibold">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredSessions.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-6 py-10 text-center text-sm text-slate-400">
                        No sessions match <span className="font-semibold text-slate-600">"{search}"</span>
                      </td>
                    </tr>
                  )}
                  {filteredSessions.map((s, i) => {
                    const dx = diagnosisOf(s);
                    const displayName = s.patient_name || dx || (s.mode === 'general' ? 'General session' : 'Untitled session');
                    const sub = s.patient_name ? dx : null;
                    const mode = (s.mode || 'health') as SessionMode;
                    return (
                      <motion.tr
                        initial={reduce ? false : { opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.25, delay: reduce ? 0 : Math.min(i * 0.03, 0.25) }}
                        key={s.id}
                        onClick={() => navigate(`/consultation/${s.id}`)}
                        className="hover:bg-primary/[0.025] cursor-pointer transition-colors group"
                      >
                        <td className="px-6 py-3.5">
                          <div className="flex items-center gap-3">
                            <button
                              type="button"
                              onClick={e => { e.stopPropagation(); if (s.patient_name) setTimelinePatient(s.patient_name); }}
                              title={s.patient_name ? 'View patient history' : undefined}
                              className="grid place-items-center w-9 h-9 rounded-xl bg-primary/10 text-primary text-xs font-bold shrink-0 border border-primary/10 hover:bg-primary/20 transition-colors cursor-pointer"
                            >
                              {initialsOf(displayName)}
                            </button>
                            <div className="min-w-0">
                              <p className="font-semibold text-slate-900 truncate max-w-[220px]">{displayName}</p>
                              {sub && <p className="text-xs text-slate-400 truncate max-w-[220px]">{sub}</p>}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-3.5 text-slate-600">
                          {s.doctor_name || <span className="text-slate-300">—</span>}
                        </td>
                        <td className="px-6 py-3.5 text-slate-500 text-xs tabular-nums">
                          {new Date(s.created_at).toLocaleDateString(undefined, {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric',
                            hour: 'numeric',
                            minute: '2-digit',
                          })}
                        </td>
                        <td className="px-6 py-3.5">
                          <span className={`px-2 py-0.5 rounded-md border text-[10px] font-bold uppercase tracking-wide ${MODE_COLORS[mode]}`}>
                            {mode.charAt(0).toUpperCase() + mode.slice(1)}
                          </span>
                        </td>
                        <td className="px-6 py-3.5">
                          <StatusBadge status={s.status} />
                        </td>
                        <td className="px-6 py-3.5 text-right">
                          <span className="text-primary group-hover:text-primary-dark font-semibold text-xs transition-colors inline-flex items-center justify-end gap-1">
                            Open
                            <svg className="w-3.5 h-3.5 transform group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
                            </svg>
                          </span>
                        </td>
                      </motion.tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* ── Patient Timeline Modal ───────────────────────────── */}
      {timelinePatient && (() => {
        const patientSessions = sessions
          .filter(s => s.patient_name === timelinePatient)
          .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        return (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center p-4"
            onClick={() => setTimelinePatient(null)}>
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md border border-slate-200 overflow-hidden max-h-[80vh] flex flex-col"
              onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between px-6 pt-5 pb-4 border-b border-slate-100 shrink-0">
                <div>
                  <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">Patient history</p>
                  <h2 className="text-[17px] font-bold text-text-dark">{timelinePatient}</h2>
                  <p className="text-[12px] text-slate-500">{patientSessions.length} visit{patientSessions.length !== 1 ? 's' : ''}</p>
                </div>
                <button onClick={() => setTimelinePatient(null)}
                  className="w-8 h-8 flex items-center justify-center rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-all cursor-pointer">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="overflow-y-auto flex-1 px-6 py-4">
                <div className="relative pl-6">
                  {/* Vertical line */}
                  <div className="absolute left-2 top-2 bottom-2 w-0.5 bg-slate-200" />
                  <div className="space-y-5">
                    {patientSessions.map((s, i) => {
                      const dx = diagnosisOf(s);
                      const date = new Date(s.created_at);
                      const isFirst = i === 0;
                      return (
                        <div key={s.id} className="relative">
                          {/* Dot */}
                          <div className={`absolute -left-[19px] top-1 w-3.5 h-3.5 rounded-full border-2 border-white shadow-sm ${
                            s.status === 'complete' ? 'bg-primary' : isFirst ? 'bg-amber-400' : 'bg-slate-300'
                          }`} />
                          <button
                            onClick={() => { setTimelinePatient(null); navigate(`/consultation/${s.id}`); }}
                            className="w-full text-left bg-slate-50 hover:bg-primary/5 border border-slate-200 hover:border-primary/30 rounded-xl p-4 transition-all cursor-pointer group"
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="min-w-0">
                                <p className="text-[12px] font-bold text-slate-500 tabular-nums">
                                  {date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                                  {isFirst && <span className="ml-2 text-[10px] font-bold text-amber-600 bg-amber-50 border border-amber-200 px-1.5 py-0.5 rounded-full">Latest</span>}
                                </p>
                                {dx && <p className="text-[13px] font-semibold text-text-dark mt-0.5 truncate">{dx}</p>}
                                {s.transcript?.startsWith('[Chief complaint:') && (
                                  <p className="text-[11px] text-slate-500 mt-0.5 truncate">
                                    {s.transcript.replace('[Chief complaint:', 'CC:').replace(']', '')}
                                  </p>
                                )}
                              </div>
                              <span className={`shrink-0 px-2 py-0.5 rounded-md text-[10px] font-bold uppercase border ${
                                STATUS_COLORS[s.status] ?? 'bg-slate-100 text-slate-600 border-slate-200'
                              }`}>{s.status.replace(/_/g, ' ')}</span>
                            </div>
                            <p className="text-[11px] text-primary mt-2 font-semibold opacity-0 group-hover:opacity-100 transition-opacity">
                              Open session →
                            </p>
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      })()}

      {/* ── Mode Selection Modal ─────────────────────────────── */}
      {showModeModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg border border-slate-200 overflow-hidden">

            {/* Header */}
            <div className="px-6 pt-6 pb-4">
              <h2 className="text-lg font-bold text-slate-900 tracking-tight">New Session</h2>
              <p className="text-xs text-slate-400 mt-0.5">Select mode, then fill in the details</p>
            </div>

            {/* Mode tabs — compact horizontal */}
            <div className="px-6 pb-4">
              <div className="grid grid-cols-2 gap-1.5 bg-slate-100 p-1 rounded-xl">
                {AVAILABLE_MODES.map((mode) => (
                  <button
                    key={mode}
                    onClick={() => setSelectedMode(mode)}
                    className={`flex flex-col items-center gap-1 py-2.5 px-1 rounded-lg text-center transition-all cursor-pointer ${
                      selectedMode === mode
                        ? 'bg-white shadow-sm text-primary'
                        : 'text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    <span className={`w-6 h-6 ${selectedMode === mode ? 'text-primary' : 'text-slate-400'}`}>
                      {MODE_ICONS[mode]}
                    </span>
                    <span className={`text-[10px] font-bold leading-tight ${selectedMode === mode ? 'text-primary' : 'text-slate-500'}`}>
                      {mode === 'health' ? 'Health' : 'General'}
                    </span>
                  </button>
                ))}
              </div>
              <p className="text-[11px] text-slate-400 mt-2 text-center">{MODE_DESCS[selectedMode]}</p>
            </div>

            {/* Contextual fields */}
            <div className="px-6 pb-5 space-y-3">
              {selectedMode === 'health' && (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-slate-600 mb-1.5">Patient Name</label>
                      <input
                        type="text"
                        value={sessionPatientName}
                        onChange={e => setSessionPatientName(e.target.value)}
                        placeholder="e.g. Ramesh Kumar"
                        className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm text-slate-800 outline-none focus:border-primary focus:ring-2 focus:ring-primary/15 transition-all"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-600 mb-1.5">Doctor Name</label>
                      <input
                        type="text"
                        value={sessionDoctorName}
                        onChange={e => setSessionDoctorName(e.target.value)}
                        placeholder="e.g. Dr. Priya Sharma"
                        className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm text-slate-800 outline-none focus:border-primary focus:ring-2 focus:ring-primary/15 transition-all"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1.5">
                      Patient WhatsApp <span className="font-normal text-slate-400">(for follow-up & lab dispatch)</span>
                    </label>
                    <input
                      type="tel"
                      value={sessionPatientPhone}
                      onChange={e => setSessionPatientPhone(e.target.value)}
                      placeholder="+91 98765 43210"
                      className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm text-slate-800 outline-none focus:border-primary focus:ring-2 focus:ring-primary/15 transition-all"
                    />
                  </div>
                </div>
              )}

              {selectedMode === 'government' && (
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1.5">Complainant Name</label>
                  <input
                    type="text"
                    value={sessionPatientName}
                    onChange={e => setSessionPatientName(e.target.value)}
                    placeholder="e.g. Ramesh Singh"
                    className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm text-slate-800 outline-none focus:border-primary focus:ring-2 focus:ring-primary/15 transition-all"
                  />
                </div>
              )}

              {selectedMode === 'legal' && (
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1.5">Party / Petitioner Name</label>
                  <input
                    type="text"
                    value={sessionPatientName}
                    onChange={e => setSessionPatientName(e.target.value)}
                    placeholder="e.g. Priya Sharma"
                    className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm text-slate-800 outline-none focus:border-primary focus:ring-2 focus:ring-primary/15 transition-all"
                  />
                </div>
              )}

              {selectedMode === 'general' && (
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1.5">Session Label <span className="font-normal text-slate-400">(optional)</span></label>
                  <input
                    type="text"
                    value={sessionPatientName}
                    onChange={e => setSessionPatientName(e.target.value)}
                    placeholder="e.g. Team meeting, Interview..."
                    className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm text-slate-800 outline-none focus:border-primary focus:ring-2 focus:ring-primary/15 transition-all"
                  />
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex gap-3 justify-end">
              <button
                onClick={() => { setShowModeModal(false); setSessionPatientPhone(''); }}
                className="px-4 py-2 text-sm text-slate-500 hover:text-slate-700 font-medium transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleNewConsultation}
                className="px-6 py-2 bg-primary hover:bg-primary-dark text-white text-sm font-semibold rounded-lg transition-all shadow-sm active:scale-[0.98] cursor-pointer flex items-center gap-2"
              >
                Start Session
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
