import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import { Zap, ArrowRight, ShieldCheck, AlertCircle, Check, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { CursorSpotlight, AuroraBackdrop } from '../components/Ambient';
import api from '../lib/api';

const TRUST = ['Audit Trail Enabled', 'Local NLP', 'On-Shore ASR', 'No LLM Hallucination'];
const VALUE_PROPS = [
  'One consultation → reviewed notes, Rx, orders & follow-ups',
  'Every clinical fact traces to the transcript — zero hallucination',
  'Hindi · English · Hinglish, built for Indian OPDs',
];

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const reduce = useReducedMotion();

  const handleLogin = async (user: string, pass: string) => {
    setError('');
    setIsLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append('username', user);
      formData.append('password', pass);

      const response = await api.post('/auth/token', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      login(response.data.access_token);
      const role: string = response.data.role ?? 'doctor';
      navigate(role === 'assistant' ? '/assistant' : '/dashboard');
    } catch (err: any) {
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.message) {
        setError("Network error: " + err.message);
      } else {
        setError('Invalid username or password');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleLogin(username, password);
  };

  const handleDemoLogin = () => {
    setUsername('arush');
    setPassword('1234');
    handleLogin('arush', '1234');
  };

  const handleAssistantDemoLogin = () => {
    setUsername('meena');
    setPassword('1234');
    handleLogin('meena', '1234');
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
          <div className="aurora-blob aurora-2 w-[28rem] h-[28rem] bottom-[-8rem] right-[-6rem] bg-accent/25" />
          <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.04)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.04)_1px,transparent_1px)] bg-[size:26px_26px] [mask-image:radial-gradient(ellipse_70%_60%_at_30%_30%,#000,transparent)]" />
        </div>

        <div className="relative z-10 flex items-center gap-2.5">
          <span className="grid place-items-center w-10 h-10 rounded-xl bg-white/15 backdrop-blur text-white font-bold text-lg ring-1 ring-white/20">श</span>
          <span className="text-[18px] font-bold text-white tracking-tight">Lipi</span>
        </div>

        <motion.div
          initial={reduce ? false : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="relative z-10 max-w-md"
        >
          <h1 className="text-[2.5rem] leading-[1.08] font-bold text-white tracking-tight">
            A doctor speaks once.<br />
            <span className="text-white/70">Lipi runs the OPD.</span>
          </h1>
          <ul className="mt-8 space-y-3.5">
            {VALUE_PROPS.map((p) => (
              <li key={p} className="flex items-start gap-3 text-white/90 text-[14.5px] leading-snug">
                <span className="mt-0.5 grid place-items-center w-5 h-5 rounded-full bg-white/15 shrink-0">
                  <Check className="w-3 h-3 text-white" strokeWidth={3} />
                </span>
                {p}
              </li>
            ))}
          </ul>
        </motion.div>

        <div className="relative z-10 flex items-center gap-2 text-white/70 text-[12.5px]">
          <ShieldCheck className="w-4 h-4" />
          AI-native healthcare administration · Built for India
        </div>
      </div>

      {/* ── Right form panel ─────────────────────────────────── */}
      <div className="relative flex flex-col justify-center px-6 py-12 sm:px-12">
        <AuroraBackdrop className="lg:hidden opacity-60" />

        <motion.div
          initial={reduce ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="relative z-10 w-full max-w-md mx-auto"
        >
          {/* Mobile logo */}
          <div className="flex lg:hidden items-center justify-center gap-2.5 mb-8">
            <span className="grid place-items-center w-10 h-10 rounded-xl bg-primary text-white font-bold text-lg shadow-sm">श</span>
            <span className="text-[18px] font-bold text-text-dark tracking-tight">Lipi</span>
          </div>

          <div className="mb-7">
            <h2 className="text-[1.75rem] font-bold tracking-tight text-text-dark">Welcome back</h2>
            <p className="text-[14px] text-slate-500 mt-1.5">Sign in to your clinic workspace.</p>
          </div>

          <div className="mb-6 rounded-xl border border-primary/20 bg-primary/5 px-4 py-3.5">
            <p className="text-[13px] text-text-dark leading-relaxed">
              Lipi is currently invite-only for partner clinics.{' '}
              <a
                href="mailto:arushsinghal98@gmail.com?subject=Lipi%20early%20access"
                className="font-semibold text-primary hover:text-primary-dark transition-colors"
              >
                Request early access
              </a>{' '}
              to get set up.
            </p>
          </div>

          {/* Demo login */}
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={handleDemoLogin}
              disabled={isLoading}
              className="flex justify-center items-center gap-1.5 py-3 px-3 rounded-full text-[13px] font-semibold text-white bg-primary hover:bg-primary-dark shadow-[0_8px_24px_-8px_rgba(27,94,59,0.5)] active:scale-[0.98] transition-all disabled:opacity-70 cursor-pointer"
            >
              {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
              Doctor demo
            </button>
            <button
              onClick={handleAssistantDemoLogin}
              disabled={isLoading}
              className="flex justify-center items-center gap-1.5 py-3 px-3 rounded-full text-[13px] font-semibold text-primary bg-primary/8 border border-primary/20 hover:bg-primary/12 active:scale-[0.98] transition-all disabled:opacity-70 cursor-pointer"
            >
              {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
              Assistant demo
            </button>
          </div>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-200" /></div>
            <div className="relative flex justify-center"><span className="px-3 bg-bg-warm text-[12px] text-slate-400">or sign in with credentials</span></div>
          </div>

          <form className="space-y-4" onSubmit={handleSubmit}>
            {error && (
              <div className="flex items-center gap-2 bg-red-50 border border-red-100 text-alert-critical px-4 py-3 rounded-xl text-[13px]">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {error}
              </div>
            )}

            <div>
              <label className="block text-[12px] font-semibold text-slate-600 mb-1.5">Username</label>
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className={inputCls}
                placeholder="Enter your username"
              />
            </div>

            <div>
              <label className="block text-[12px] font-semibold text-slate-600 mb-1.5">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={inputCls}
                placeholder="••••••••"
              />
            </div>

            <div className="flex items-center justify-between pt-0.5">
              <a
                href="mailto:arushsinghal98@gmail.com?subject=Lipi%20early%20access"
                className="text-[13px] font-medium text-primary hover:text-primary-dark transition-colors"
              >
                Request early access
              </a>
              <a href="#" className="text-[13px] font-medium text-slate-400 hover:text-slate-600 transition-colors">
                Forgot password?
              </a>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center items-center gap-1.5 py-3.5 px-4 rounded-full text-[14px] font-semibold text-text-dark bg-white border border-slate-200 hover:border-primary/30 hover:bg-slate-50 active:scale-[0.98] transition-all disabled:opacity-50 cursor-pointer"
            >
              Sign in manually
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Trust badges */}
          <div className="mt-8 flex items-center justify-center gap-x-2 gap-y-2 flex-wrap">
            {TRUST.map((label) => (
              <span key={label} className="text-[10px] font-bold uppercase tracking-wider text-primary border border-primary/15 bg-primary/5 px-2.5 py-1 rounded-full">
                {label}
              </span>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
