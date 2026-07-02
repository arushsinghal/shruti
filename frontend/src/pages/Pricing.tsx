import { useState, type MouseEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, useReducedMotion, AnimatePresence } from 'framer-motion';
import { ArrowRight, Check, Sparkles, Plus, Minus, TrendingUp, Zap, IndianRupee } from 'lucide-react';
import { CursorSpotlight, AuroraBackdrop } from '../components/Ambient';

interface Tier {
  name: string;
  tagline: string;
  price: string;
  unit: string;
  highlight?: boolean;
  cta: string;
  note?: string;
  features: string[];
}

const TIERS: Tier[] = [
  {
    name: 'Pay-as-you-go',
    tagline: 'For solo doctors trying Lipi',
    price: '₹100',
    unit: 'per consultation',
    cta: 'Start free',
    features: [
      'Voice → reviewed SOAP note',
      'Evidence-backed fact extraction',
      'Prescription & investigation orders',
      'ABDM FHIR R4 export (DHIS-ready)',
    ],
  },
  {
    name: 'Clinic Pro',
    tagline: 'Net cost: ₹0 after DHIS income',
    price: '₹1,499',
    unit: 'per doctor / month',
    highlight: true,
    cta: 'Start 14-day trial',
    note: 'DHIS deposits ₹9,000+/mo to your clinic — more than covers this fee.',
    features: [
      'Unlimited consultations',
      'Auto DHIS claim logging — ₹7.50/OPD monthly from NHA',
      'WhatsApp follow-up reminders to patients',
      'Lab dispatch — Thyrocare & 1mg booking links',
      'Consultation fee collection via UPI deep-link',
      'ABDM FHIR R4 + HIE-CM push (Cat1 & Cat2)',
      'Assistant work queue & patient timeline',
      'Learns your clinic workflow over time',
    ],
  },
  {
    name: 'Hospital / Chain',
    tagline: 'For multi-doctor practices',
    price: 'Custom',
    unit: 'volume pricing',
    cta: 'Talk to us',
    features: [
      'Everything in Clinic Pro',
      'Multi-doctor admin console',
      'Zero-friction lab & payment rails',
      'NHCX pre-auth & insurance integration',
      'Dedicated onboarding & SLA',
      'On-shore data residency',
    ],
  },
];

const REVENUE_STREAMS = [
  {
    icon: <IndianRupee className="w-5 h-5" />,
    label: 'DHIS government payout',
    detail: '₹7.50 per OPD · ₹15 per discharge — deposited by NHA monthly',
    color: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  },
  {
    icon: <TrendingUp className="w-5 h-5" />,
    label: 'Lab affiliate commission',
    detail: 'Thyrocare & 1mg — per booking completed via Lipi dispatch',
    color: 'bg-sky-50 text-sky-700 border-sky-200',
  },
  {
    icon: <Zap className="w-5 h-5" />,
    label: 'Consultation fee settlement',
    detail: 'UPI deep-link sent to patient when appointment is confirmed',
    color: 'bg-violet-50 text-violet-700 border-violet-200',
  },
  {
    icon: <Check className="w-5 h-5" />,
    label: 'NHCX insurance pre-auth',
    detail: 'Cashless claim filing — coming soon',
    color: 'bg-amber-50 text-amber-700 border-amber-200',
  },
];

const INCLUDED = [
  { task: 'Clinical notes', detail: 'Written as you speak' },
  { task: 'Prescriptions', detail: 'Drafted, ready to sign' },
  { task: 'Patient follow-ups', detail: 'Automated WhatsApp reminders' },
  { task: 'Lab orders', detail: 'Dispatched directly to patient' },
  { task: 'Payment collection', detail: 'UPI link after appointment confirm' },
  { task: 'ABDM records', detail: 'FHIR R4 auto-filed, DHIS claimed' },
];

