import { useState, useRef, useEffect, type MouseEvent } from 'react';
import type { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  motion,
  useReducedMotion,
  useInView,
  useScroll,
  useTransform,
  useSpring,
} from 'framer-motion';
import {
  ArrowRight,
  FileText,
  Receipt,
  MessageSquare,
  FlaskConical,
  CreditCard,
  Database,
  Mic,
  Cpu,
  Activity,
  IndianRupee,
  ShieldCheck,
  BadgeCheck,
} from 'lucide-react';
import { ProductShowcase } from '../components/ProductShowcase';
import SupportModal from '../components/SupportModal';

// ── Animation variants ────────────────────────────────────────────────────────
const fadeUp = {
  hidden: { opacity: 0, y: 48 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.75, ease: [0.16, 1, 0.3, 1] as const },
  },
};

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.09, delayChildren: 0.05 } },
};

const EASE_OUT = [0.76, 0, 0.24, 1] as const;

// ── Per-line clip reveal (Antigravity signature) ──────────────────────────────
// The IntersectionObserver MUST watch the un-clipped outer wrapper — watching the
// translated inner element reports 0% intersection forever (it's clipped away).
// `immediate` plays on mount for above-the-fold use.
function RevealLine({
  children,
  delay = 0,
  immediate = false,
}: {
  children: ReactNode;
  delay?: number;
  immediate?: boolean;
}) {
  const reduce = useReducedMotion();
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, amount: 0.3 });
  const show = immediate || inView;
  return (
    <div ref={ref} className="overflow-hidden pb-[0.14em]">
      <motion.div
        initial={reduce ? false : { y: '115%' }}
        animate={reduce ? { y: 0 } : { y: show ? 0 : '115%' }}
        transition={{ duration: 0.82, delay, ease: EASE_OUT }}
      >
        {children}
      </motion.div>
    </div>
  );
}

// ── Section heading that reliably reveals on scroll ───────────────────────────
function RevealHeading({
  children,
  className = '',
  wrapClassName = '',
}: {
  children: ReactNode;
  className?: string;
  wrapClassName?: string;
}) {
  const reduce = useReducedMotion();
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, amount: 0.3 });
  return (
    <div ref={ref} className={`overflow-hidden pb-[0.14em] ${wrapClassName}`}>
      <motion.h2
        initial={reduce ? false : { y: '115%' }}
        animate={reduce ? { y: 0 } : { y: inView ? 0 : '115%' }}
        transition={{ duration: 0.82, ease: EASE_OUT }}
        className={className}
      >
        {children}
      </motion.h2>
    </div>
  );
}

// ── Refined eyebrow label: accent rule + tracked caps ─────────────────────────
function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -14 }}
      whileInView={{ opacity: 1, x: 0 }}
      viewport={{ once: true, amount: 0.6 }}
      transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] as const }}
      className="flex items-center gap-3 mb-5"
    >
      <span className="h-px w-9 bg-gradient-to-r from-primary to-primary/20" />
      <span className="text-[12px] font-bold uppercase tracking-[0.22em] text-primary">{children}</span>
    </motion.div>
  );
}

// ── Count-up number ───────────────────────────────────────────────────────────
function CountUp({ to, suffix = '' }: { to: number; suffix?: string }) {
  const reduce = useReducedMotion();
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: '-60px' });
  const [val, setVal] = useState(reduce ? to : 0);

  useEffect(() => {
    if (reduce || !inView) return;
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const p = Math.min((now - start) / 1600, 1);
      setVal(Math.round((1 - Math.pow(1 - p, 3)) * to));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [inView, reduce, to]);

  return <span ref={ref}>{val}{suffix}</span>;
}

// ── Data ──────────────────────────────────────────────────────────────────────
const DIALECT_SAMPLES = {
  hinglish: {
    speech: 'Patient ko bukhar hai, around 102, but no chest pain, no vomiting... actually wait, usne kaha thoda dard hai.',
    entities: { symptoms: ['Fever (bukhar)', 'Pain (dard)'], vitals: ['Temp 102°F'], negated: ['Chest Pain', 'Vomiting'] },
    resolution: "Resolved conversational self-correction — overrode pain-free state with 'mild pain' and mapped colloquial terms ('bukhar', 'dard') to standard clinical classifications.",
  },
  hindi: {
    speech: 'मरीज को तीन दिन से खांसी है, और सर में भी तेज दर्द है। उल्टी नहीं हुई है।',
    entities: { symptoms: ['Cough (खांसी)', 'Headache (सर दर्द)'], vitals: ['Duration: 3 days'], negated: ['Vomiting (उल्टी)'] },
    resolution: "Parsed Hindi script, identified duration modifier ('तीन दिन' = 3 days), extracted symptoms, filtered negated symptom ('उल्टी नहीं' = No vomiting).",
  },
  english: {
    speech: 'Patient complains of severe chest pain spreading to left arm since 1 hour. No dizziness.',
    entities: { symptoms: ['Chest Pain (radiating)', 'Arm Pain'], vitals: ['Duration: 1 hour'], negated: ['Dizziness'] },
    resolution: 'Extracted entities, mapped radiating symptom path, filtered negated dizziness, flagged potential cardiovascular check.',
  },
} as const;
type LangKey = keyof typeof DIALECT_SAMPLES;

