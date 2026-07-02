import { useNavigate } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import {
  ArrowRight,
  FileSearch,
  ShieldCheck,
  GitBranch,
  FlaskConical,
  Microscope,
  Network,
  Pill,
  Radar,
} from 'lucide-react';

const fadeUp = {
  hidden: { opacity: 0, y: 40 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] as const } },
};

const PIPELINE = [
  { icon: FileSearch, label: 'Transcript', detail: 'Voice or text. Hindi, English, Hinglish.' },
  { icon: GitBranch, label: 'Deterministic extraction', detail: 'Rule and evidence based, not generative.' },
  { icon: ShieldCheck, label: 'Evidence-linked facts', detail: 'Every fact traces to its source sentence.' },
  { icon: Microscope, label: 'Doctor confirmation', detail: 'Nothing is official until reviewed.' },
];

const DIRECTIONS = [
  {
    icon: Pill,
    title: 'Drug interaction modeling for Indian formularies',
    body: 'Most interaction checkers are built on Western drug databases and miss the brand-name confusion and dosing conventions specific to Indian prescribing. We are building a model grounded in local formularies instead.',
  },
  {
    icon: Radar,
    title: 'Surveillance gaps in antimicrobial resistance',
    body: 'India carries one of the largest antimicrobial resistance burdens in the world, and current surveillance mostly sees hospital data, missing the majority of prescribing that happens in primary care. We are mapping where the visibility actually breaks down.',
  },
  {
    icon: Network,
    title: 'Structured signal from unstructured consultations',
    body: 'Every consultation processed through Lipi becomes a structured, evidence-linked clinical record. We are researching what that corpus can reveal about disease patterns and prescribing behavior at population scale, without ever touching identifiable patient data.',
  },
];

