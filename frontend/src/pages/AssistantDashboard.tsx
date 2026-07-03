import { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FlaskConical, Pill, CalendarClock, Send, CheckCircle2,
  ChevronDown, ChevronRight, LogOut, ClipboardList, Bell, ShieldAlert, FileText, UserPlus,
} from 'lucide-react';
import {
  listTasks, listSessions, updateTask, sendTaskFollowup,
  getMyClinicStatus, joinClinic, dispatchPrescription, getRevenueSummary,
} from '../lib/api';
import type { RevenueSummary } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import ShareWhatsappModal from '../components/ShareWhatsappModal';
import type { AssistantTask, ConsultationSession } from '../types/clinical';

// ── Task-type presentation + primary action ────────────────────────────────────

type PrimaryAction = 'whatsapp' | 'followup' | 'done';

interface TaskMeta {
  icon: React.ElementType;
  color: string;
  bg: string;
  label: string;
  action: PrimaryAction;
  cta: string;
}

const TASK_META: Record<string, TaskMeta> = {
  review_prescription:  { icon: Pill,         color: 'text-emerald-600', bg: 'bg-emerald-50 border-emerald-100', label: 'Prescription', action: 'whatsapp', cta: 'Send on WhatsApp' },
  order_investigations: { icon: FlaskConical,  color: 'text-blue-600',    bg: 'bg-blue-50 border-blue-100',       label: 'Lab order',     action: 'done',     cta: 'Mark dispatched' },
  follow_up:            { icon: CalendarClock, color: 'text-amber-600',   bg: 'bg-amber-50 border-amber-100',     label: 'Follow-up',     action: 'followup', cta: 'Send reminder' },
  document_allergy:     { icon: ShieldAlert,   color: 'text-rose-600',    bg: 'bg-rose-50 border-rose-100',       label: 'Allergy',       action: 'done',     cta: 'Mark documented' },
};

const DEFAULT_META: TaskMeta = {
  icon: ClipboardList, color: 'text-slate-500', bg: 'bg-slate-50 border-slate-200', label: 'Task', action: 'done', cta: 'Mark done',
};

function metaFor(taskType: string): TaskMeta {
  return TASK_META[taskType] ?? DEFAULT_META;
}

function patientFor(session?: ConsultationSession): string {
  return session?.patient_name || 'Patient';
}

function detailFor(task: AssistantTask, session?: ConsultationSession): string {
  if (task.task_type === 'review_prescription') {
    const meds = (session?.clinical_facts as any)?.medications;
    if (Array.isArray(meds) && meds.length) {
      const text = meds
        .filter((m: any) => m?.name)
        .map((m: any) => `${m.name}${m.dosage ? ' ' + m.dosage : ''}${m.frequency ? ' ' + m.frequency : ''}`)
        .join(' · ');
      if (text) return text;
    }
    return 'Review & share the prescription with the patient.';
  }
  // Other task titles read "Order investigations: …" / "Schedule follow-up: …".
  const colon = task.title.indexOf(':');
  return colon >= 0 ? task.title.slice(colon + 1).trim() : task.title;
}