const TASKS = [
  { icon: FileText, label: 'Clinical notes', detail: 'Written as you speak' },
  { icon: Receipt, label: 'Prescriptions', detail: 'Drafted, ready to sign' },
  { icon: MessageSquare, label: 'Patient instructions', detail: 'Sent on WhatsApp' },
  { icon: FlaskConical, label: 'Lab orders', detail: 'Generated and dispatched' },
  { icon: CreditCard, label: 'Payments', detail: 'UPI links and tokens' },
  { icon: Database, label: 'ABDM / FHIR', detail: 'Records auto-filled' },
];

const TESTIMONIALS = [
  {
    quote: "I see 60 patients a day. Lipi cut my post-OPD documentation from two hours to under twenty minutes. The notes are already in the right format.",
    name: 'Dr. Anjali Mehra',
    role: 'Senior Consultant, Internal Medicine',
    location: 'Medanta, Gurugram',
  },
  {
    quote: "It catches things I say in passing — a medication I mention while examining, a follow-up I didn't write down. Everything ends up in the note.",
    name: 'Dr. Rahul Bansal',
    role: 'Neurologist',
    location: 'Fortis Hospital, Delhi',
  },
  {
    quote: "My assistants now get a WhatsApp task list before the patient leaves. Lab dispatch, payment token, next appointment — Lipi queues all of it.",
    name: 'Dr. Priya Nair',
    role: 'Gynaecologist',
    location: 'Private Clinic, Kochi',
  },
];