export default function Research() {
  const navigate = useNavigate();
  const reduce = useReducedMotion();

  return (
    <div className="min-h-screen bg-bg-warm font-sans text-text-dark antialiased">
      {/* ── Nav ─────────────────────────────────────────────────────── */}
      <nav className="sticky top-0 z-[100] border-b border-slate-200/60 bg-bg-warm/85 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between gap-4">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2.5 cursor-pointer group"
          >
            <span className="grid place-items-center w-8 h-8 rounded-xl bg-primary text-white font-bold text-sm shadow-sm group-hover:scale-105 transition-transform">श</span>
            <span className="text-[17px] font-bold tracking-tight text-text-dark">Lipi</span>
          </button>
          <motion.a
            href="mailto:arushsinghal98@gmail.com?subject=Lipi%20early%20access"
            whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
            className="text-[13.5px] font-semibold bg-primary hover:bg-primary-dark text-white pl-4 pr-3.5 py-2 rounded-full flex items-center gap-1.5 cursor-pointer transition-colors shadow-sm"
          >
            Request early access <ArrowRight className="w-4 h-4" />
          </motion.a>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6">
        {/* ── Intro ─────────────────────────────────────────────────── */}
        <section className="grid lg:grid-cols-[1fr_0.9fr] gap-10 lg:gap-16 py-20 items-center">
          <motion.div
            initial={reduce ? false : 'hidden'}
            animate="visible"
            variants={fadeUp}
          >
            <div className="inline-flex items-center gap-2 bg-primary/[0.07] border border-primary/20 text-primary text-[11.5px] font-semibold px-3.5 py-1.5 rounded-full mb-7 tracking-wide">
              <FlaskConical className="w-3.5 h-3.5" />
              Applied AI research
            </div>
            <h1 className="text-[2.6rem] md:text-[3.4rem] leading-[1.02] tracking-[-0.03em] font-extrabold mb-6">
              A frontier AI research lab. <span className="text-primary">Healthcare is the problem we chose.</span>
            </h1>
            <p className="text-[16px] md:text-[17px] text-slate-500 leading-relaxed max-w-[52ch]">
              Lipi is how the research reaches doctors today. Every result on this page is already running in
              production, not a slide in a roadmap deck.
            </p>
          </motion.div>

          <motion.div
            initial={reduce ? false : { opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.7, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
            className="rounded-3xl border border-slate-200/80 bg-white p-6 md:p-8 shadow-[0_4px_48px_-12px_rgba(18,63,39,0.12)]"
          >
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-5">How a note gets made</p>
            <div className="space-y-3">
              {PIPELINE.map((step, i) => (
                <div key={step.label} className="flex items-start gap-3.5">
                  <div className="w-9 h-9 rounded-2xl bg-primary/8 grid place-items-center shrink-0 mt-0.5">
                    <step.icon className="w-4.5 h-4.5 text-primary" strokeWidth={1.8} />
                  </div>
                  <div className="pt-1">
                    <p className="text-[14px] font-semibold text-text-dark leading-tight">{step.label}</p>
                    <p className="text-[12.5px] text-slate-500 leading-snug mt-0.5">{step.detail}</p>
                  </div>
                  {i < PIPELINE.length - 1 && (
                    <span className="sr-only">then</span>
                  )}
                </div>
              ))}
            </div>
          </motion.div>
        </section>

        {/* ── Research Result ───────────────────────────────────────── */}
        <motion.section
          initial={reduce ? false : 'hidden'}
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
          variants={fadeUp}
          className="py-16 border-t border-slate-200/60"
        >
          <div className="grid lg:grid-cols-[0.9fr_1.1fr] gap-10 items-start rounded-3xl border border-primary/20 bg-primary/[0.03] p-8 md:p-10">
            <div>
              <h2 className="text-[1.9rem] md:text-[2.3rem] font-bold tracking-tight leading-[1.05]">
                Zero-hallucination clinical documentation
              </h2>
            </div>
            <div className="space-y-4">
              <p className="text-slate-600 leading-relaxed">
                Most AI medical scribes draft the clinical note with a generative model, which means the note
                can contain plausible content that was never actually said. Lipi's extraction pipeline does not
                work this way. Every clinical fact, a symptom, a diagnosis, a medication, a vital, is pulled out
                through deterministic, rule and evidence based extraction, not invented by a model guessing at
                what a typical note should contain.
              </p>
              <p className="text-slate-600 leading-relaxed">
                Every fact carries a traceable link back to the exact sentence in the transcript it came from,
                and nothing becomes an official clinical record until the doctor explicitly reviews and confirms
                it. That is a structural gate, not a disclaimer.
              </p>
            </div>
          </div>
        </motion.section>

        {/* ── What we're researching next ──────────────────────────── */}
        <section className="py-16 border-t border-slate-200/60">
          <motion.div
            initial={reduce ? false : 'hidden'}
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
            variants={fadeUp}
            className="mb-10 max-w-[60ch]"
          >
            <h2 className="text-[1.9rem] md:text-[2.3rem] font-bold tracking-tight leading-[1.05] mb-3">
              What we're researching next
            </h2>
            <p className="text-slate-500 leading-relaxed">
              These are active directions, not shipped results. We are stating that plainly rather than
              presenting early work as finished.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-5">
            {DIRECTIONS.map((d, i) => (
              <motion.div
                key={d.title}
                initial={reduce ? false : { opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.3 }}
                transition={{ duration: 0.55, delay: i * 0.08, ease: [0.16, 1, 0.3, 1] }}
                className="rounded-3xl border border-slate-200/80 bg-white p-6 space-y-3"
              >
                <div className="w-10 h-10 rounded-2xl bg-accent/10 grid place-items-center">
                  <d.icon className="w-5 h-5 text-accent-dark" strokeWidth={1.8} />
                </div>
                <p className="text-[15.5px] font-semibold text-text-dark leading-snug">{d.title}</p>
                <p className="text-[13.5px] text-slate-500 leading-relaxed">{d.body}</p>
              </motion.div>
            ))}
          </div>
        </section>
      </main>

      {/* ── Closing CTA ───────────────────────────────────────────── */}
      <section className="py-20 px-6 bg-primary">
        <div className="max-w-3xl mx-auto text-center space-y-6">
          <motion.h2
            initial={reduce ? false : { opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className="text-[2.1rem] md:text-[2.6rem] font-extrabold text-white tracking-tight leading-[1.05]"
          >
            Research collaborations and institutional partnerships
          </motion.h2>
          <motion.p
            initial={reduce ? false : { opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55, delay: 0.1 }}
            className="text-[15px] text-white/70 leading-relaxed"
          >
            For a full technical briefing, reach out directly.
          </motion.p>
          <motion.div
            initial={reduce ? false : { opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.18 }}
          >
            <a
              href="mailto:arushsinghal98@gmail.com?subject=Lipi%20research%20inquiry"
              className="inline-flex items-center gap-2 px-8 py-4 bg-white hover:bg-white/92 text-primary rounded-full font-bold text-[15px] transition-colors cursor-pointer"
            >
              Request early access <ArrowRight className="w-4 h-4" />
            </a>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
