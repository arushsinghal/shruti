import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';

interface BillingStatus {
  plan: 'trial' | 'paid';
  trial_sessions_used: number;
  trial_limit: number;
  sessions_left: number | null;
  paid_until: string | null;
  razorpay_page_id: string;
  price_rupees: number;
  can_create_session: boolean;
}

export default function Billing() {
  const navigate = useNavigate();
  const [status, setStatus] = useState<BillingStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/billing/status').then(r => setStatus(r.data)).finally(() => setLoading(false));
  }, []);

  const isPaid = status?.plan === 'paid';
  const pct = status ? Math.min(100, (status.trial_sessions_used / status.trial_limit) * 100) : 0;

  function openRazorpay() {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const base = `https://pages.razorpay.com/${status?.razorpay_page_id}`;
    const params = new URLSearchParams();
    if (user.email) params.set('prefill[email]', user.email);
    if (user.name) params.set('prefill[name]', user.name);
    window.open(`${base}?${params}`, '_blank');
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <button onClick={() => navigate('/dashboard')} className="flex items-center gap-2 text-slate-500 hover:text-slate-900 transition-colors text-sm">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Dashboard
        </button>
        <span className="text-sm font-semibold text-slate-900">Billing & Plan</span>
        <div className="w-20" />
      </div>

      <div className="max-w-lg mx-auto px-4 py-10 space-y-6">
        {/* Plan card */}
        <div className={`rounded-2xl border p-6 ${isPaid ? 'bg-emerald-50 border-emerald-200' : 'bg-white border-slate-200'}`}>
          <div className="flex items-start justify-between mb-4">
            <div>
              <span className={`text-[11px] font-bold uppercase tracking-widest ${isPaid ? 'text-emerald-600' : 'text-slate-500'}`}>
                {isPaid ? 'Pro Plan' : 'Free Trial'}
              </span>
              <h2 className="text-2xl font-bold text-slate-900 mt-0.5">
                {isPaid ? '₹999 / month' : `${status?.sessions_left} sessions left`}
              </h2>
              {isPaid && status?.paid_until && (
                <p className="text-sm text-emerald-700 mt-1">
                  Active until {new Date(status.paid_until).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}
                </p>
              )}
            </div>
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${isPaid ? 'bg-emerald-100' : 'bg-slate-100'}`}>
              {isPaid ? (
                <svg className="w-5 h-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <svg className="w-5 h-5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
            </div>
          </div>

          {!isPaid && (
            <>
              <div className="flex items-center justify-between text-[12px] text-slate-500 mb-1.5">
                <span>Sessions used</span>
                <span className="font-semibold text-slate-700">{status?.trial_sessions_used} / {status?.trial_limit}</span>
              </div>
              <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                <div
                  className={`h-2 rounded-full transition-all ${pct >= 80 ? 'bg-amber-500' : 'bg-primary'}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </>
          )}
        </div>

        {/* Feature list */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          <h3 className="text-[13px] font-bold text-slate-900 mb-4">What's included in Pro</h3>
          <ul className="space-y-3">
            {[
              'Unlimited sessions',
              'AI SOAP notes (Gemini-enhanced)',
              'Prescription PDF generation',
              'Referral letters',
              'TPA insurance claim package',
              'OPD register PDF (MCI format)',
              'WhatsApp patient intake',
              'Legal export (court-admissible)',
              'Learning engine — AI improves with your practice',
            ].map(f => (
              <li key={f} className="flex items-center gap-2.5 text-sm text-slate-700">
                <svg className="w-4 h-4 text-emerald-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                {f}
              </li>
            ))}
          </ul>
        </div>

        {/* CTA */}
        {!isPaid && (
          <div className="space-y-3">
            <button
              onClick={openRazorpay}
              className="w-full bg-primary hover:bg-primary-dark text-white font-bold py-4 rounded-xl text-[15px] transition-all active:scale-[0.98] shadow-sm"
            >
              Upgrade to Pro — ₹{status?.price_rupees}/month
            </button>
            <p className="text-center text-[12px] text-slate-400">
              Secure payment via Razorpay · Cancel anytime · Instant activation
            </p>
          </div>
        )}

        {isPaid && (
          <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 text-center">
            <p className="text-sm text-slate-500">Need to cancel or have a billing question?</p>
            <a href="mailto:support@lipi.health" className="text-primary text-sm font-semibold hover:underline">
              support@lipi.health
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