const FAQS: { q: string; a: string }[] = [
  {
    q: 'What is DHIS and why does the government pay us?',
    a: 'The Digital Health Incentive Scheme (DHIS) is an NHA program that pays clinics ₹7.50 per OPD (₹15 for discharges) for every record digitized via ABDM-compliant software. Lipi is built as a registered Digital Solution Company (DSC), so both you and Lipi earn from the government every month — no extra work required.',
  },
  {
    q: 'How does the "net cost ₹0" work?',
    a: '40 patients/day × ₹7.50 × 22 working days = ₹6,600/month deposited by NHA into your clinic account. Lipi Pro is ₹1,499/month. You\'re up ₹5,100 just from DHIS — before anything else. At volume, one doctor\'s DHIS income covers multiple seats.',
  },
  {
    q: 'Is Lipi just an AI scribe?',
    a: 'No. The scribe is the entry point. Lipi is an AI-native healthcare service — from one consultation it produces reviewed records, prescriptions, referrals, investigation orders, patient follow-ups, payment collection, and the ABDM records that trigger your government income. All from speech.',
  },
  {
    q: 'How does "zero hallucination" work?',
    a: 'Extraction from speech to clinical facts is fully deterministic — no LLM. Every fact traces to the exact sentence the doctor spoke. The SOAP note stays empty until the doctor confirms facts in one tap. AI only ever operates on confirmed ground truth.',
  },
  {
    q: 'What is the lock-in risk if I switch EMRs?',
    a: 'If you switch to a non-DSC EMR, your clinic loses DHIS income entirely — even at 200 patients/day. NHA only pays when the software filing records is ABDM v3 DSC-registered. This is not our lock-in — it is the government\'s incentive structure.',
  },
  {
    q: 'Which languages does Lipi support?',
    a: 'Hindi, English, and Hinglish code-switching — built for how Indian OPDs actually speak, including self-corrections and regional vocabulary.',
  },
  {
    q: 'Is patient data secure?',
    a: 'Audio is processed by an India-based speech-to-text provider only after explicit consent. Transcript identifiers are scrubbed before storage. Raw audio is deleted after transcription. Records are ABDM-compliant HL7 FHIR R4.',
  },
];