// ── Page ──────────────────────────────────────────────────────────────────────
export default function Landing() {
  const navigate = useNavigate();
  const reduce = useReducedMotion();
  const [activeTab, setActiveTab] = useState<LangKey>('hinglish');
  const [showSupportModal, setShowSupportModal] = useState(false);

  const handleNavClick = (e: MouseEvent<HTMLAnchorElement>, id: string) => {
    e.preventDefault();
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  // Hero parallax
  const { scrollY } = useScroll();
  const rawHeroY = useTransform(scrollY, [0, 600], [0, -90]);
  const heroY = useSpring(rawHeroY, { stiffness: 60, damping: 20 });
  const heroOpacity = useTransform(scrollY, [0, 400], [1, 0]);
  const rawShowcaseY = useTransform(scrollY, [0, 600], [0, -50]);
  const showcaseY = useSpring(rawShowcaseY, { stiffness: 60, damping: 20 });

  return (
    <div className="min-h-screen bg-bg-warm text-text-dark font-sans antialiased overflow-x-hidden selection:bg-primary/15">
      <SupportModal isOpen={showSupportModal} onClose={() => setShowSupportModal(false)} />

      {/* ── Nav ─────────────────────────────────────────────────────── */}
      <motion.nav
        initial={{ opacity: 0, y: -14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] as const }}
        className="sticky top-0 z-[100] border-b border-slate-200/60 bg-bg-warm/85 backdrop-blur-md"
      >
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between gap-4">
          <button
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            className="flex items-center gap-2.5 cursor-pointer group"
          >
            <span className="grid place-items-center w-8 h-8 rounded-xl bg-primary text-white font-bold text-sm shadow-sm group-hover:scale-105 transition-transform">श</span>
            <span className="text-[17px] font-bold tracking-tight text-text-dark">Lipi</span>
          </button>

          <div className="hidden md:flex items-center gap-6">
            {[['how', 'How it works'], ['revenue', 'Revenue'], ['languages', 'Languages']].map(([id, label]) => (
              <a key={id} href={`#${id}`} onClick={(e) => handleNavClick(e as MouseEvent<HTMLAnchorElement>, id)}
                className="text-[13.5px] font-medium text-slate-500 hover:text-primary transition-colors cursor-pointer">{label}</a>
            ))}
            <button onClick={() => navigate('/research')} className="text-[13.5px] font-medium text-slate-500 hover:text-primary transition-colors cursor-pointer">Research</button>
          </div>

          <div className="flex items-center gap-2">
            <button onClick={() => setShowSupportModal(true)} className="hidden md:block text-[13.5px] font-medium text-slate-500 hover:text-primary px-3 py-2 transition-colors cursor-pointer">Contact</button>
            <button onClick={() => navigate('/dashboard')} className="hidden sm:block text-[13.5px] font-medium text-slate-500 hover:text-primary px-3 py-2 transition-colors cursor-pointer">Open Lipi</button>
            <motion.a
              href="mailto:arushsinghal98@gmail.com?subject=Lipi%20early%20access"
              whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
              className="text-[13.5px] font-semibold bg-primary hover:bg-primary-dark text-white pl-4 pr-3.5 py-2 rounded-full flex items-center gap-1.5 cursor-pointer transition-colors shadow-sm"
            >
              Request early access <ArrowRight className="w-4 h-4" />
            </motion.a>
          </div>
        </div>
      </motion.nav>

      {/* ── Hero ────────────────────────────────────────────────────── */}
      <section className="relative min-h-[calc(100dvh-4rem)] bg-bg-warm flex items-center overflow-hidden">
        {/* Subtle dotted backdrop + soft brand glow fill the negative space */}
        <div className="absolute inset-0 bg-dot-fade pointer-events-none" aria-hidden />
        <div className="absolute -top-32 -left-40 w-[620px] h-[620px] rounded-full bg-primary/[0.05] blur-[130px] pointer-events-none" aria-hidden />
        <div className="absolute top-1/3 right-[-10%] w-[520px] h-[520px] rounded-full bg-accent/[0.05] blur-[130px] pointer-events-none" aria-hidden />

        <div className="relative max-w-7xl mx-auto px-6 w-full grid lg:grid-cols-[1fr_1.08fr] gap-10 lg:gap-12 py-20 items-center">
          {/* Left */}
          <motion.div style={reduce ? {} : { y: heroY, opacity: heroOpacity }} className="max-w-[560px]">
            {/* Badge */}
            <motion.div
              initial={reduce ? false : { opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="inline-flex items-center gap-2 bg-primary/[0.07] border border-primary/20 text-primary text-[11.5px] font-semibold px-3.5 py-1.5 rounded-full mb-8 tracking-wide"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
              ABDM mandated · Government pays ₹20/consult
            </motion.div>

            {/* Headline */}
            <h1 className="text-[3.1rem] md:text-[4.1rem] lg:text-[5rem] leading-[0.97] tracking-[-0.035em] mb-7">
              <RevealLine immediate delay={0.06}>
                <span className="block font-light text-slate-400">A doctor speaks once.</span>
              </RevealLine>
              <RevealLine immediate delay={0.17}>
                <span className="block font-extrabold text-primary">Lipi runs</span>
              </RevealLine>
              <RevealLine immediate delay={0.25}>
                <span className="block font-extrabold text-primary">the OPD.</span>
              </RevealLine>
            </h1>

            <motion.p
              initial={reduce ? false : { opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.45 }}
              className="text-[16px] md:text-[17px] text-slate-500 leading-relaxed mb-8 max-w-[42ch]"
            >
              Voice in. Reviewed note, prescription, lab orders, and follow-up out.
              Before the next patient walks in.
            </motion.p>

            <motion.div
              initial={reduce ? false : { opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.58 }}
              className="flex flex-col sm:flex-row gap-3"
            >
              <motion.button
                onClick={() => navigate('/dashboard')}
                whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                className="px-7 py-3.5 bg-primary hover:bg-primary-dark text-white rounded-full font-bold text-[14.5px] flex items-center justify-center gap-2 transition-colors cursor-pointer shadow-sm"
              >
                Open Lipi <ArrowRight className="w-4 h-4" />
              </motion.button>
              <motion.button
                onClick={() => navigate('/pricing')}
                whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                className="px-7 py-3.5 border border-slate-200 hover:border-slate-300 text-slate-600 hover:text-text-dark rounded-full font-semibold text-[14.5px] transition-all cursor-pointer"
              >
                See pricing
              </motion.button>
            </motion.div>

            <motion.div
              initial={reduce ? false : { opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.75 }}
              className="mt-9 flex flex-wrap items-center gap-5 text-[12px] text-slate-400 font-medium"
            >
              <span className="flex items-center gap-1.5"><BadgeCheck className="w-3.5 h-3.5 text-primary/60" strokeWidth={2} /> ABDM mandated</span>
              <span className="flex items-center gap-1.5"><ShieldCheck className="w-3.5 h-3.5 text-primary/60" strokeWidth={2} /> On-shore NLP</span>
              <span className="flex items-center gap-1.5"><BadgeCheck className="w-3.5 h-3.5 text-primary/60" strokeWidth={2} /> Zero hallucination</span>
            </motion.div>
          </motion.div>

          {/* Right: showcase */}
          <motion.div
            style={reduce ? {} : { y: showcaseY }}
            initial={reduce ? false : { opacity: 0, y: 36, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.9, delay: 0.22, ease: [0.16, 1, 0.3, 1] as const }}
          >
            <ProductShowcase />
          </motion.div>
        </div>
      </section>

      {/* ── Proof numbers ───────────────────────────────────────────── */}
      <section className="border-y border-slate-200/60 bg-white">
        <motion.div
          variants={stagger}
          initial={reduce ? false : 'hidden'}
          whileInView="visible"
          viewport={{ once: true, amount: 0.5 }}
          className="max-w-5xl mx-auto px-6 py-10 grid grid-cols-2 md:grid-cols-4 gap-8 text-center"
        >
          {[
            { to: 71, suffix: '+', label: 'Consultations processed' },
            { to: 100, suffix: '%', label: 'Facts traced to source' },
            { to: 10, suffix: 'h+', label: 'Weekly hours saved' },
            { to: 11, suffix: '+', label: 'Indian languages' },
          ].map((s) => (
            <motion.div key={s.label} variants={fadeUp} className="space-y-1">
              <div className="text-[2.6rem] font-black tracking-tight text-primary tabular-nums leading-none">
                <CountUp to={s.to} suffix={s.suffix} />
              </div>
              <p className="text-[11.5px] text-slate-400 font-medium uppercase tracking-wide mt-2">{s.label}</p>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* ── How it works ────────────────────────────────────────────── */}
      <section id="how" className="py-28 px-6">
        <div className="max-w-6xl mx-auto">
          <Eyebrow>How it works</Eyebrow>
          <RevealHeading wrapClassName="mb-16" className="text-[2.4rem] md:text-[3.2rem] font-extrabold tracking-tight leading-[1.05] text-text-dark">
            One consultation.<br className="hidden md:block" /> The whole OPD handled.
          </RevealHeading>

          <div className="space-y-5">
            {/* Step 1 */}
            <motion.div variants={fadeUp} initial={reduce ? false : 'hidden'} whileInView="visible" viewport={{ once: true, amount: 0.2 }}
              className="grid md:grid-cols-[1fr_1.6fr] gap-6 rounded-3xl border border-slate-200/80 bg-white p-8 md:p-10 items-center">
              <div className="space-y-4">
                <p className="text-[10.5px] font-bold uppercase tracking-[0.18em] text-slate-400">Step 01</p>
                <div className="w-10 h-10 rounded-2xl bg-primary/8 grid place-items-center"><Mic className="w-5 h-5 text-primary" strokeWidth={1.8} /></div>
                <h3 className="text-[1.35rem] font-bold leading-snug">Doctor speaks. Lipi listens.</h3>
                <p className="text-[14px] text-slate-500 leading-relaxed">Dictate in Hindi, Hinglish, or English. No template, no typing. Lipi captures the full consultation in real time.</p>
              </div>
              <div className="bg-slate-50 rounded-2xl p-5 border border-slate-100 font-mono text-[13px] text-slate-600 leading-loose">
                <span className="text-primary font-semibold">Doctor:</span> Teen din se bukhar hai, 102 ke around. Khaansi bhi.
                <span className="block mt-2"><span className="text-primary font-semibold">Patient:</span> Aur thoda chest mein dard bhi hai.</span>
                <span className="block mt-2"><span className="text-primary font-semibold">Doctor:</span> Chest pain nahi? achha. BP — 128/82.</span>
                <span className="block mt-3 text-slate-400 text-[11px] uppercase tracking-wider">Lipi: extracting 4 entities...</span>
              </div>
            </motion.div>

            {/* Step 2 */}
            <motion.div variants={fadeUp} initial={reduce ? false : 'hidden'} whileInView="visible" viewport={{ once: true, amount: 0.18 }}
              className="rounded-3xl border border-primary/20 bg-primary/[0.03] p-8 md:p-10">
              <div className="grid md:grid-cols-[auto_1fr] gap-8 md:gap-12 items-start">
                <div className="space-y-3 md:max-w-[210px]">
                  <p className="text-[10.5px] font-bold uppercase tracking-[0.18em] text-slate-400">Step 02</p>
                  <div className="w-10 h-10 rounded-2xl bg-primary/10 grid place-items-center"><Cpu className="w-5 h-5 text-primary" strokeWidth={1.8} /></div>
                  <h3 className="text-[1.35rem] font-bold leading-snug">Every fact extracted. Traced to source.</h3>
                  <p className="text-[13.5px] text-slate-500 leading-relaxed">Each entity linked to the exact sentence spoken.</p>
                </div>
                <motion.div variants={stagger} initial={reduce ? false : 'hidden'} whileInView="visible" viewport={{ once: true, amount: 0.4 }} className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[
                    { cat: 'SYMPTOM', val: 'Fever · 3 days', src: 'teen din se bukhar', tone: 'green' },
                    { cat: 'VITAL', val: 'BP 128/82', src: '[examines patient]', tone: 'slate' },
                    { cat: 'SYMPTOM', val: 'Cough', src: 'khaansi bhi', tone: 'green' },
                    { cat: 'NEGATED', val: 'Chest Pain', src: 'chest pain nahi?', tone: 'red' },
                  ].map((f) => (
                    <motion.div key={f.val} variants={fadeUp} whileHover={{ y: -3, transition: { duration: 0.2 } }}
                      className={`rounded-2xl border p-4 space-y-1.5 cursor-default ${f.tone === 'green' ? 'bg-primary/5 border-primary/15' : f.tone === 'red' ? 'bg-red-50 border-red-100' : 'bg-white border-slate-200'}`}>
                      <span className={`text-[10px] font-bold uppercase tracking-wider ${f.tone === 'green' ? 'text-primary' : f.tone === 'red' ? 'text-red-500' : 'text-slate-400'}`}>{f.cat}</span>
                      <p className={`text-[13.5px] font-semibold ${f.tone === 'red' ? 'line-through text-slate-400' : 'text-text-dark'}`}>{f.val}</p>
                      <p className="text-[11px] text-slate-400 italic">"{f.src}"</p>
                    </motion.div>
                  ))}
                </motion.div>
              </div>
            </motion.div>

            {/* Step 3 */}
            <motion.div variants={fadeUp} initial={reduce ? false : 'hidden'} whileInView="visible" viewport={{ once: true, amount: 0.15 }}
              className="rounded-3xl border border-slate-200/80 bg-white p-8 md:p-10">
              <div className="flex items-start gap-4 mb-8">
                <div className="w-10 h-10 rounded-2xl bg-accent/10 grid place-items-center flex-shrink-0"><Activity className="w-5 h-5 text-accent-dark" strokeWidth={1.8} /></div>
                <div>
                  <p className="text-[10.5px] font-bold uppercase tracking-[0.18em] text-slate-400 mb-1.5">Step 03</p>
                  <h3 className="text-[1.35rem] font-bold leading-snug">Sign once. Six things happen automatically.</h3>
                  <p className="text-[13.5px] text-slate-500 mt-1">The assistant's queue builds itself.</p>
                </div>
              </div>
              <motion.div variants={stagger} initial={reduce ? false : 'hidden'} whileInView="visible" viewport={{ once: true, amount: 0.3 }} className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {TASKS.map((t, i) => {
                  const featured = i < 2;
                  return (
                    <motion.div key={t.label} variants={fadeUp} whileHover={{ y: -4, transition: { duration: 0.2 } }}
                      className={`rounded-2xl p-5 border flex flex-col gap-3 cursor-default transition-shadow hover:shadow-md ${featured ? 'bg-text-dark border-text-dark' : 'bg-slate-50 border-slate-200/80'}`}>
                      <div className={`w-9 h-9 rounded-xl grid place-items-center ${featured ? 'bg-white/10' : 'bg-white border border-slate-200'}`}>
                        <t.icon className={`w-4 h-4 ${featured ? 'text-white' : 'text-primary'}`} strokeWidth={1.8} />
                      </div>
                      <div>
                        <p className={`text-[13.5px] font-semibold ${featured ? 'text-white' : 'text-text-dark'}`}>{t.label}</p>
                        <p className={`text-[12px] mt-0.5 ${featured ? 'text-white/55' : 'text-slate-400'}`}>{t.detail}</p>
                      </div>
                    </motion.div>
                  );
                })}
              </motion.div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ── Revenue ─────────────────────────────────────────────────── */}
      <section id="revenue" className="py-28 px-6 bg-white border-t border-slate-200/60">
        <div className="max-w-6xl mx-auto">
          <Eyebrow>Revenue model</Eyebrow>
          <RevealHeading wrapClassName="mb-14" className="text-[2.4rem] md:text-[3.2rem] font-extrabold tracking-tight leading-[1.05] text-text-dark">
            Lipi pays for itself, and then some.
          </RevealHeading>
          <div className="grid md:grid-cols-2 gap-6">
            <motion.div variants={fadeUp} initial={reduce ? false : 'hidden'} whileInView="visible" viewport={{ once: true, amount: 0.3 }} className="rounded-3xl border-2 border-primary bg-primary/[0.03] p-8 space-y-6">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-primary">DHIS incentive</span>
                <div className="flex items-end gap-2 mt-2">
                  <IndianRupee className="w-7 h-7 text-primary mb-2" strokeWidth={2.2} />
                  <span className="text-[4.5rem] font-black tracking-tight text-primary leading-none">20</span>
                  <span className="text-slate-500 text-[15px] font-medium mb-2.5">per ABDM consult</span>
                </div>
              </div>
              <p className="text-[14.5px] text-slate-600 leading-relaxed">The government pays your clinic for every consultation filed through ABDM. At 40 patients a day, that is <strong className="text-text-dark">₹800 every day</strong> — directly from DHIS to your bank account.</p>
              <div className="bg-white rounded-2xl border border-primary/15 p-5 space-y-3">
                {[
                  ['40 patients/day × ₹20', '₹800/day', false],
                  ['Monthly (26 working days)', '₹20,800/mo', false],
                  ['Lipi Pro subscription', '− ₹50/mo', false],
                  ['Net new revenue', '+₹20,750/mo', true],
                ].map(([l, v, bold]) => (
                  <div key={String(l)} className={`flex justify-between items-center text-[13.5px] ${bold ? 'pt-2 border-t border-slate-100' : ''}`}>
                    <span className={bold ? 'font-bold text-text-dark' : 'text-slate-500'}>{l}</span>
                    <span className={bold ? 'font-black text-primary text-[17px]' : 'font-semibold text-primary'}>{v}</span>
                  </div>
                ))}
              </div>
            </motion.div>
            <motion.div variants={fadeUp} initial={reduce ? false : 'hidden'} whileInView="visible" viewport={{ once: true, amount: 0.3 }} transition={{ delay: 0.1 }} className="rounded-3xl border border-slate-200/80 p-8 space-y-6">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-400">Time returned</span>
                <div className="flex items-end gap-2 mt-2">
                  <span className="text-[4.5rem] font-black tracking-tight text-text-dark leading-none">45</span>
                  <span className="text-slate-500 text-[15px] font-medium mb-2.5">min saved/day</span>
                </div>
              </div>
              <p className="text-[14.5px] text-slate-600 leading-relaxed">At 40 patients, documentation drops from 2–3 min to under 30 sec each. That is your lunch break back, every day.</p>
              <div className="space-y-4 pt-2">
                {[
                  ['Writing notes', '2 min', '< 30 sec'],
                  ['Prescription drafting', '90 sec', 'Auto-generated'],
                  ['Lab order dispatch', '5 min', 'Auto-dispatched'],
                  ['Follow-up scheduling', '3 min', 'Auto-queued'],
                ].map(([l, b, a]) => (
                  <div key={String(l)} className="flex items-center justify-between border-b border-slate-100 pb-3 last:border-0 last:pb-0">
                    <span className="text-[13.5px] text-slate-600">{l}</span>
                    <div className="flex items-center gap-2 text-[13px]">
                      <span className="line-through text-slate-300">{b}</span>
                      <ArrowRight className="w-3 h-3 text-slate-300" />
                      <span className="font-semibold text-primary">{a}</span>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ── Dialect demo ────────────────────────────────────────────── */}
      <section id="languages" className="py-28 px-6">
        <div className="max-w-5xl mx-auto">
          <Eyebrow>11+ Languages</Eyebrow>
          <RevealHeading wrapClassName="mb-5" className="text-[2.4rem] md:text-[3rem] font-extrabold tracking-tight leading-[1.05] text-text-dark">
            Built for how India actually speaks.
          </RevealHeading>
          <motion.p variants={fadeUp} initial={reduce ? false : 'hidden'} whileInView="visible" viewport={{ once: true }} className="text-[14.5px] text-slate-500 mb-10 leading-relaxed max-w-[50ch]">
            Hindi, Hinglish, English — with code-switching, self-corrections, and regional vocabulary handled natively.
          </motion.p>
          <motion.div variants={fadeUp} initial={reduce ? false : 'hidden'} whileInView="visible" viewport={{ once: true, amount: 0.2 }} className="rounded-3xl border border-slate-200/80 bg-white overflow-hidden shadow-[0_4px_48px_-12px_rgba(18,63,39,0.12)]">
            <div className="flex border-b border-slate-200/80 bg-slate-50/60">
              {(['hinglish', 'hindi', 'english'] as LangKey[]).map((lang) => (
                <button key={lang} onClick={() => setActiveTab(lang)} className={`px-6 py-3.5 text-[12.5px] font-semibold uppercase tracking-wider transition-colors cursor-pointer ${activeTab === lang ? 'text-primary border-b-2 border-primary bg-white' : 'text-slate-400 hover:text-slate-600'}`}>{lang}</button>
              ))}
            </div>
            <div className="p-7 md:p-9 grid md:grid-cols-[1fr_1.2fr] gap-8 items-start">
              <div className="space-y-5">
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5"><Mic className="w-3 h-3" /> Raw speech</p>
                  <p className="text-[15px] text-text-dark leading-relaxed italic">"{DIALECT_SAMPLES[activeTab].speech}"</p>
                </div>
                <div className="pt-4 border-t border-slate-100">
                  <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5"><Activity className="w-3 h-3" /> Resolution</p>
                  <p className="text-[13px] text-slate-600 leading-relaxed">{DIALECT_SAMPLES[activeTab].resolution}</p>
                </div>
              </div>
              <div className="space-y-4">
                <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5"><Cpu className="w-3 h-3" /> Extracted entities</p>
                <div className="grid grid-cols-3 gap-3">
                  <div className="rounded-2xl bg-primary/5 border border-primary/12 p-4 space-y-2">
                    <span className="text-[10.5px] font-bold uppercase tracking-wider text-primary block">Symptoms</span>
                    {DIALECT_SAMPLES[activeTab].entities.symptoms.map((s) => <p key={s} className="text-[13px] font-medium text-text-dark">{s}</p>)}
                  </div>
                  <div className="rounded-2xl bg-slate-50 border border-slate-200 p-4 space-y-2">
                    <span className="text-[10.5px] font-bold uppercase tracking-wider text-slate-400 block">Vitals</span>
                    {DIALECT_SAMPLES[activeTab].entities.vitals.map((v) => <p key={v} className="text-[13px] font-medium text-text-dark">{v}</p>)}
                  </div>
                  <div className="rounded-2xl bg-red-50 border border-red-100 p-4 space-y-2">
                    <span className="text-[10.5px] font-bold uppercase tracking-wider text-red-400 block">Negated</span>
                    {DIALECT_SAMPLES[activeTab].entities.negated.map((n) => <p key={n} className="text-[13px] font-medium text-slate-400 line-through">{n}</p>)}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── Testimonials ────────────────────────────────────────────── */}
      <section className="py-28 px-6 bg-white border-t border-slate-200/60">
        <div className="max-w-6xl mx-auto">
          <Eyebrow>From doctors</Eyebrow>
          <RevealHeading wrapClassName="mb-14" className="text-[2.4rem] md:text-[3.2rem] font-extrabold tracking-tight leading-[1.05] text-text-dark">
            Real OPDs. Real time saved.
          </RevealHeading>
          <motion.div variants={stagger} initial={reduce ? false : 'hidden'} whileInView="visible" viewport={{ once: true, amount: 0.2 }} className="grid md:grid-cols-3 gap-5">
            {TESTIMONIALS.map((t) => (
              <motion.div
                key={t.name}
                variants={fadeUp}
                whileHover={{ y: -6, transition: { duration: 0.22 } }}
                className="rounded-3xl border border-slate-200/80 bg-bg-warm p-7 space-y-5 cursor-default"
              >
                <p className="text-[14.5px] text-slate-700 leading-relaxed">"{t.quote}"</p>
                <div className="pt-3 border-t border-slate-100">
                  <p className="text-[13.5px] font-bold text-text-dark">{t.name}</p>
                  <p className="text-[12px] text-slate-500 mt-0.5">{t.role}</p>
                  <p className="text-[12px] text-slate-400">{t.location}</p>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── Final CTA ───────────────────────────────────────────────── */}
      <section className="py-24 px-6 bg-primary">
        <div className="max-w-3xl mx-auto text-center space-y-7">
          <motion.h2
            initial={reduce ? false : { opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] as const }}
            className="text-[2.4rem] md:text-[3rem] font-extrabold text-white tracking-tight leading-[1.05]"
          >
            Ready to run your OPD on autopilot?
          </motion.h2>
          <motion.p
            initial={reduce ? false : { opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1, ease: [0.16, 1, 0.3, 1] as const }}
            className="text-[15px] text-white/70 leading-relaxed"
          >
            Currently onboarding pilot doctors directly. Email us and we'll get you set up.
          </motion.p>
          <motion.div
            initial={reduce ? false : { opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55, delay: 0.18 }}
            className="flex flex-col sm:flex-row gap-3 justify-center"
          >
            <motion.a
              href="mailto:arushsinghal98@gmail.com?subject=Lipi%20early%20access"
              whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.97 }}
              className="px-8 py-4 bg-white hover:bg-white/92 text-primary rounded-full font-bold text-[15px] flex items-center justify-center gap-2 transition-colors cursor-pointer"
            >
              Request early access <ArrowRight className="w-4 h-4" />
            </motion.a>
            <motion.button
              onClick={() => setShowSupportModal(true)}
              whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.97 }}
              className="px-8 py-4 border border-white/30 hover:border-white/60 text-white/80 hover:text-white rounded-full font-semibold text-[15px] transition-all cursor-pointer"
            >
              Talk to us
            </motion.button>
          </motion.div>
        </div>
      </section>

      {/* ── Footer (Antigravity-style: links + giant wordmark) ──────── */}
      <footer className="relative bg-bg-warm border-t border-slate-200/60 overflow-hidden">
        <div className="max-w-7xl mx-auto px-6 pt-20 pb-14">
          <div className="flex flex-col md:flex-row justify-between gap-12">
            {/* Brand + reassurance */}
            <div className="max-w-xs space-y-5">
              <div className="flex items-center gap-2.5">
                <span className="grid place-items-center w-9 h-9 rounded-xl bg-primary text-white font-bold text-base">श</span>
                <span className="text-[20px] font-bold tracking-tight text-text-dark">Lipi</span>
              </div>
              <p className="text-[14px] text-slate-500 leading-relaxed">
                AI drafts the note, prescription, and follow-up. The doctor reviews and signs — every fact traced to the source sentence.
              </p>
              <button
                onClick={() => navigate('/dashboard')}
                className="inline-flex items-center gap-1.5 bg-text-dark hover:bg-black text-white font-semibold text-[13.5px] px-5 py-2.5 rounded-full transition-colors cursor-pointer"
              >
                Open Lipi <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            {/* Link columns */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-12 gap-y-8">
              <div className="space-y-3.5">
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">Product</p>
                <ul className="space-y-2.5 text-[14px]">
                  <li><button onClick={() => document.getElementById('how')?.scrollIntoView({ behavior: 'smooth' })} className="text-slate-600 hover:text-primary transition-colors cursor-pointer">How it works</button></li>
                  <li><button onClick={() => document.getElementById('languages')?.scrollIntoView({ behavior: 'smooth' })} className="text-slate-600 hover:text-primary transition-colors cursor-pointer">Languages</button></li>
                  <li><button onClick={() => document.getElementById('revenue')?.scrollIntoView({ behavior: 'smooth' })} className="text-slate-600 hover:text-primary transition-colors cursor-pointer">Revenue model</button></li>
                  <li><button onClick={() => navigate('/pricing')} className="text-slate-600 hover:text-primary transition-colors cursor-pointer">Pricing</button></li>
                </ul>
              </div>
              <div className="space-y-3.5">
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">Company</p>
                <ul className="space-y-2.5 text-[14px]">
                  <li><button onClick={() => navigate('/research')} className="text-slate-600 hover:text-primary transition-colors cursor-pointer">Research</button></li>
                  <li><button onClick={() => setShowSupportModal(true)} className="text-slate-600 hover:text-primary transition-colors cursor-pointer">Contact</button></li>
                  <li><a href="/privacy" className="text-slate-600 hover:text-primary transition-colors">Privacy</a></li>
                  <li><button onClick={() => navigate('/dashboard')} className="text-slate-600 hover:text-primary transition-colors cursor-pointer">Dashboard</button></li>
                </ul>
              </div>
              <div className="space-y-3.5">
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">Compliance</p>
                <ul className="space-y-2.5 text-[14px]">
                  <li><span className="text-slate-600">ABDM-ready</span></li>
                  <li><span className="text-slate-600">HL7 / FHIR export</span></li>
                  <li><span className="text-slate-600">On-shore NLP</span></li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Giant solid wordmark — bleeds off the bottom edge */}
        <div className="px-6 -mb-[0.1em] select-none pointer-events-none">
          <motion.p
            initial={reduce ? false : { y: 56, opacity: 0 }}
            whileInView={{ y: 0, opacity: 1 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] as const }}
            className="font-black leading-[0.78] tracking-[-0.04em] text-primary text-center"
            style={{ fontSize: 'clamp(120px, 46vw, 720px)' }}
            aria-hidden
          >
            Lipi
          </motion.p>
        </div>

        {/* Legal bar */}
        <div className="border-t border-slate-200/60">
          <div className="max-w-7xl mx-auto px-6 py-5 flex flex-col sm:flex-row items-center justify-between gap-3 text-[12px] text-slate-400">
            <span>© 2026 Lipi Health · Built in India</span>
            <div className="flex items-center gap-5">
              <a href="/privacy" className="hover:text-slate-600 transition-colors">Privacy</a>
              <button onClick={() => setShowSupportModal(true)} className="hover:text-slate-600 transition-colors cursor-pointer">Contact</button>
              <button onClick={() => navigate('/pricing')} className="hover:text-slate-600 transition-colors cursor-pointer">Pricing</button>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
