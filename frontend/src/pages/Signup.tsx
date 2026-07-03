import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../lib/api';

const SPECIALTIES = [
  'General Practitioner', 'Internal Medicine', 'Cardiology', 'Neurology',
  'Orthopaedics', 'Gynaecology & Obstetrics', 'Paediatrics', 'Dermatology',
  'ENT', 'Ophthalmology', 'Psychiatry', 'General Surgery', 'Other',
];

export default function Signup() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    full_name: '', username: '', email: '', password: '', specialty: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    if (!form.full_name || !form.username || !form.email || !form.password) {
      setError('All fields are required.');
      return;
    }
    if (form.password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }
    setLoading(true);
    try {
      await api.post('/auth/register', {
        username: form.username,
        email: form.email,
        password: form.password,
        full_name: form.full_name,
        role: 'doctor',
      });
      // Auto-login after signup
      const tokenResp = await api.post('/auth/token',
        new URLSearchParams({ username: form.username, password: form.password }),
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
      );
      localStorage.setItem('token', tokenResp.data.access_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Sign-up failed. Try a different username.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <span className="text-xl font-bold text-slate-900">Lipi</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Start your free trial</h1>
          <p className="text-slate-500 text-sm mt-1">5 sessions free · No credit card required</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[12px] font-semibold text-slate-500 mb-1.5 uppercase tracking-wide">Full name</label>
              <input
                value={form.full_name} onChange={set('full_name')}
                placeholder="Dr. Priya Sharma"
                className="w-full border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[12px] font-semibold text-slate-500 mb-1.5 uppercase tracking-wide">Username</label>
                <input
                  value={form.username} onChange={set('username')}
                  placeholder="drpriya" autoCapitalize="none"
                  className="w-full border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all"
                />
              </div>
              <div>
                <label className="block text-[12px] font-semibold text-slate-500 mb-1.5 uppercase tracking-wide">Password</label>
                <input
                  type="password" value={form.password} onChange={set('password')}
                  placeholder="Min. 6 chars"
                  className="w-full border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all"
                />
              </div>
            </div>
            <div>
              <label className="block text-[12px] font-semibold text-slate-500 mb-1.5 uppercase tracking-wide">Email</label>
              <input
                type="email" value={form.email} onChange={set('email')}
                placeholder="you@hospital.com"
                className="w-full border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all"
              />
            </div>
            <div>
              <label className="block text-[12px] font-semibold text-slate-500 mb-1.5 uppercase tracking-wide">Specialty</label>
              <select
                value={form.specialty} onChange={set('specialty')}
                className="w-full border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm text-slate-900 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all bg-white"
              >
                <option value="">Select specialty</option>
                {SPECIALTIES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-[13px] rounded-lg px-4 py-3">
                {error}
              </div>
            )}

            <button
              type="submit" disabled={loading}
              className="w-full bg-primary hover:bg-primary-dark disabled:opacity-50 text-white font-semibold py-3 rounded-xl transition-all active:scale-[0.98] mt-2"
            >
              {loading ? 'Creating account…' : 'Create free account'}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-slate-100 text-center">
            <p className="text-[13px] text-slate-500">
              Already have an account?{' '}
              <Link to="/login" className="text-primary font-semibold hover:underline">Sign in</Link>
            </p>
          </div>
        </div>

        {/* Trust strip */}
        <div className="mt-6 flex items-center justify-center gap-6 text-[12px] text-slate-400">
          <span className="flex items-center gap-1">
            <svg className="w-3.5 h-3.5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            5 sessions free
          </span>
          <span className="flex items-center gap-1">
            <svg className="w-3.5 h-3.5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            No card required
          </span>
          <span className="flex items-center gap-1">
            <svg className="w-3.5 h-3.5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            Cancel anytime
          </span>
        </div>
      </div>
    </div>
  );
}