export default function Pricing() {
  const navigate = useNavigate();
  const reduce = useReducedMotion();
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  const navLink = 'text-[13.5px] font-medium text-slate-500 hover:text-primary transition-colors cursor-pointer';
  const goHome = (e: MouseEvent, hash?: string) => {
    e.preventDefault();
    navigate(hash ? `/${hash}` : '/');
  };

  return (
    <div className="min-h-screen bg-bg-warm font-sans text-text-dark antialiased overflow-x-hidden">
      <CursorSpotlight />

      {/* Nav */}
      <nav className="w-full sticky top-0 z-[100] bg-white/80 backdrop-blur-md border-b border-slate-200/70">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between gap-4">
          <button className="flex items-center gap-2.5 cursor-pointer group" onClick={() => navigate('/')}>
            <span className="grid place-items-center w-9 h-9 rounded-xl bg-primary text-white font-bold text-base shadow-sm group-hover:scale-105 transition-transform">श</span>
            <span className="text-[17px] font-bold text-text-dark tracking-tight">Lipi</span>
          </button>
          <div className="hidden md:flex items-center gap-7">
            <a href="/#usecases" onClick={(e) => goHome(e, '#usecases')} className={navLink}>Product</a>
            <a href="/#platform" onClick={(e) => goHome(e, '#platform')} className={navLink}>How It Works</a>
            <span className="text-[13.5px] font-semibold text-primary">Pricing</span>
            <a href="/#safety" onClick={(e) => goHome(e, '#safety')} className={navLink}>Safety</a>
          </div>
          <button
            onClick={() => navigate('/dashboard')}
            className="text-[13.5px] font-semibold bg-primary hover:bg-primary-dark text-white pl-4 pr-3.5 py-2 rounded-full transition-all active:scale-95 flex items-center gap-1.5 cursor-pointer shadow-sm"
          >
            Open Lipi <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative px-6 pt-20 pb-12 text-center overflow-hidden">
        <AuroraBackdrop />
        <motion.div
          initial={reduce ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="max-w-3xl mx-auto"
        >
          <span className="inline-flex items-center gap-2 rounded-full border border-primary/15 bg-primary/5 px-3.5 py-1.5 text-[12.5px] font-medium text-primary mb-6">
            <Sparkles className="w-3.5 h-3.5" /> Government pays both you and us, monthly
          </span>
          <h1 className="text-[2.5rem] leading-[1.05] md:text-[3.5rem] md:leading-[1.03] tracking-tight font-bold">
            Lipi pays for itself.
            <span className="text-gradient-brand"> Government money, deposited monthly.</span>
          </h1>
          <p className="mt-6 text-[16px] md:text-[18px] text-slate-500 max-w-2xl mx-auto leading-relaxed">
            The NHA Digital Health Incentive Scheme pays your clinic ₹7.50 per OPD visit for every digitized record. 40 patients/day = ₹9,240/month new income. Lipi handles the filing. You collect the deposit.
          </p>
        </motion.div>
      </section>

      {/* DHIS Math Banner */}
      <section className="px-6 pb-10">
        <div className="max-w-4xl mx-auto grid sm:grid-cols-3 gap-4">
          {[
            { label: 'Clinic earns (40 OPDs/day)', value: '₹9,000', sub: '/month · direct from NHA', green: true },
            { label: 'Lipi earns (DSC share)', value: '₹3,000', sub: '/month · 25% of DHIS pool', primary: true },
            { label: 'Net cost to clinic', value: '₹0', sub: 'DHIS income > Lipi subscription', dark: true },
          ].map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={reduce ? false : { opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.07 }}
              className="rounded-2xl bg-white border border-slate-200/80 px-5 py-5 flex flex-col gap-1"
            >
              <p className="text-[11.5px] font-semibold text-slate-500 uppercase tracking-wider">{stat.label}</p>
              <p className={`text-[2rem] font-bold tracking-tight leading-none ${stat.green ? 'text-emerald-600' : stat.primary ? 'text-primary' : 'text-slate-800'}`}>{stat.value}</p>
              <p className="text-[12px] text-slate-400">{stat.sub}</p>
            </motion.div>
          ))}
        </div>
        <p className="text-center text-[12px] text-slate-400 mt-4 max-w-xl mx-auto">Based on 40 OPD/day × ₹7.50 × 22 working days. First 100 transactions/month per facility unpaid (NHA threshold). Actual deposits vary by volume.</p>
      </section>

      {/* Pricing tiers */}
      <section className="px-6 pb-8">
        <div className="max-w-6xl mx-auto grid md:grid-cols-3 gap-5 items-start">
          {TIERS.map((tier, i) => (
            <motion.div
              key={tier.name}
              initial={reduce ? false : { opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              className={`relative rounded-3xl p-7 transition-all ${
                tier.highlight
                  ? 'bg-primary text-white shadow-[0_30px_70px_-30px_rgba(27,94,59,0.6)] md:-translate-y-3 ring-1 ring-primary'
                  : 'bg-white border border-slate-200/80 hover:border-primary/30 hover:shadow-[0_24px_50px_-30px_rgba(27,94,59,0.3)]'
              }`}
            >
              {tier.highlight && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-accent text-text-dark text-[10.5px] font-bold uppercase tracking-wider px-3 py-1 rounded-full shadow-sm">
                  Most popular
                </span>
              )}
              <h3 className={`text-[15px] font-bold ${tier.highlight ? 'text-white' : 'text-text-dark'}`}>{tier.name}</h3>
              <p className={`text-[13px] mt-1 ${tier.highlight ? 'text-white/70' : 'text-slate-500'}`}>{tier.tagline}</p>

              <div className="mt-5 flex items-baseline gap-1.5">
                <span className={`text-[2.5rem] font-bold leading-none tracking-tight ${tier.highlight ? 'text-white' : 'text-text-dark'}`}>{tier.price}</span>
                <span className={`text-[13px] ${tier.highlight ? 'text-white/70' : 'text-slate-400'}`}>{tier.unit}</span>
              </div>

              {tier.note && (
                <p className={`mt-2 text-[11.5px] leading-snug ${tier.highlight ? 'text-white/60' : 'text-slate-400'}`}>{tier.note}</p>
              )}

              <button
                onClick={() => navigate(tier.name === 'Hospital / Chain' ? '/' : '/dashboard')}
                className={`mt-6 w-full py-3 rounded-full font-semibold text-[14px] transition-all active:scale-[0.98] cursor-pointer flex items-center justify-center gap-1.5 ${
                  tier.highlight
                    ? 'bg-white text-primary hover:bg-slate-50 shadow-sm'
                    : 'bg-primary text-white hover:bg-primary-dark shadow-sm'
                }`}
              >
                {tier.cta} <ArrowRight className="w-4 h-4" />
              </button>

              <ul className="mt-7 space-y-3">
                {tier.features.map((f) => (
                  <li key={f} className="flex items-start gap-2.5">
                    <span className={`mt-0.5 grid place-items-center w-4 h-4 rounded-full shrink-0 ${tier.highlight ? 'bg-white/20' : 'bg-primary/10'}`}>
                      <Check className={`w-2.5 h-2.5 ${tier.highlight ? 'text-white' : 'text-primary'}`} strokeWidth={3} />
                    </span>
                    <span className={`text-[13.5px] leading-snug ${tier.highlight ? 'text-white/90' : 'text-slate-600'}`}>{f}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
        <p className="text-center text-[12.5px] text-slate-400 mt-6">All plans include zero-hallucination extraction, doctor review, and ABDM-ready exports. Prices in INR, exclusive of GST. DHIS income credited separately by NHA.</p>
      </section>

      {/* Revenue streams */}
      <section className="px-6 py-20">
        <div className="max-w-5xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-10">
            <span className="text-[12.5px] font-bold uppercase tracking-wider text-primary">Multiple income streams</span>
            <h2 className="text-3xl md:text-[2.25rem] font-bold tracking-tight mt-3 leading-tight">Lipi opens revenue channels you didn't have before.</h2>
            <p className="text-slate-500 text-[15px] mt-3 leading-relaxed">Every consultation produces not just a note — it produces a government payout, a lab referral, and an opportunity to collect your fee before the patient leaves.</p>
          </div>
          <div className="grid sm:grid-cols-2 gap-4">
            {REVENUE_STREAMS.map((stream, i) => (
              <motion.div
                key={stream.label}
                initial={reduce ? false : { opacity: 0, y: 14 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.06 }}
                className={`flex items-start gap-4 rounded-2xl border px-5 py-4 ${stream.color}`}
              >
                <span className="mt-0.5 shrink-0">{stream.icon}</span>
                <div>
                  <p className="text-[14px] font-semibold leading-tight">{stream.label}</p>
                  <p className="text-[12.5px] opacity-70 mt-0.5">{stream.detail}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* What it handles */}
      <section className="px-6 pb-20">
        <div className="max-w-5xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-10">
            <span className="text-[12.5px] font-bold uppercase tracking-wider text-primary">Around every visit</span>
            <h2 className="text-3xl md:text-[2.25rem] font-bold tracking-tight mt-3 leading-tight">Everything around the visit, handled.</h2>
            <p className="text-slate-500 text-[15px] mt-3 leading-relaxed">From one spoken consultation, Lipi handles the full administrative tail — so you see more patients without adding to your team.</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {INCLUDED.map((r, i) => (
              <motion.div
                key={r.task}
                initial={reduce ? false : { opacity: 0, y: 14 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.05 }}
                className="flex items-center gap-3 rounded-2xl bg-white border border-slate-200/80 px-4 py-3.5"
              >
                <span className="grid place-items-center w-7 h-7 rounded-lg bg-primary/10 shrink-0"><Check className="w-3.5 h-3.5 text-primary" strokeWidth={3} /></span>
                <div>
                  <p className="text-[13.5px] font-semibold text-slate-700 leading-tight">{r.task}</p>
                  <p className="text-[12px] text-slate-400">{r.detail}</p>
                </div>
              </motion.div>
            ))}
          </div>
          <div className="mt-6 rounded-2xl bg-primary/[0.05] border border-primary/15 px-6 py-5 text-center">
            <p className="text-[15px] text-slate-600 leading-relaxed"><span className="font-semibold text-text-dark">The government pays both of you.</span> But only if your software is ABDM v3 DSC-certified. A clinic that switches to an uncertified EMR loses their DHIS income entirely — the lock-in is structural, not UX.</p>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="px-6 pb-20">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl md:text-[2.25rem] font-bold tracking-tight text-center mb-10 leading-tight">Questions, answered.</h2>
          <div className="space-y-3">
            {FAQS.map((faq, i) => (
              <div key={faq.q} className="rounded-2xl bg-white border border-slate-200/80 overflow-hidden">
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full flex items-center justify-between gap-4 px-5 py-4 text-left cursor-pointer"
                >
                  <span className="text-[14.5px] font-semibold text-text-dark">{faq.q}</span>
                  <span className="shrink-0 grid place-items-center w-6 h-6 rounded-full bg-primary/10 text-primary">
                    {openFaq === i ? <Minus className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
                  </span>
                </button>
                <AnimatePresence initial={false}>
                  {openFaq === i && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.25, ease: 'easeInOut' }}
                    >
                      <p className="px-5 pb-4 text-[14px] text-slate-500 leading-relaxed">{faq.a}</p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 pb-24">
        <div className="max-w-4xl mx-auto relative overflow-hidden rounded-[2rem] bg-primary px-8 py-16 text-center">
          <div className="absolute inset-0 opacity-[0.12] [background:radial-gradient(40%_60%_at_80%_20%,#fff,transparent_60%)]" />
          <div className="relative z-10 max-w-2xl mx-auto space-y-6">
            <h2 className="text-3xl md:text-[2.5rem] font-bold tracking-tight text-white leading-tight">Start earning from your records today.</h2>
            <p className="text-white/80 text-[15px] leading-relaxed">No card required. Run your first consultation — see a reviewed note, prescription, and DHIS-ready FHIR bundle from one spoken session.</p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
              <button onClick={() => navigate('/dashboard')} className="w-full sm:w-auto px-7 py-3.5 bg-white text-primary hover:bg-slate-50 rounded-full font-semibold text-[14.5px] transition-all active:scale-[0.98] cursor-pointer shadow-lg flex items-center justify-center gap-2">
                Open Lipi <ArrowRight className="w-4 h-4" />
              </button>
              <button onClick={() => navigate('/')} className="w-full sm:w-auto px-7 py-3.5 bg-primary-dark/40 hover:bg-primary-dark/60 text-white border border-white/20 rounded-full font-semibold text-[14.5px] transition-all active:scale-[0.98] cursor-pointer">
                Back to home
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-10 text-center text-[12px] text-slate-400 border-t border-slate-200/70 space-y-2">
        <div className="flex items-center justify-center gap-2 mb-1">
          <span className="grid place-items-center w-6 h-6 rounded-lg bg-primary/10 text-primary font-bold text-xs">श</span>
          <span className="text-[13px] font-bold text-slate-600">Lipi</span>
        </div>
        <p>© 2026 Lipi · AI-native healthcare service for India</p>
        <p><a href="/privacy" className="underline hover:text-primary transition-colors">Privacy Policy</a></p>
      </footer>
    </div>
  );
}
