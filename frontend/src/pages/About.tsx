import { useNavigate } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import { ArrowRight, FileSearch, MapPin, Network, Pill, Radar, ShieldCheck } from 'lucide-react';
import { RESEARCH_POSTS } from '../data/researchPosts';

const fadeUp = {
  hidden: { opacity: 0, y: 32 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.55, ease: [0.16, 1, 0.3, 1] as const } },
};

const TRACK_ICONS: Record<string, React.ElementType> = {
  'drug-safety-indian-formularies': Pill,
  'amr-surveillance-gap': Radar,
  'hinglish-clinical-nlp': Network,
  'indian-opd-ontology': FileSearch,
};

const PRINCIPLES = [
  {
    n: '01',
    title: 'Workflow first',
    body: 'Products must fit real clinical throughput before they can become intelligent systems. A tool that slows a 60-patient OPD down does not get a second consultation.',
  },
  {
    n: '02',
    title: 'Local by default',
    body: 'Clinical extraction, memory resolution, and conflict detection run deterministically, with patient data on India-hosted infrastructure. Nothing clinical is invented by a generative model.',
  },
  {
    n: '03',
    title: 'Models with accountability',
    body: 'The doctor is the final authority on everything. Every clinical fact links back to the exact sentence it came from, and nothing becomes a record until the doctor signs it.',
  },
];

