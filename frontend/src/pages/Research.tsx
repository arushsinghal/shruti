import { useNavigate } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import {
  ArrowRight,
  Activity,
  FileSearch,
  FlaskConical,
  Network,
  Pill,
  Radar,
  ShieldCheck,
} from 'lucide-react';
import { RESEARCH_POSTS } from '../data/researchPosts';

const fadeUp = {
  hidden: { opacity: 0, y: 32 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.55, ease: [0.16, 1, 0.3, 1] as const } },
};

const SECONDARY_STATS = [
  { value: '80', label: 'Drug-drug interaction pairs', sublabel: 'openFDA · PubMed · India NLEM' },
  { value: '85.2%', label: 'Hinglish clinical NLP F1', sublabel: 'Internal 200-sentence benchmark · deterministic rules' },
  { value: '150', label: 'Indian OPD diagnoses mapped', sublabel: '435 lookup terms · ICD-10-CM and ICD-10-WHO' },
];

const CORE_RESEARCH_TRACKS = [
  {
    icon: Activity,
    title: 'Continual learning for healthcare services',
    body: 'How an AI-native OPD assistant improves from doctor corrections, task completion, follow-up responses, and signed workflows without silently changing clinical facts.',
  },
  {
    icon: Network,
    title: 'Multilingual clinical understanding',
    body: 'Hindi, Hinglish, English, code-switching, self-corrections, negations, Indian brand names, lab terms, and real OPD speech patterns.',
  },
  {
    icon: ShieldCheck,
    title: 'Drug safety and personalization',
    body: 'Allergy conflicts, dose ambiguity, brand-generic confusion, repeat medication history, and doctor-gated patient-specific risk signals.',
  },
  {
    icon: Radar,
    title: 'AMR and antibiotic intelligence',
    body: 'OPD antibiotic patterns, suspected diagnosis, follow-up outcomes, and stewardship signals for Indian primary care.',
  },
];

const TRACK_META: Record<string, { icon: React.ElementType; stat: string }> = {
  'drug-safety-indian-formularies': {
    icon: Pill,
    stat: '80 DDI pairs · 15 PGx rules · 8 deployable in OPD today',
  },
  'amr-surveillance-gap': {
    icon: Radar,
    stat: '80 pp gap · 12 site-years reviewed · validation protocol designed',
  },
  'hinglish-clinical-nlp': {
    icon: Network,
    stat: '85.2% macro-F1 · 6 failure modes mapped · 200 annotated sentences',
  },
  'indian-opd-ontology': {
    icon: FileSearch,
    stat: '150 diagnoses · 435 lookup terms · ICD-10-CM and ICD-10-WHO coded',
  },
};

