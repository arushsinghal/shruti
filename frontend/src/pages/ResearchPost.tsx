import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, ArrowRight, FileSearch, Network, Pill, Radar } from 'lucide-react';
import { RESEARCH_POSTS } from '../data/researchPosts';

const ICONS: Record<string, React.ElementType> = {
  'drug-safety-indian-formularies': Pill,
  'amr-surveillance-gap': Radar,
  'hinglish-clinical-nlp': Network,
  'indian-opd-ontology': FileSearch,
};

function PullQuote({ text }: { text: string }) {
  return (
    <motion.blockquote
      initial={{ opacity: 0, x: -8 }}
      whileInView={{ opacity: 1, x: 0 }}
      viewport={{ once: true, amount: 0.5 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="my-14 pl-7 border-l-[3px] border-primary"
    >
      <p className="text-[1.15rem] md:text-[1.25rem] font-medium text-text-dark leading-[1.55] italic">
        &ldquo;{text}&rdquo;
      </p>
    </motion.blockquote>
  );
}

export default function ResearchPost() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const post = RESEARCH_POSTS.find(p => p.slug === slug);

  if (!post) {
    return (
      <div className="min-h-screen bg-bg-warm flex items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-slate-500 text-sm">Post not found.</p>
          <button
            onClick={() => navigate('/research')}
            className="text-primary text-sm font-semibold hover:underline cursor-pointer"
          >
            Back to research
          </button>
        </div>
      </div>
    );
  }

  const Icon = ICONS[post.slug] ?? FileSearch;

  return (
    <div className="min-h-screen bg-bg-warm font-sans text-text-dark antialiased">

      {/* ── Sticky nav ─────────────────────────────────────────────── */}
      <nav className="sticky top-0 z-[100] border-b border-slate-200/60 bg-bg-warm/90 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between gap-4">
          <button
            onClick={() => navigate('/research')}
            className="flex items-center gap-2 text-[13px] font-medium text-slate-500 hover:text-text-dark transition-colors cursor-pointer group"
          >
            <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" strokeWidth={2} />
            Research
          </button>
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 cursor-pointer group"
          >
            <span className="grid place-items-center w-7 h-7 rounded-lg bg-primary text-white font-bold text-xs shadow-sm group-hover:scale-105 transition-transform">श</span>
            <span className="text-[15px] font-bold tracking-tight text-text-dark hidden sm:block">Lipi</span>
          </button>
          <motion.a
            href="mailto:arushsinghal98@gmail.com?subject=Lipi%20research%20inquiry"
            whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
            className="text-[12.5px] font-semibold bg-primary text-white pl-3.5 pr-3 py-1.5 rounded-full flex items-center gap-1 cursor-pointer transition-colors shadow-sm"
          >
            Get in touch <ArrowRight className="w-3.5 h-3.5" />
          </motion.a>
        </div>
      </nav>

      {/* ── Hero ─────────────────────────────────────────────────────── */}
      <header className="border-b border-slate-200/60">
        <div className="max-w-6xl mx-auto px-6 py-16 md:py-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
            className="max-w-3xl"
          >
            {/* Tag + icon */}
            <div className="flex items-center gap-3 mb-8">
              <div className="w-9 h-9 rounded-xl bg-primary/10 grid place-items-center shrink-0">
                <Icon className="w-4.5 h-4.5 text-primary" strokeWidth={1.8} />
              </div>
              <span className="text-[11px] font-bold uppercase tracking-widest text-primary/80">
                {post.tag}
              </span>
            </div>

            {/* Title */}
            <h1 className="text-[2.4rem] md:text-[3.2rem] font-extrabold tracking-[-0.025em] leading-[1.06] mb-7 text-text-dark">
              {post.title}
            </h1>

            {/* Lead paragraph — larger than body */}
            <p className="text-[1.1rem] md:text-[1.2rem] text-slate-500 leading-[1.7] max-w-[60ch]">
              {post.intro}
            </p>
          </motion.div>
        </div>
      </header>

      {/* ── Hero stat (AMR only) ─────────────────────────────────────── */}
      {post.heroStat && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.15 }}
          className="border-b border-slate-200/60 bg-primary"
        >
          <div className="max-w-6xl mx-auto px-6 py-14 md:py-20">
            <div className="max-w-3xl">
              <p className="text-[4rem] md:text-[5.5rem] font-extrabold tracking-tight text-white leading-none mb-4">
                {post.heroStat.value}
              </p>
              <p className="text-[15px] font-semibold text-white/80 mb-2">{post.heroStat.label}</p>
              <p className="text-[13.5px] text-white/55 leading-relaxed max-w-[52ch]">
                {post.heroStat.sublabel}
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* ── Article body ─────────────────────────────────────────────── */}
      <main className="max-w-6xl mx-auto px-6 py-16 md:py-24">
        <div className="max-w-3xl space-y-20">
          {post.sections.map((section, i) => (
            <div key={section.heading}>
              <motion.article
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.2 }}
                transition={{ duration: 0.5, delay: i * 0.04, ease: [0.16, 1, 0.3, 1] }}
              >
                <h2 className="text-[1.2rem] md:text-[1.35rem] font-bold text-text-dark tracking-tight leading-snug mb-5">
                  {section.heading}
                </h2>
                <p className="text-[15.5px] text-slate-600 leading-[1.8]">
                  {section.body}
                </p>

                {section.image && (
                  <figure className="mt-10 -mx-6 md:-mx-12">
                    <div className="rounded-2xl md:rounded-3xl border border-slate-200/70 overflow-hidden bg-slate-50 shadow-[0_4px_32px_-8px_rgba(0,0,0,0.08)]">
                      <img
                        src={section.image.src}
                        alt={section.image.alt}
                        className="w-full h-auto block"
                        loading="lazy"
                      />
                    </div>
                    <figcaption className="mt-3 px-6 md:px-12 text-[12px] text-slate-400 leading-relaxed">
                      {section.image.caption}
                    </figcaption>
                  </figure>
                )}
              </motion.article>

              {/* Pull quote injected after the specified section */}
              {post.pullQuote && post.pullQuote.afterSection === i && (
                <PullQuote text={post.pullQuote.text} />
              )}
            </div>
          ))}
        </div>

        {/* ── Key findings ─────────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="max-w-3xl mt-20 rounded-3xl bg-primary/[0.04] border border-primary/15 p-8 md:p-10"
        >
          <p className="text-[11px] font-bold uppercase tracking-widest text-primary/70 mb-6">
            Key findings
          </p>
          <ul className="space-y-4">
            {post.keyFindings.map((f, i) => (
              <li key={i} className="flex items-start gap-3.5">
                <span className="mt-[7px] w-1.5 h-1.5 rounded-full bg-primary shrink-0" />
                <span className="text-[14.5px] text-slate-700 leading-relaxed">{f}</span>
              </li>
            ))}
          </ul>
        </motion.div>

        {/* ── Back link ────────────────────────────────────────────── */}
        <div className="max-w-3xl mt-16 pt-10 border-t border-slate-200/60">
          <button
            onClick={() => navigate('/research')}
            className="group flex items-center gap-2.5 text-[13.5px] font-semibold text-slate-500 hover:text-primary transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" strokeWidth={2} />
            All research
          </button>
        </div>
      </main>

      {/* ── Footer CTA ───────────────────────────────────────────────── */}
      <footer className="bg-primary mt-8">
        <div className="max-w-6xl mx-auto px-6 py-16">
          <div className="max-w-2xl">
            <p className="text-[11px] font-bold uppercase tracking-widest text-white/40 mb-4">
              Research collaborations
            </p>
            <h2 className="text-[1.8rem] md:text-[2.2rem] font-extrabold text-white tracking-tight leading-[1.08] mb-6">
              Interested in this work? We are open to institutional partnerships and data-sharing agreements.
            </h2>
            <a
              href="mailto:arushsinghal98@gmail.com?subject=Lipi%20research%20inquiry"
              className="inline-flex items-center gap-2 bg-white text-primary font-bold text-[14px] px-6 py-3 rounded-full hover:bg-white/92 transition-colors cursor-pointer"
            >
              Get in touch <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
