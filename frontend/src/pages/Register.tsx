import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import { ArrowRight, ShieldCheck, AlertCircle, Check, Loader2, Stethoscope, ClipboardList } from 'lucide-react';
import { CursorSpotlight, AuroraBackdrop } from '../components/Ambient';
import api from '../lib/api';

const TRUST = ['Audit Trail Enabled', 'Local NLP', 'On-Shore ASR', 'No LLM Hallucination'];

const VALUE_PROPS = [
  'Voice → reviewed SOAP note in under 2 minutes',
  'Every clinical fact traces to the transcript — zero hallucination',
  'Hindi · English · Hinglish, built for Indian OPDs',
];

const ROLES = [
  { value: 'doctor', label: 'Doctor', icon: Stethoscope, desc: 'Record consultations, review notes, manage your OPD' },
  { value: 'assistant', label: 'Assistant / Staff', icon: ClipboardList, desc: 'Manage patient queue, dispatch prescriptions & orders' },
] as const;

export default function Register() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState<'doctor' | 'assistant'>('doctor');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const reduce = useReducedMotion();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      await api.post('/auth/register', { username, email, password, full_name: fullName, role });
      navigate('/login');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error creating account. Try a different username.');
    } finally {
      setIsLoading(false);
    }
  };

  const inputCls =
    'block w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-[14px] text-text-dark placeholder-slate-400 focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/15 focus:bg-white transition-all';

  return (
    <div className="min-h-screen bg-bg-warm font-sans text-text-dark antialiased grid lg:grid-cols-2 overflow-hidden">
      <CursorSpotlight />

      {/* ── Left brand panel ─────────────────────────────────── */}
      <div className="relative hidden lg:flex flex-col justify-between p-12 bg-primary overflow-hidden">
        <div aria-hidden className="absolute inset-0 -z-0 overflow-hidden">
          <div className="aurora-blob aurora-1 w-[36rem] h-[36rem] -top-32 -left-24 bg-[#46b96e]/40" />
          <div className="aurora-blob aurora-2 w-[28rem] h-[28rem] bottom-0 right-0 bg-[#2E8B57]/30" />
        </div>

        <div className="relative z-10">
          <div className="flex items-center gap-2.5">
            <span className="grid place-items-center w-9 h-9 rounded-xl bg-white/15 text-white font-bold text-xl">श</span>
            <span className="text-white text-[17px] font-bold tracking-tight">Lipi</span>
          </div>
        </div>

        <div className="relative z-10 space-y-7">
          <div>
            <p className="text-white/60 text-[11px] font-semibold uppercase tracking-widest mb-3">Why Lipi</p>
            <ul className="space-y-3">
              {VALUE_PROPS.map(p => (
                <li key={p} className="flex items-start gap-3 text-white/90 text-[13px] leading-snug">
                  <Check className="w-4 h-4 text-[#46b96e] shrink-0 mt-0.5" strokeWidth={2.5} />
                  {p}
                </li>
              ))}
            </ul>
          </div>

          <div className="border-t border-white/10 pt-6">
            <p className="text-white/50 text-[11px] leading-relaxed">
              Trusted by cardiologists, neurologists, and surgeons across India's top hospitals.
            </p>
          </div>
        </div>

        <div className="relative z-10">
          <p className="text-white/30 text-[11px]">Research prototype. Not a certified medical device.</p>
        </div>
      </div>

      {/* ── Right form panel ─────────────────────────────────── */}
      <div className="relative flex flex-col justify-center px-6 py-12 sm:px-12 lg:px-16 overflow-hidden">
        <AuroraBackdrop />

        <motion.div
          initial={reduce ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
          className="relative z-10 w-full max-w-sm mx-auto"
        >
          {/* Mobile logo */}
          <div className="flex items-center gap-2 mb-8 lg:hidden">
            <span className="grid place-items-center w-8 h-8 rounded-lg bg-primary text-white font-bold text-base">श</span>
            <span className="text-[16px] font-bold tracking-tight text-text-dark">Lipi</span>
          </div>

          <div className="mb-7">
            <h1 className="text-[1.6rem] font-bold tracking-tight text-text-dark leading-tight">
              Create your account
            </h1>
            <p className="text-slate-500 text-[13px] mt-1">
              Already have one?{' '}
              <Link to="/login" className="text-primary font-semibold hover:underline">Sign in</Link>
            </p>
          </div>

          {/* Trust strip */}
          <div className="flex flex-wrap gap-1.5 mb-6">
            {TRUST.map(t => (
              <span key={t} className="flex items-center gap-1 text-[10px] font-semibold text-primary/90 bg-primary/8 border border-primary/15 px-2 py-1 rounded-full">
                <ShieldCheck className="w-3 h-3" strokeWidth={2.5} />
                {t}
              </span>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Role selector */}
            <div>
              <label className="block text-[12px] font-semibold text-slate-600 mb-2">I am a</label>
              <div className="grid grid-cols-2 gap-2">
                {ROLES.map(r => {
                  const Icon = r.icon;
                  const active = role === r.value;
                  return (
                    <button
                      key={r.value}
                      type="button"
                      onClick={() => setRole(r.value)}
                      className={`flex items-center gap-2 px-3 py-2.5 rounded-xl border text-left transition-all cursor-pointer ${
                        active
                          ? 'bg-primary/8 border-primary/40 text-primary'
                          : 'bg-white border-slate-200 text-slate-500 hover:border-slate-300'
                      }`}
                    >
                      <Icon className="w-4 h-4 shrink-0" strokeWidth={active ? 2.2 : 1.8} />
                      <span className="text-[12px] font-semibold truncate">{r.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[12px] font-semibold text-slate-600 mb-1.5">Full name</label>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={e => setFullName(e.target.value)}
                  placeholder="Dr. Priya Sharma"
                  className={inputCls}
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-[12px] font-semibold text-slate-600 mb-1.5">Username</label>
                <input
                  type="text"
                  required
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  placeholder="drpriya"
                  className={inputCls}
                />
              </div>
            </div>

            <div>
              <label className="block text-[12px] font-semibold text-slate-600 mb-1.5">Email address</label>
              <input
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="doctor@hospital.in"
                className={inputCls}
              />
            </div>

            <div>
              <label className="block text-[12px] font-semibold text-slate-600 mb-1.5">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Choose a secure password"
                className={inputCls}
              />
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-start gap-2.5 bg-red-50 text-red-700 border border-red-200 rounded-xl px-4 py-3 text-[13px]"
              >
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                {error}
              </motion.div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-1 flex items-center justify-center gap-2 py-3 px-4 bg-primary hover:bg-primary-dark disabled:opacity-60 text-white text-[14px] font-semibold rounded-xl transition-all shadow-sm active:scale-[0.98] cursor-pointer"
            >
              {isLoading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Creating account…</>
              ) : (
                <>Create Lipi account <ArrowRight className="w-4 h-4" /></>
              )}
            </button>
          </form>

          <p className="mt-5 text-center text-[11px] text-slate-400 leading-relaxed">
            By registering you agree to our{' '}
            <Link to="/privacy" className="text-slate-500 underline hover:text-primary transition-colors">Privacy Policy</Link>.
            {' '}Patient audio is never stored permanently.
          </p>
        </motion.div>
      </div>
    </div>
  );
}