export default function Research() {
  const navigate = useNavigate();
  const reduce = useReducedMotion();

  return (
    <div className="min-h-screen bg-bg-warm font-sans text-text-dark antialiased">

      {/* ── Nav ─────────────────────────────────────────────────────── */}
      <nav className="sticky top-0 z-[100] border-b border-slate-200/60 bg-bg-warm/85 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between gap-4">
          <button onClick={() => navigate('/')} className="flex items-center gap-2.5 cursor-pointer group">
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

        {/* ── Hero ─────────────────────────────────────────────────── */}
        <section className="grid lg:grid-cols-[1fr_0.85fr] gap-10 lg:gap-16 py-20 items-center">
          <motion.div initial={reduce ? false : 'hidden'} animate="visible" variants={fadeUp}>
            <div className="inline-flex items-center gap-2 bg-primary/[0.07] border border-primary/20 text-primary text-[11.5px] font-semibold px-3.5 py-1.5 rounded-full mb-7 tracking-wide">
              <FlaskConical className="w-3.5 h-3.5" />
              Applied AI research
            </div>
            <h1 className="text-[2.6rem] md:text-[3.4rem] leading-[1.02] tracking-[-0.03em] font-extrabold mb-6">
              Healthcare AI that learns from reviewed care,{' '}
              <span className="text-primary">not scraped text.</span>
            </h1>
            <p className="text-[16px] md:text-[17px] text-slate-500 leading-relaxed max-w-[50ch] mb-10">
              Lipi is a research-driven AI-native healthcare service company. The product starts
              with the OPD assistant; the research program studies how doctor-reviewed clinical
              traces can make healthcare AI safer, more multilingual, and more useful over time.
            </p>

            {/* Featured 80pp stat — in the hero copy itself */}
            <div className="border-t border-slate-200/70 pt-8">
              <p className="text-[3.8rem] md:text-[4.6rem] font-extrabold text-primary tracking-tight leading-none">
                80 pp
              </p>
              <p className="text-[13.5px] font-semibold text-text-dark mt-2 mb-1.5">
                Primary-care AMR surveillance gap
              </p>
              <p className="text-[12.5px] text-slate-500 leading-relaxed max-w-[46ch]">
                ~80% of India's antibiotic consumption happens in primary care. 0% of ICMR AMRSN and
                NCDC NARS-Net specimens come from primary-care settings. Quantified across 12
                site-years of source reports. Treat this as a gap analysis, not a deployed
                surveillance claim.
              </p>
            </div>
          </motion.div>

          {/* Figure 1 — research chart */}
          <motion.div
            initial={reduce ? false : { opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.65, delay: 0.12, ease: [0.16, 1, 0.3, 1] }}
            className="rounded-3xl border border-slate-200/80 bg-white overflow-hidden shadow-[0_4px_48px_-12px_rgba(18,63,39,0.10)]"
          >
            <div className="bg-slate-50/70 overflow-hidden">
              <img
                src="/research/chart1_consumption_vs_surveillance.png"
                alt="Antibiotic consumption in primary care vs. AMR surveillance site coverage, India"
                className="w-full h-auto block"
                loading="eager"
              />
            </div>
            <div className="px-5 pt-3.5 pb-4 flex items-start gap-3 border-t border-slate-100">
              <span className="text-[9.5px] font-bold font-mono text-primary/60 shrink-0 mt-0.5 tracking-wider">FIG. 1</span>
              <span className="text-[11.5px] text-slate-500 leading-snug">
                Antibiotic consumption in primary care vs. AMR surveillance site coverage, India.
                From our AMR gap analysis.
              </span>
            </div>
          </motion.div>
        </section>

        {/* ── Secondary stats ───────────────────────────────────────── */}
        <motion.section
          initial={reduce ? false : 'hidden'}
          whileInView="visible"
          viewport={{ once: true, amount: 0.25 }}
          variants={fadeUp}
          className="pb-16 border-t border-slate-200/60 pt-12"
        >
          <div className="grid sm:grid-cols-3 gap-px bg-slate-200/50 rounded-3xl overflow-hidden border border-slate-200/60">
            {SECONDARY_STATS.map(s => (
              <div key={s.value} className="bg-white px-7 py-7">
                <p className="text-[2.4rem] font-extrabold tracking-tight text-text-dark leading-none mb-2">{s.value}</p>
                <p className="text-[13px] font-semibold text-slate-700 leading-snug mb-1">{s.label}</p>
                <p className="text-[11.5px] text-slate-400 leading-snug">{s.sublabel}</p>
              </div>
            ))}
          </div>
        </motion.section>

        {/* ── Research thesis ──────────────────────────────────────── */}
        <section className="py-16 border-t border-slate-200/60">
          <motion.div
            initial={reduce ? false : 'hidden'}
            whileInView="visible"
            viewport={{ once: true, amount: 0.25 }}
            variants={fadeUp}
            className="grid lg:grid-cols-[0.85fr_1.15fr] gap-10 lg:gap-16 items-start mb-10"
          >
            <div>
              <p className="text-[10.5px] font-bold uppercase tracking-widest text-primary/60 mb-3">Core AI research</p>
              <h2 className="text-[1.9rem] md:text-[2.35rem] font-bold tracking-tight leading-[1.06] max-w-[16ch]">
                Continual learning for doctor-gated healthcare AI services
              </h2>
            </div>
            <div className="space-y-5 max-w-2xl">
              <p className="text-[15px] text-slate-600 leading-relaxed">
                Personalized care needs longitudinal, trustworthy clinical context. In India, that
                context is fragmented across speech, paper, WhatsApp, prescriptions, test orders,
                and follow-ups. Lipi's first job is to structure that reality through doctor-reviewed
                workflows.
              </p>
              <p className="text-[15px] text-slate-600 leading-relaxed">
                Once every visit is source-traced and doctor-gated, we can research safer
                personalization: drug safety, antibiotic stewardship, follow-up risk, chronic-care
                memory, and clinic-specific workflow learning. These are research directions, not
                autonomous clinical claims.
              </p>
            </div>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-5">
            {CORE_RESEARCH_TRACKS.map((track, i) => {
              const Icon = track.icon;
              return (
                <motion.div
                  key={track.title}
                  initial={reduce ? false : { opacity: 0, y: 18 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, amount: 0.2 }}
                  transition={{ duration: 0.48, delay: i * 0.06, ease: [0.16, 1, 0.3, 1] }}
                  className="rounded-3xl border border-slate-200/80 bg-white p-7"
                >
                  <div className="mb-4 grid h-10 w-10 place-items-center rounded-2xl bg-primary/8">
                    <Icon className="h-5 w-5 text-primary" strokeWidth={1.8} />
                  </div>
                  <h3 className="text-[16px] font-bold text-text-dark leading-snug">{track.title}</h3>
                  <p className="mt-3 text-[13.5px] leading-relaxed text-slate-500">{track.body}</p>
                </motion.div>
              );
            })}
          </div>
        </section>

        {/* ── Shipped result ───────────────────────────────────────── */}
        <motion.section
          initial={reduce ? false : 'hidden'}
          whileInView="visible"
          viewport={{ once: true, amount: 0.25 }}
          variants={fadeUp}
          className="py-16 border-t border-slate-200/60"
        >
          <div className="rounded-3xl border border-primary/20 bg-primary/[0.03] p-8 md:p-10">
            <p className="text-[10.5px] font-bold uppercase tracking-widest text-primary/60 mb-3">Shipped result</p>
            <h2 className="text-[1.9rem] md:text-[2.2rem] font-bold tracking-tight leading-[1.06] mb-6 max-w-[30ch]">
              Zero-hallucination clinical documentation is the first proof point
            </h2>
            <div className="grid lg:grid-cols-2 gap-6 max-w-4xl">
              <p className="text-[15px] text-slate-600 leading-relaxed">
                Most AI medical scribes draft the clinical note with a generative model, which means
                the note can contain plausible content that was never actually said. Lipi's extraction
                pipeline does not work this way. Every clinical fact is pulled through deterministic,
                rule and evidence-based extraction — not invented by a model guessing at what a
                typical note should contain.
              </p>
              <p className="text-[15px] text-slate-600 leading-relaxed">
                Every fact carries a traceable link back to the exact sentence in the transcript it
                came from, and nothing becomes an official clinical record until the doctor explicitly
                reviews and confirms it. That is a structural gate, not a disclaimer.
              </p>
            </div>
          </div>
        </motion.section>

        {/* ── Research outcomes ────────────────────────────────────── */}
        <section className="py-16 border-t border-slate-200/60">
          <motion.div
            initial={reduce ? false : 'hidden'}
            whileInView="visible"
            viewport={{ once: true, amount: 0.25 }}
            variants={fadeUp}
            className="mb-10"
          >
            <h2 className="text-[1.9rem] md:text-[2.2rem] font-bold tracking-tight leading-[1.06] mb-3">
              Research outcomes
            </h2>
            <p className="text-[15px] text-slate-500 leading-relaxed max-w-[52ch]">
              Completed and in-progress work with source citations, gap audits, and explicit
              product-readiness boundaries.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-5">
            {RESEARCH_POSTS.map((post, i) => {
              const meta = TRACK_META[post.slug];
              const Icon = meta?.icon ?? FileSearch;
              return (
                <motion.div
                  key={post.slug}
                  initial={reduce ? false : { opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, amount: 0.2 }}
                  transition={{ duration: 0.5, delay: i * 0.07, ease: [0.16, 1, 0.3, 1] }}
                  onClick={() => navigate(`/research/${post.slug}`)}
                  className="group rounded-3xl border border-slate-200/80 bg-white p-7 flex flex-col gap-5 cursor-pointer hover:border-primary/25 hover:shadow-[0_8px_40px_-16px_rgba(27,94,59,0.18)] transition-all duration-300"
                >
                  {/* Header row */}
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-2xl bg-primary/8 grid place-items-center shrink-0">
                        <Icon className="w-5 h-5 text-primary" strokeWidth={1.8} />
                      </div>
                      <span className="text-[10.5px] font-bold uppercase tracking-widest text-primary/70 bg-primary/[0.06] border border-primary/12 px-2.5 py-1 rounded-full">
                        {post.tag}
                      </span>
                    </div>
                    <div className="w-7 h-7 rounded-full border border-slate-200 grid place-items-center shrink-0 group-hover:border-primary/30 group-hover:bg-primary/[0.04] transition-colors mt-0.5">
                      <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-primary group-hover:translate-x-0.5 transition-all" strokeWidth={2} />
                    </div>
                  </div>

                  {/* Title */}
                  <div className="flex-1">
                    <h3 className="text-[17px] font-bold text-text-dark leading-snug mb-3 group-hover:text-primary transition-colors">
                      {post.title}
                    </h3>
                    <p className="text-[13.5px] text-slate-500 leading-relaxed line-clamp-3">
                      {post.intro}
                    </p>
                  </div>

                  {/* Stat footer */}
                  <p className="text-[11.5px] font-semibold text-slate-400 border-t border-slate-100 pt-4">
                    {meta?.stat}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </section>
      </main>

      {/* ── Closing CTA ───────────────────────────────────────────── */}
      <section className="py-20 px-6 bg-primary">
        <div className="max-w-3xl mx-auto space-y-6">
          <motion.h2
            initial={reduce ? false : { opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
            className="text-[2rem] md:text-[2.5rem] font-extrabold text-white tracking-tight leading-[1.06]"
          >
            Research collaborations and institutional partnerships
          </motion.h2>
          <motion.p
            initial={reduce ? false : { opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.08 }}
            className="text-[15px] text-white/65 leading-relaxed max-w-[48ch]"
          >
            For a full technical briefing, reach out directly.
          </motion.p>
          <motion.div
            initial={reduce ? false : { opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.45, delay: 0.15 }}
          >
            <a
              href="mailto:arushsinghal98@gmail.com?subject=Lipi%20research%20inquiry"
              className="inline-flex items-center gap-2 px-7 py-3.5 bg-white hover:bg-white/92 text-primary rounded-full font-bold text-[14.5px] transition-colors cursor-pointer"
            >
              Get in touch <ArrowRight className="w-4 h-4" />
            </a>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