export default function About() {
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
          <div className="hidden md:flex items-center gap-6">
            <button onClick={() => navigate('/research')} className="text-[13.5px] font-medium text-slate-500 hover:text-primary transition-colors cursor-pointer">Research</button>
            <button onClick={() => navigate('/pricing')} className="text-[13.5px] font-medium text-slate-500 hover:text-primary transition-colors cursor-pointer">Pricing</button>
          </div>
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
        <section className="py-20 md:py-28 max-w-4xl">
          <motion.div initial={reduce ? false : 'hidden'} animate="visible" variants={fadeUp}>
            <div className="flex items-center gap-3 mb-6">
              <span className="h-px w-9 bg-gradient-to-r from-primary to-primary/20" />
              <span className="text-[12px] font-bold uppercase tracking-[0.22em] text-primary">Company</span>
            </div>
            <h1 className="text-[2.6rem] md:text-[3.6rem] leading-[1.02] tracking-[-0.03em] font-extrabold mb-8">
              The world's largest outpatient system{' '}
              <span className="text-primary">still runs on paper.</span>
            </h1>
            <p className="text-[1.1rem] md:text-[1.2rem] text-slate-500 leading-[1.7] max-w-[58ch]">
              Lipi is a research-driven AI-native healthcare services company, starting with the
              OPD assistant for Indian clinics. A doctor speaks once, and Lipi turns that visit into
              doctor-reviewed records, prescriptions, test orders, follow-ups, patient communication,
              assistant tasks, and ABDM-ready documentation. Every clinical fact traces back to the
              exact sentence spoken.
            </p>
          </motion.div>
        </section>

        {/* ── Mission ──────────────────────────────────────────────── */}
        <motion.section
          initial={reduce ? false : 'hidden'}
          whileInView="visible"
          viewport={{ once: true, amount: 0.25 }}
          variants={fadeUp}
          className="py-16 border-t border-slate-200/60"
        >
          <div className="grid lg:grid-cols-[0.85fr_1.15fr] gap-10 lg:gap-16 items-start">
            <h2 className="text-[1.9rem] md:text-[2.2rem] font-bold tracking-tight leading-[1.06] max-w-[16ch]">
              Why the OPD comes first
            </h2>
            <div className="space-y-5 max-w-2xl">
              <p className="text-[15px] text-slate-600 leading-relaxed">
                Outpatient care is the highest-frequency workflow in Indian medicine. Every
                consultation creates a note, a prescription, follow-up instructions, and a record
                the system needs. Centralizing that work earns Lipi a place in the clinic on day
                one, and builds the doctor-approved clinical record that everything else compounds
                on.
              </p>
              <p className="text-[15px] text-slate-600 leading-relaxed">
                The service wedge is OPD administration. The research engine is doctor-reviewed
                clinical traces: what was spoken, what Lipi prepared, what the doctor corrected,
                what was sent to the patient, and what happened at follow-up. That is how a narrow
                clinic service becomes safer, more personalized healthcare AI over time.
              </p>
            </div>
          </div>
        </motion.section>

        {/* ── Research credibility ─────────────────────────────────── */}
        <section className="py-16 border-t border-slate-200/60">
          <motion.div
            initial={reduce ? false : 'hidden'}
            whileInView="visible"
            viewport={{ once: true, amount: 0.25 }}
            variants={fadeUp}
            className="mb-10 flex flex-col md:flex-row md:items-end md:justify-between gap-6"
          >
            <div>
              <h2 className="text-[1.9rem] md:text-[2.2rem] font-bold tracking-tight leading-[1.06] mb-3">
                The research arm
              </h2>
              <p className="text-[15px] text-slate-500 leading-relaxed max-w-[54ch]">
                Underneath the product, Lipi studies continual learning for doctor-gated healthcare
                AI services: prescribing safety tuned to Indian OPDs, Hinglish clinical NLP,
                antibiotic intelligence, and follow-up/outcome memory. Research earns its place
                only when it improves the assistant doctors use.
              </p>
            </div>
            <button
              onClick={() => navigate('/research')}
              className="group flex items-center gap-2 text-[13.5px] font-semibold text-primary shrink-0 cursor-pointer"
            >
              All research
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" strokeWidth={2} />
            </button>
          </motion.div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {RESEARCH_POSTS.map((post, i) => {
              const Icon = TRACK_ICONS[post.slug] ?? FileSearch;
              return (
                <motion.div
                  key={post.slug}
                  initial={reduce ? false : { opacity: 0, y: 16 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, amount: 0.2 }}
                  transition={{ duration: 0.45, delay: i * 0.06, ease: [0.16, 1, 0.3, 1] }}
                  whileHover={{ y: -4, transition: { duration: 0.2 } }}
                  onClick={() => navigate(`/research/${post.slug}`)}
                  className="group rounded-3xl border border-slate-200/80 bg-white p-6 cursor-pointer hover:border-primary/25 hover:shadow-[0_8px_40px_-16px_rgba(27,94,59,0.18)] transition-all duration-300 flex flex-col gap-4"
                >
                  <div className="w-9 h-9 rounded-xl bg-primary/8 grid place-items-center">
                    <Icon className="w-4.5 h-4.5 text-primary" strokeWidth={1.8} />
                  </div>
                  <div className="flex-1">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-primary/60 mb-2">{post.tag}</p>
                    <h3 className="text-[15px] font-bold leading-snug group-hover:text-primary transition-colors">{post.title}</h3>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-primary group-hover:translate-x-1 transition-all" strokeWidth={2} />
                </motion.div>
              );
            })}
          </div>
        </section>

        {/* ── Founder ──────────────────────────────────────────────── */}
        <motion.section
          initial={reduce ? false : 'hidden'}
          whileInView="visible"
          viewport={{ once: true, amount: 0.25 }}
          variants={fadeUp}
          className="py-16 border-t border-slate-200/60"
        >
          <div className="grid lg:grid-cols-[0.85fr_1.15fr] gap-10 lg:gap-16 items-start">
            <h2 className="text-[1.9rem] md:text-[2.2rem] font-bold tracking-tight leading-[1.06]">
              Built by one person,<br />on purpose
            </h2>
            <div className="max-w-2xl">
              <div className="flex items-start gap-5 mb-6">
                <div className="w-16 h-16 rounded-2xl bg-primary text-white grid place-items-center text-[1.4rem] font-extrabold shrink-0 shadow-sm">
                  AS
                </div>
                <div>
                  <p className="text-[16px] font-bold text-text-dark">Arush Singhal</p>
                  <p className="text-[13.5px] text-slate-500 mt-0.5">Founder</p>
                  <p className="text-[12.5px] text-slate-400 mt-1 flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5" strokeWidth={2} /> Building in Delhi, India
                  </p>
                </div>
              </div>
              <p className="text-[15px] text-slate-600 leading-relaxed mb-6">
                Lipi is a solo-founder company by design: one person who writes the code, sits in
                the clinics, reads the surveillance reports, and answers the doctors' WhatsApp
                messages. Small enough to ship weekly, close enough to the OPD floor that the
                product cannot drift from how Indian medicine actually works.
              </p>
              <a
                href="mailto:arushsinghal98@gmail.com?subject=Working%20at%20Lipi"
                className="group inline-flex items-center gap-2 text-[13.5px] font-semibold text-primary cursor-pointer"
              >
                We're hiring — write to us
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" strokeWidth={2} />
              </a>
            </div>
          </div>
        </motion.section>

        {/* ── Operating principles ─────────────────────────────────── */}
        <motion.section
          initial={reduce ? false : 'hidden'}
          whileInView="visible"
          viewport={{ once: true, amount: 0.2 }}
          variants={fadeUp}
          className="py-16 border-t border-slate-200/60"
        >
          <h2 className="text-[1.9rem] md:text-[2.2rem] font-bold tracking-tight leading-[1.06] mb-12">
            Operating principles
          </h2>
          <div className="grid md:grid-cols-3 gap-x-10 gap-y-10">
            {PRINCIPLES.map((p) => (
              <div key={p.n} className="border-t-2 border-primary/80 pt-6">
                <p className="text-[12px] font-bold font-mono text-primary/50 mb-3 tracking-wider">{p.n}</p>
                <h3 className="text-[17px] font-bold mb-3 leading-snug">{p.title}</h3>
                <p className="text-[14px] text-slate-500 leading-relaxed">{p.body}</p>
              </div>
            ))}
          </div>
        </motion.section>

        {/* ── Safety notice ────────────────────────────────────────── */}
        <motion.section
          initial={reduce ? false : 'hidden'}
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
          variants={fadeUp}
          className="pb-20"
        >
          <div className="rounded-3xl border border-slate-200/80 bg-white p-8 flex items-start gap-5 max-w-4xl">
            <div className="w-10 h-10 rounded-2xl bg-slate-100 grid place-items-center shrink-0">
              <ShieldCheck className="w-5 h-5 text-slate-500" strokeWidth={1.8} />
            </div>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-widest text-slate-400 mb-2">Clinical safety</p>
              <p className="text-[13.5px] text-slate-600 leading-relaxed">
                Lipi is an assistive clinical AI platform. It is not a certified medical device and
                does not replace professional clinical evaluation. All diagnoses, prescriptions, and
                notes remain under the sole signature and authority of the attending licensed
                provider.
              </p>
            </div>
          </div>
        </motion.section>
      </main>

      {/* ── Closing CTA ───────────────────────────────────────────── */}
      <section className="py-20 px-6 bg-primary">
        <div className="max-w-7xl mx-auto">
          <div className="max-w-2xl space-y-6">
            <motion.h2
              initial={reduce ? false : { opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
              className="text-[2rem] md:text-[2.5rem] font-extrabold text-white tracking-tight leading-[1.06]"
            >
              Onboarding pilot doctors and clinics directly
            </motion.h2>
            <motion.p
              initial={reduce ? false : { opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.08 }}
              className="text-[15px] text-white/65 leading-relaxed max-w-[48ch]"
            >
              The platform is live today; the research that deepens it runs continuously alongside
              it. Email us and we'll get you set up.
            </motion.p>
            <motion.div
              initial={reduce ? false : { opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.45, delay: 0.15 }}
            >
              <a
                href="mailto:arushsinghal98@gmail.com?subject=Lipi%20early%20access"
                className="inline-flex items-center gap-2 px-7 py-3.5 bg-white hover:bg-white/92 text-primary rounded-full font-bold text-[14.5px] transition-colors cursor-pointer"
              >
                Get in touch <ArrowRight className="w-4 h-4" />
              </a>
            </motion.div>
          </div>
        </div>
      </section>
    </div>
  );
}