function timeAgo(iso?: string): string {
  if (!iso) return '';
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function initials(name: string) {
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
}

// ── Clinic Code Entry Screen ───────────────────────────────────────────────────

function ClinicCodeEntry({ onLinked }: { onLinked: () => void }) {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleJoin(e: React.FormEvent) {
    e.preventDefault();
    if (!code.trim()) return;
    setLoading(true);
    setError('');
    try {
      await joinClinic(code.trim());
      onLinked();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Invalid code. Ask your doctor for the correct 6-character code.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#FAFAF7] flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-1">
            <span className="grid place-items-center w-10 h-10 rounded-xl bg-primary text-white font-bold text-lg">श</span>
            <span className="text-xl font-bold text-text-dark tracking-tight">Lipi</span>
          </div>
          <p className="text-sm text-slate-500 mt-1">Assistant mode</p>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="mb-5">
            <h1 className="text-[17px] font-bold text-text-dark">Enter your clinic code</h1>
            <p className="text-[13px] text-slate-500 mt-1 leading-relaxed">
              Ask your doctor for their 6-character clinic code. You only need to enter this once.
            </p>
          </div>

          <form onSubmit={handleJoin} className="space-y-4">
            <input
              type="text"
              value={code}
              onChange={e => setCode(e.target.value.toUpperCase().replace(/[^A-F0-9]/g, '').slice(0, 6))}
              placeholder="e.g. A1B2C3"
              maxLength={6}
              className="w-full text-center font-mono text-[28px] font-bold tracking-[0.2em] uppercase border border-slate-200 rounded-xl px-4 py-4 outline-none focus:border-primary focus:ring-2 focus:ring-primary/15 bg-slate-50 focus:bg-white transition-all placeholder:text-slate-300 placeholder:text-[18px] placeholder:tracking-normal"
              autoFocus
            />

            {error && (
              <p className="text-[12.5px] text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={code.length < 4 || loading}
              className="w-full bg-primary hover:bg-primary-dark disabled:opacity-50 text-white font-semibold text-[14px] py-3 rounded-xl transition-all active:scale-[0.98] cursor-pointer"
            >
              {loading ? 'Joining…' : 'Join clinic'}
            </button>
          </form>

          <p className="text-[11.5px] text-slate-400 text-center mt-4 leading-relaxed">
            The code is the same until the doctor resets it. Contact your doctor if you don't have it.
          </p>
        </div>
      </div>
    </div>
  );
}

// ── Follow-up reminder modal ────────────────────────────────────────────────────

function FollowupModal({
  task, patientName, defaultText, defaultPhone, onClose, onSent,
}: {
  task: AssistantTask;
  patientName: string;
  defaultText: string;
  defaultPhone?: string;
  onClose: () => void;
  onSent: () => void;
}) {
  const [phone, setPhone] = useState(defaultPhone || '');
  const [text, setText] = useState(defaultText);
  const [consent, setConsent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!consent) { setError('Patient consent is required to send.'); return; }
    setError('');
    setLoading(true);
    try {
      await sendTaskFollowup(task.id, { phone_number: phone, consent, follow_up_text: text });
      onSent();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to send reminder.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        onClick={onClose}
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
      />
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 10 }} animate={{ opacity: 1, scale: 1, y: 0 }}
        className="relative w-full max-w-md bg-white rounded-2xl shadow-2xl border border-slate-100 overflow-hidden"
      >
        <div className="px-6 py-4 border-b border-slate-100 flex items-center gap-2">
          <CalendarClock className="w-5 h-5 text-amber-500" />
          <h3 className="text-[15px] font-bold text-text-dark">Send follow-up reminder</h3>
        </div>
        <form onSubmit={submit} className="p-6 space-y-4">
          <div className="bg-slate-50 rounded-xl px-3 py-2 text-[12px] text-slate-500 flex justify-between">
            <span>Patient</span><strong className="text-text-dark font-medium">{patientName}</strong>
          </div>
          <div>
            <label className="block text-[12px] font-semibold text-slate-600 mb-1.5">Patient phone (WhatsApp)</label>
            <input
              type="tel" required value={phone} onChange={e => setPhone(e.target.value)}
              placeholder="e.g. 9876543210 or +91…"
              className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-[14px] outline-none focus:border-primary focus:ring-2 focus:ring-primary/15 bg-slate-50 focus:bg-white transition-all"
            />
          </div>
          <div>
            <label className="block text-[12px] font-semibold text-slate-600 mb-1.5">Reminder message</label>
            <textarea
              value={text} onChange={e => setText(e.target.value)} rows={3}
              className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-[13px] outline-none focus:border-primary focus:ring-2 focus:ring-primary/15 bg-slate-50 focus:bg-white transition-all resize-none"
            />
          </div>
          <label className="flex items-start gap-2.5 bg-amber-50/60 border border-amber-100 px-3 py-2.5 rounded-xl cursor-pointer">
            <input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)} className="mt-0.5 h-4 w-4 accent-primary" />
            <span className="text-[12px] text-amber-800/90 leading-relaxed">Patient consents to receiving this reminder via WhatsApp.</span>
          </label>
          {error && <p className="text-[12.5px] text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">{error}</p>}
          <div className="flex justify-end gap-3 pt-1">
            <button type="button" onClick={onClose} className="px-4 py-2 text-[13px] font-medium text-slate-400 hover:text-slate-600 transition-colors cursor-pointer">Cancel</button>
            <button
              type="submit" disabled={loading || !phone.trim() || !consent}
              className="flex items-center gap-1.5 px-5 py-2 text-[13px] font-semibold text-white bg-primary hover:bg-primary-dark rounded-lg disabled:opacity-50 transition-all active:scale-[0.98] cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
              {loading ? 'Sending…' : 'Send reminder'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}

// ── One-click prescription dispatch (phone already on file) ───────────────────

function DispatchConfirmModal({
  task, patientName, phone, onClose, onSent,
}: {
  task: AssistantTask;
  patientName: string;
  phone: string;
  onClose: () => void;
  onSent: () => void;
}) {
  const [consent, setConsent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleDispatch() {
    if (!consent) { setError('Patient consent is required.'); return; }
    setLoading(true);
    setError('');
    try {
      await dispatchPrescription(task.id, true);
      onSent();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to send. Try again.');
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center px-4">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        onClick={onClose} className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 8 }} animate={{ opacity: 1, scale: 1, y: 0 }}
        className="relative w-full max-w-sm bg-white rounded-2xl shadow-2xl border border-slate-100 overflow-hidden"
      >
        <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-emerald-50 border border-emerald-100 flex items-center justify-center">
            <svg className="w-4 h-4 text-emerald-600" viewBox="0 0 24 24" fill="currentColor">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/>
              <path d="M11.854 0h-.008A11.838 11.838 0 000 11.854c0 2.652.876 5.099 2.352 7.074L.813 23.187l4.345-1.391a11.843 11.843 0 006.688 2.04h.008A11.838 11.838 0 0023.708 11.99C23.708 5.365 18.479.136 11.854 0zm0 21.666a9.835 9.835 0 01-5.031-1.381l-.36-.214-3.74 1.198 1.168-3.646-.235-.374A9.853 9.853 0 012.01 11.854c0-5.437 4.42-9.857 9.854-9.857 5.431 0 9.849 4.42 9.849 9.857 0 5.434-4.418 9.812-9.859 9.812z"/>
            </svg>
          </div>
          <h3 className="text-[14px] font-bold text-text-dark">Send prescription</h3>
          <button onClick={onClose} className="ml-auto text-slate-400 hover:text-slate-600 transition-colors cursor-pointer text-[16px] leading-none">✕</button>
        </div>
        <div className="p-5 space-y-4">
          <div className="bg-slate-50 rounded-xl px-4 py-3 space-y-1.5 text-[12px]">
            <div className="flex justify-between text-slate-500">
              <span>Patient</span>
              <strong className="text-text-dark font-semibold">{patientName}</strong>
            </div>
            <div className="flex justify-between text-slate-500">
              <span>WhatsApp</span>
              <strong className="text-emerald-600 font-semibold">{phone}</strong>
            </div>
          </div>

          <label className="flex items-start gap-2.5 bg-emerald-50/70 border border-emerald-100 px-3 py-2.5 rounded-xl cursor-pointer">
            <input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)}
              className="mt-0.5 h-4 w-4 accent-emerald-600 cursor-pointer" />
            <span className="text-[12px] text-emerald-800/90 leading-relaxed">
              Patient consents to receiving their prescription via WhatsApp.
            </span>
          </label>

          {error && <p className="text-[12px] text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">{error}</p>}

          <button
            onClick={handleDispatch}
            disabled={loading || !consent}
            className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-[13px] font-semibold py-2.5 rounded-xl transition-all active:scale-[0.98] cursor-pointer"
          >
            <Send className="w-3.5 h-3.5" />
            {loading ? 'Sending…' : 'Send prescription'}
          </button>
          <p className="text-[11px] text-slate-400 text-center">Phone number was captured at patient registration.</p>
        </div>
      </motion.div>
    </div>
  );
}

// ── Main Dashboard ─────────────────────────────────────────────────────────────

export default function AssistantDashboard() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [clinicLinked, setClinicLinked] = useState<boolean | null>(null);  // null = checking
  const [clinicName, setClinicName] = useState<string | null>(null);
  const [tasks, setTasks] = useState<AssistantTask[]>([]);
  const [sessionMap, setSessionMap] = useState<Record<string, ConsultationSession>>({});
  const [loading, setLoading] = useState(true);
  const [newTaskCount, setNewTaskCount] = useState(0);
  const [showDone, setShowDone] = useState(false);
  const [whatsappTask, setWhatsappTask] = useState<AssistantTask | null>(null);
  const [dispatchTask, setDispatchTask] = useState<AssistantTask | null>(null);
  const [followupTask, setFollowupTask] = useState<AssistantTask | null>(null);
  const lastCountRef = useRef<number | null>(null);
  const [revenue, setRevenue] = useState<RevenueSummary | null>(null);

  // ── Clinic status check ────────────────────────────────────────────────────

  useEffect(() => {
    getMyClinicStatus()
      .then(status => {
        setClinicLinked(status.linked);
        if (status.linked) setClinicName(status.clinic_name || null);
      })
      .catch(() => setClinicLinked(true)); // graceful: assume linked if endpoint fails
    getRevenueSummary().then(setRevenue).catch(() => {});
  }, []);

  // ── Poll real tasks + sessions every 30s ───────────────────────────────────

  const fetchData = useCallback(async () => {
    try {
      const [taskList, sessionList] = await Promise.all([listTasks(), listSessions()]);
      const map: Record<string, ConsultationSession> = {};
      for (const s of sessionList) map[s.id] = s;
      setSessionMap(map);
      setTasks(taskList);

      const pendingCount = taskList.filter(t => t.status !== 'done').length;
      if (lastCountRef.current !== null && pendingCount > lastCountRef.current) {
        setNewTaskCount(n => n + (pendingCount - (lastCountRef.current ?? 0)));
      }
      lastCountRef.current = pendingCount;
    } catch {
      // silent on poll failures
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (clinicLinked === null) return;
    fetchData();
    const interval = setInterval(fetchData, 30_000);
    return () => clearInterval(interval);
  }, [clinicLinked, fetchData]);

  const pending = useMemo(
    () => tasks.filter(t => t.status !== 'done')
      .sort((a, b) => new Date(b.created_at ?? 0).getTime() - new Date(a.created_at ?? 0).getTime()),
    [tasks],
  );
  const done = useMemo(() => tasks.filter(t => t.status === 'done'), [tasks]);

  function applyDone(taskId: string) {
    setTasks(prev => prev.map(t =>
      t.id === taskId ? { ...t, status: 'done', completed_at: new Date().toISOString() } : t,
    ));
  }

  async function markDone(taskId: string) {
    applyDone(taskId);                       // optimistic
    try {
      await updateTask(taskId, { status: 'done' });
    } catch {
      fetchData();                           // revert from server on failure
    }
  }

  function handlePrimary(task: AssistantTask) {
    const action = metaFor(task.task_type).action;
    if (action === 'whatsapp') {
      // If phone is on file from intake, skip the modal — use one-click dispatch
      const phone = sessionMap[task.session_id]?.patient_phone;
      if (phone) setDispatchTask(task);
      else setWhatsappTask(task);
    } else if (action === 'followup') {
      setFollowupTask(task);
    } else {
      markDone(task.id);
    }
  }

  function handleLogout() {
    logout();
    navigate('/login');
  }

  // ── Clinic gate ────────────────────────────────────────────────────────────

  if (clinicLinked === null) {
    return (
      <div className="min-h-screen bg-[#FAFAF7] flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!clinicLinked) {
    return <ClinicCodeEntry onLinked={() => { setClinicLinked(true); setLoading(true); fetchData(); }} />;
  }

  return (
    <div className="min-h-screen bg-[#FAFAF7] font-sans text-text-dark antialiased">
      {/* Nav */}
      <header className="sticky top-0 z-20 bg-white/90 backdrop-blur border-b border-slate-200/80">
        <div className="max-w-2xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="grid place-items-center w-8 h-8 rounded-lg bg-primary text-white font-bold text-sm">श</span>
            <span className="font-bold text-[15px] tracking-tight">Lipi</span>
            <span className="text-[11px] font-semibold text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full ml-1">Assistant</span>
            {clinicName && (
              <span className="hidden sm:inline text-[11px] text-slate-400">· {clinicName}</span>
            )}
          </div>
          <div className="flex items-center gap-2.5">
            {newTaskCount > 0 && (
              <button
                onClick={() => setNewTaskCount(0)}
                className="flex items-center gap-1.5 text-[12px] font-semibold text-white bg-primary px-2.5 py-1 rounded-full animate-pulse"
              >
                <Bell className="w-3 h-3" />
                {newTaskCount} new
              </button>
            )}
            <button
              onClick={() => navigate('/assistant/intake')}
              className="flex items-center gap-1.5 text-[12px] font-semibold text-white bg-primary hover:bg-primary-dark px-3 py-1.5 rounded-lg transition-all active:scale-[0.98] cursor-pointer"
            >
              <UserPlus className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Register patient</span>
              <span className="sm:hidden">+</span>
            </button>
            <button
              onClick={handleLogout}
              className="flex items-center gap-1 text-[12px] text-slate-400 hover:text-slate-600 transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        {/* Revenue summary card */}
        {revenue && (revenue.dhis_transactions > 0 || revenue.lab_dispatches_sent > 0 || revenue.follow_ups_sent > 0) && (
          <div className="rounded-2xl border border-emerald-200/80 bg-emerald-50/70 px-5 py-4">
            <p className="text-[10.5px] font-bold uppercase tracking-wider text-emerald-700/70 mb-3">This month — clinic revenue activity</p>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <p className="text-[1.35rem] font-bold text-emerald-700 leading-none">₹{(revenue.dhis_clinic_amount + revenue.dhis_dsc_amount).toLocaleString('en-IN')}</p>
                <p className="text-[11px] text-emerald-600/70 mt-0.5">DHIS income</p>
              </div>
              <div>
                <p className="text-[1.35rem] font-bold text-emerald-700 leading-none">{revenue.lab_dispatches_sent}</p>
                <p className="text-[11px] text-emerald-600/70 mt-0.5">lab orders sent</p>
              </div>
              <div>
                <p className="text-[1.35rem] font-bold text-emerald-700 leading-none">{revenue.follow_ups_confirmed}</p>
                <p className="text-[11px] text-emerald-600/70 mt-0.5">appts confirmed</p>
              </div>
            </div>
          </div>
        )}

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-[1.25rem] font-bold tracking-tight">Today's queue</h1>
            <p className="text-[13px] text-slate-500 mt-0.5">
              {loading ? 'Loading…' : `${pending.length} task${pending.length !== 1 ? 's' : ''} pending`}
            </p>
          </div>
          {!loading && pending.length === 0 && done.length > 0 && (
            <span className="flex items-center gap-1.5 text-[12px] font-semibold text-emerald-600 bg-emerald-50 border border-emerald-100 px-3 py-1.5 rounded-full">
              <CheckCircle2 className="w-3.5 h-3.5" />
              All caught up
            </span>
          )}
        </div>

        {/* Pending */}
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => <div key={i} className="h-28 bg-slate-100 rounded-2xl animate-pulse" />)}
          </div>
        ) : pending.length === 0 && done.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <ClipboardList className="w-10 h-10 text-slate-300 mb-3" />
            <p className="text-[14px] font-medium text-slate-500">No tasks yet</p>
            <p className="text-[12px] text-slate-400 mt-1">Tasks appear here once the doctor finishes a consultation.</p>
          </div>
        ) : (
          <AnimatePresence mode="popLayout">
            {pending.map(task => (
              <TaskCard
                key={task.id}
                task={task}
                session={sessionMap[task.session_id]}
                onPrimary={() => handlePrimary(task)}
                onDone={() => markDone(task.id)}
                onView={() => navigate(`/review/${task.session_id}`)}
              />
            ))}
          </AnimatePresence>
        )}

        {/* Done */}
        {done.length > 0 && (
          <div>
            <button
              onClick={() => setShowDone(v => !v)}
              className="flex items-center gap-1.5 text-[12px] font-semibold text-slate-400 hover:text-slate-600 transition-colors mb-3"
            >
              {showDone ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
              Done ({done.length})
            </button>
            <AnimatePresence>
              {showDone && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                  className="space-y-2 overflow-hidden"
                >
                  {done.map(task => (
                    <DoneCard key={task.id} task={task} session={sessionMap[task.session_id]} />
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </main>

      {/* Action modals */}
      {whatsappTask && (
        <ShareWhatsappModal
          isOpen
          onClose={() => setWhatsappTask(null)}
          sessionId={whatsappTask.session_id}
          patientName={patientFor(sessionMap[whatsappTask.session_id])}
          onSent={() => { markDone(whatsappTask.id); setWhatsappTask(null); }}
        />
      )}
      <AnimatePresence>
        {dispatchTask && (
          <DispatchConfirmModal
            task={dispatchTask}
            patientName={patientFor(sessionMap[dispatchTask.session_id])}
            phone={sessionMap[dispatchTask.session_id]?.patient_phone || ''}
            onClose={() => setDispatchTask(null)}
            onSent={() => { applyDone(dispatchTask.id); setDispatchTask(null); }}
          />
        )}
      </AnimatePresence>
      <AnimatePresence>
        {followupTask && (
          <FollowupModal
            task={followupTask}
            patientName={patientFor(sessionMap[followupTask.session_id])}
            defaultText={detailFor(followupTask, sessionMap[followupTask.session_id])}
            defaultPhone={sessionMap[followupTask.session_id]?.patient_phone}
            onClose={() => setFollowupTask(null)}
            onSent={() => { applyDone(followupTask.id); setFollowupTask(null); }}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

function TaskCard({
  task, session, onPrimary, onDone, onView,
}: {
  task: AssistantTask;
  session?: ConsultationSession;
  onPrimary: () => void;
  onDone: () => void;
  onView: () => void;
}) {
  const meta = metaFor(task.task_type);
  const Icon = meta.icon;
  const patient = patientFor(session);
  const detail = detailFor(task, session);
  const primaryIsDone = meta.action === 'done';

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: 40, transition: { duration: 0.2 } }}
      className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-4 flex gap-3"
    >
      <div className={`shrink-0 w-10 h-10 rounded-xl border flex items-center justify-center ${meta.bg}`}>
        <Icon className={`w-[18px] h-[18px] ${meta.color}`} strokeWidth={2} />
      </div>

      <div className="flex-1 min-w-0">
        <span className={`text-[10px] font-bold uppercase tracking-wider ${meta.color}`}>{meta.label}</span>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="grid place-items-center w-5 h-5 rounded-full bg-slate-100 text-[9px] font-bold text-slate-600 shrink-0">
            {initials(patient)}
          </span>
          <p className="text-[14px] font-semibold text-text-dark truncate">{patient}</p>
          <span className="text-[11px] text-slate-400 shrink-0">{timeAgo(task.created_at)}</span>
        </div>
        <p className="text-[12px] text-slate-500 mt-1.5 leading-relaxed line-clamp-2">{detail}</p>

        <div className="flex items-center gap-3 mt-3">
          <button onClick={onView} className="flex items-center gap-1 text-[12px] font-medium text-slate-500 hover:text-primary transition-colors">
            <FileText className="w-3.5 h-3.5" />
            View note
          </button>
          {!primaryIsDone && (
            <button onClick={onDone} className="text-[12px] font-medium text-slate-400 hover:text-slate-600 transition-colors">
              Mark done
            </button>
          )}
          <button
            onClick={onPrimary}
            className="ml-auto flex items-center gap-1.5 text-[12px] font-semibold text-white bg-primary hover:bg-primary-dark px-3 py-1.5 rounded-full active:scale-[0.97] transition-all"
          >
            {meta.action === 'whatsapp' || meta.action === 'followup'
              ? <Send className="w-3.5 h-3.5" />
              : <CheckCircle2 className="w-3.5 h-3.5" />}
            {meta.cta}
          </button>
        </div>
      </div>
    </motion.div>
  );
}

function DoneCard({ task, session }: { task: AssistantTask; session?: ConsultationSession }) {
  const meta = metaFor(task.task_type);
  const Icon = meta.icon;
  const patient = patientFor(session);

  return (
    <div className="bg-slate-50 rounded-xl border border-slate-100 p-3 flex items-center gap-3 opacity-70">
      <div className="shrink-0 w-8 h-8 rounded-lg border flex items-center justify-center bg-white border-slate-200">
        <Icon className="w-3.5 h-3.5 text-slate-400" strokeWidth={2} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-[12px] font-medium text-slate-500 truncate">{meta.label} · {patient}</p>
        <p className="text-[11px] text-slate-400 truncate">{task.notes || detailFor(task, session)}</p>
      </div>
      <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
    </div>
  );
}
