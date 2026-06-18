import { useState, type FormEvent, type MouseEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Mic,
  FileCheck,
  Cpu,
  ArrowRight,
  ShieldCheck,
  Database,
  Activity,
  Network
} from 'lucide-react';
import { InteractiveDemo } from '../components/InteractiveDemo';

interface DialectSample {
  speech: string;
  translation: string;
  entities: {
    symptoms: string[];
    vitals: string[];
    negated: string[];
  };
  resolution: string;
}

const DIALECT_SAMPLES: Record<'hinglish' | 'hindi' | 'english', DialectSample> = {
  hinglish: {
    speech: "Patient ko bukhar hai, around 102, but no chest pain, no vomiting... actually wait, usne kaha thoda dard hai.",
    translation: "Patient has fever (~102°F), but no chest pain and no vomiting. Note: patient reports mild pain.",
    entities: {
      symptoms: ["Fever (bukhar)", "Pain (dard)"],
      vitals: ["Temp 102°F"],
      negated: ["Chest Pain", "Vomiting"]
    },
    resolution: "Successfully resolved conversational self-correction (overrode pain-free state with 'mild pain') and mapped colloquial Hinglish terms ('bukhar' ➔ Fever, 'dard' ➔ Pain) to standard clinical classifications."
  },
  hindi: {
    speech: "मरीज को तीन दिन से खांसी है, और सर में भी तेज दर्द है। उल्टी नहीं हुई है।",
    translation: "Patient has had a cough for 3 days, and also has a severe headache. No vomiting.",
    entities: {
      symptoms: ["Cough (खांसी)", "Headache (सर दर्द)"],
      vitals: ["Duration: 3 days"],
      negated: ["Vomiting (उल्टी)"]
    },
    resolution: "Parsed regional Hindi script directly, identifying duration modifier ('तीन दिन' ➔ 3 days), symptoms ('खांसी' ➔ Cough, 'सर में दर्द' ➔ Headache), and filtering out negated symptom ('उल्टी नहीं' ➔ No vomiting)."
  },
  english: {
    speech: "Patient complains of severe chest pain spreading to left arm since 1 hour. No dizziness.",
    translation: "Patient complains of severe chest pain radiating to the left arm for 1 hour. No dizziness.",
    entities: {
      symptoms: ["Chest Pain (radiating)", "Arm Pain"],
      vitals: ["Duration: 1 hour"],
      negated: ["Dizziness"]
    },
    resolution: "Extracted clinical entities, mapped the radiating symptom path to both Chest and Arm anatomical sites, filtered out negated dizziness, and flagged potential cardiovascular check."
  }
};

const demoMailto = 'mailto:arushsinghal98@gmail.com?subject=Lipi Demo Request';

// Animation Variants
const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" as const } }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

export default function Landing() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'hinglish' | 'hindi' | 'english'>('hinglish');

  const [showAccessModal, setShowAccessModal] = useState(false);
  const [depName, setDepName] = useState('');
  const [depEmail, setDepEmail] = useState('');
  const [depOrg, setDepOrg] = useState('');
  const [depState, setDepState] = useState('Uttar Pradesh');
  const [depRole, setDepRole] = useState('Clinician / Doctor');

  const handleNavClick = (e: MouseEvent<HTMLAnchorElement>, id: string) => {
    e.preventDefault();
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleAccessSubmit = (e: FormEvent) => {
    e.preventDefault();
    const subject = encodeURIComponent(`Lipi access request from ${depOrg || depName}`);
    const body = encodeURIComponent(
      [
        `Name: ${depName}`,
        `Email: ${depEmail}`,
        `Organization: ${depOrg}`,
        `State: ${depState}`,
        `Role: ${depRole}`,
        '',
        `I would like to evaluate Lipi for my team. Role: ${depRole}.`
      ].join('\n')
    );
    window.location.href = `mailto:arushsinghal98@gmail.com?subject=${subject}&body=${body}`;
    closeAccessModal();
  };

  const closeAccessModal = () => {
    setShowAccessModal(false);
    setDepName('');
    setDepEmail('');
    setDepOrg('');
    setDepState('Uttar Pradesh');
    setDepRole('Clinician / Doctor');
  };

  return (
    <div className="min-h-screen bg-[#05070b] selection:bg-primary/30 font-sans text-slate-100 antialiased overflow-x-hidden">
      {/* Navigation */}
      <nav className="w-full px-6 py-4 border-b border-white/5 flex flex-col md:flex-row items-center justify-between glass-panel sticky top-0 z-[100] gap-4">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center shadow-[0_0_15px_rgba(27,94,59,0.5)]">
            <span className="text-white font-bold text-base">श</span>
          </div>
          <span className="text-base font-bold text-white tracking-tight">Lipi</span>
        </div>

        <div className="flex items-center gap-6 text-sm font-medium text-slate-400">
          <a href="#usecases" onClick={(e) => handleNavClick(e, 'usecases')} className="hover:text-white transition-colors">Use Cases</a>
          <a href="#platform" onClick={(e) => handleNavClick(e, 'platform')} className="hover:text-white transition-colors">How It Works</a>
          <a href="#architecture" onClick={(e) => handleNavClick(e, 'architecture')} className="hover:text-white transition-colors">Architecture</a>
          <a href="#safety" onClick={(e) => handleNavClick(e, 'safety')} className="hover:text-white transition-colors">Safety</a>
        </div>

        <div className="flex items-center gap-3">
          <a
            href={demoMailto}
            className="text-sm font-medium text-slate-300 hover:text-white hidden md:block px-3 py-2 transition-colors"
          >
            Contact Sales
          </a>
          <button
            onClick={() => navigate('/dashboard')}
            className="text-sm font-semibold bg-white hover:bg-slate-200 text-slate-950 px-4 py-2 rounded-md transition-transform active:scale-95 flex items-center gap-2 cursor-pointer"
          >
            Launch Console
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-24 pb-32 px-6 bg-glow-slate overflow-hidden">
        {/* Subtle Grid Background Visuals */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none"></div>
        <div className="max-w-5xl mx-auto text-center relative z-10">
          <motion.div 
            initial="hidden" animate="visible" variants={staggerContainer}
            className="space-y-8"
          >
            <motion.div variants={fadeUp} className="inline-flex items-center gap-2 rounded-full border-glow glass-panel px-3 py-1 text-xs font-medium text-slate-300 mb-4">
              <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Backed by Sarvam AI · Pilot live with 10+ doctors & 3 police stations
            </motion.div>

            <motion.h1 variants={fadeUp} className="text-5xl md:text-7xl font-bold tracking-tighter text-white leading-[1.05]">
              Speak. <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-200">Lipi writes.</span>
            </motion.h1>

            <motion.p variants={fadeUp} className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
              AI that turns spoken conversations into structured documents — SOAP notes for doctors, FIRs for police officers, legal filings for advocates. In any Indian language. On-device.
            </motion.p>

            <motion.div variants={fadeUp} className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="w-full sm:w-auto px-6 py-3 bg-white text-slate-950 hover:bg-slate-100 rounded-lg font-bold text-sm flex items-center justify-center gap-2 transition-all shadow-[0_0_20px_rgba(255,255,255,0.1)] hover:shadow-[0_0_30px_rgba(255,255,255,0.2)] cursor-pointer"
              >
                Open Lipi
                <ArrowRight className="w-4 h-4" />
              </button>
              <button
                onClick={() => setShowAccessModal(true)}
                className="w-full sm:w-auto px-6 py-3 bg-transparent hover:bg-white/5 text-white border-glow rounded-lg font-bold text-sm transition-colors cursor-pointer"
              >
                Request Pilot Access
              </button>
            </motion.div>
          </motion.div>

          {/* Hero Mockup */}
          <motion.div 
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.8, ease: "easeOut" }}
            className="mt-20 relative mx-auto max-w-4xl"
          >
            <InteractiveDemo />
          </motion.div>
        </div>
      </section>

      {/* Stats/Logos Strip */}
      <section className="border-y border-white/5 bg-white/[0.02]">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-wrap justify-center gap-x-12 gap-y-6 text-sm font-medium text-slate-400">
          <div className="flex items-center gap-2"><Mic className="w-4 h-4 text-emerald-400"/> 10+ Indian Languages</div>
          <div className="flex items-center gap-2"><Cpu className="w-4 h-4 text-emerald-400"/> Fully On-Device</div>
          <div className="flex items-center gap-2"><Database className="w-4 h-4 text-emerald-400"/> Health · Government · Legal</div>
          <div className="flex items-center gap-2"><ShieldCheck className="w-4 h-4 text-emerald-400"/> 0% Data Leakage</div>
        </div>
      </section>

      {/* Use Cases */}
      <section id="usecases" className="py-24 px-6">
        <div className="max-w-6xl mx-auto space-y-16">
          <div className="text-center space-y-4 max-w-2xl mx-auto">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white">One platform. Three professions.</h2>
            <p className="text-slate-400">The same voice → document pipeline, shaped for each workflow. Speak in any Indian language — Lipi writes the right document.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {/* Health */}
            <motion.div whileInView={{ opacity: 1, y: 0 }} initial={{ opacity: 0, y: 20 }} viewport={{ once: true }} className="glass-panel p-8 rounded-2xl space-y-4 hover:bg-white/[0.04] transition-colors border border-emerald-900/40">
              <div className="w-12 h-12 rounded-lg bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20 mb-2">
                <svg className="w-6 h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" /></svg>
              </div>
              <div className="inline-flex items-center gap-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-full px-2 py-0.5 text-[10px] font-bold text-emerald-400 uppercase tracking-wider">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block"></span> Pilot live · 10+ doctors
              </div>
              <h3 className="text-xl font-semibold text-white">Health</h3>
              <p className="text-slate-400 text-sm leading-relaxed">Doctor-patient consultation → structured SOAP note with vitals, symptoms, medications, allergy flags, and HL7 FHIR export. Works in Hindi, Hinglish, English.</p>
              <div className="pt-2 text-xs text-slate-500 font-mono">→ SOAP Note · CDS Alerts · FHIR R4</div>
            </motion.div>

            {/* Government */}
            <motion.div whileInView={{ opacity: 1, y: 0 }} initial={{ opacity: 0, y: 20 }} viewport={{ once: true }} transition={{ delay: 0.1 }} className="glass-panel p-8 rounded-2xl space-y-4 hover:bg-white/[0.04] transition-colors border border-stone-700/40">
              <div className="w-12 h-12 rounded-lg bg-stone-500/10 flex items-center justify-center border border-stone-500/20 mb-2">
                <svg className="w-6 h-6 text-stone-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              </div>
              <div className="inline-flex items-center gap-1.5 bg-stone-500/10 border border-stone-500/20 rounded-full px-2 py-0.5 text-[10px] font-bold text-stone-300 uppercase tracking-wider">
                <span className="w-1.5 h-1.5 rounded-full bg-stone-400 inline-block"></span> Pilot live · 3 stations
              </div>
              <h3 className="text-xl font-semibold text-white">Government</h3>
              <p className="text-slate-400 text-sm leading-relaxed">Officer dictates the complainant's account → Lipi generates a pre-filled FIR with IPC sections, accused details, witnesses, and incident summary — ready for registration.</p>
              <div className="pt-2 text-xs text-slate-500 font-mono">→ FIR Draft · IPC Sections · Printable</div>
            </motion.div>

            {/* Legal */}
            <motion.div whileInView={{ opacity: 1, y: 0 }} initial={{ opacity: 0, y: 20 }} viewport={{ once: true }} transition={{ delay: 0.2 }} className="glass-panel p-8 rounded-2xl space-y-4 hover:bg-white/[0.04] transition-colors border border-indigo-900/40">
              <div className="w-12 h-12 rounded-lg bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 mb-2">
                <svg className="w-6 h-6 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" /></svg>
              </div>
              <div className="inline-flex items-center gap-1.5 bg-indigo-500/10 border border-indigo-500/20 rounded-full px-2 py-0.5 text-[10px] font-bold text-indigo-400 uppercase tracking-wider">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 inline-block"></span> Coming to pilot
              </div>
              <h3 className="text-xl font-semibold text-white">Legal</h3>
              <p className="text-slate-400 text-sm leading-relaxed">Advocate dictates facts → Lipi generates affidavits, writ petitions, bail applications with parties, court details, cited sections, reliefs, and verification clause.</p>
              <div className="pt-2 text-xs text-slate-500 font-mono">→ Affidavit · Petition · Legal Notice</div>
            </motion.div>
          </div>

          {/* Capability strip below use cases */}
          <div className="grid md:grid-cols-2 gap-6">
            <motion.div whileInView={{ opacity: 1, y: 0 }} initial={{ opacity: 0, y: 20 }} viewport={{ once: true }} className="glass-panel p-8 rounded-2xl space-y-4 hover:bg-white/[0.04] transition-colors">
              <div className="w-12 h-12 rounded-lg bg-amber-500/10 flex items-center justify-center border border-amber-500/20 mb-6">
                <Activity className="w-6 h-6 text-amber-400" />
              </div>
              <h3 className="text-xl font-semibold text-white">Conversation State Resolution</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Lipi runs a deterministic state engine across all modes. If a speaker self-corrects — "actually, no, he was there" — the system supersedes the prior state and maintains a full audit trail. No hallucination, no omission.
              </p>
            </motion.div>

            <motion.div whileInView={{ opacity: 1, y: 0 }} initial={{ opacity: 0, y: 20 }} viewport={{ once: true }} transition={{ delay: 0.1 }} className="glass-panel p-8 rounded-2xl space-y-4 hover:bg-white/[0.04] transition-colors">
              <div className="w-12 h-12 rounded-lg bg-cyan-500/10 flex items-center justify-center border border-cyan-500/20 mb-6">
                <FileCheck className="w-6 h-6 text-cyan-400" />
              </div>
              <h3 className="text-xl font-semibold text-white">Expert-in-the-Loop Review</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Lipi drafts, structures, and flags. The doctor, officer, or advocate reviews the output, makes edits, signs off, and retains full accountability. AI accelerates; the professional decides.
              </p>
            </motion.div>

            <motion.div whileInView={{ opacity: 1, y: 0 }} initial={{ opacity: 0, y: 20 }} viewport={{ once: true }} transition={{ delay: 0.2 }} className="glass-panel p-8 rounded-2xl space-y-4 hover:bg-white/[0.04] transition-colors">
              <div className="w-12 h-12 rounded-lg bg-blue-500/10 flex items-center justify-center border border-blue-500/20 mb-6">
                <Network className="w-6 h-6 text-blue-400" />
              </div>
              <h3 className="text-xl font-semibold text-white">Structured Export</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Every document is printable and exportable. Health → HL7 FHIR R4, ABDM-compatible. Government → FIR PDF. Legal → court-ready draft. Nothing is locked in a proprietary format.
              </p>
            </motion.div>

            <motion.div whileInView={{ opacity: 1, y: 0 }} initial={{ opacity: 0, y: 20 }} viewport={{ once: true }} transition={{ delay: 0.3 }} className="glass-panel p-8 rounded-2xl space-y-4 hover:bg-white/[0.04] transition-colors">
              <div className="w-12 h-12 rounded-lg bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20 mb-6">
                <ShieldCheck className="w-6 h-6 text-emerald-400" />
              </div>
              <h3 className="text-xl font-semibold text-white">Zero Data Leakage</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Extraction, structuring, and safety checks all run locally on-device. No audio or document content is ever transmitted to a third-party cloud. Full data sovereignty for sensitive professional workflows.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Interactive Dialect Demo */}
      <section id="platform" className="py-24 px-6 bg-glow-primary">
        <div className="max-w-5xl mx-auto space-y-12">
          <div className="text-center space-y-4">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white">Built for how India actually speaks.</h2>
            <p className="text-slate-400">Hindi, Hinglish, English — Lipi's local NLP handles code-switching, self-corrections, and regional vocabulary natively.</p>
          </div>

          <motion.div whileInView={{ opacity: 1, y: 0 }} initial={{ opacity: 0, y: 20 }} viewport={{ once: true }} className="glass-panel rounded-2xl border border-emerald-500/20 overflow-hidden shadow-[0_0_40px_rgba(27,94,59,0.1)]">
            <div className="flex border-b border-white/5 bg-black/40 px-4 pt-4 gap-2 overflow-x-auto">
              {(['hinglish', 'hindi', 'english'] as const).map((lang) => (
                <button
                  key={lang}
                  onClick={() => setActiveTab(lang)}
                  className={`px-4 py-2 text-xs font-semibold uppercase tracking-wider rounded-t-lg transition-colors cursor-pointer ${
                    activeTab === lang
                      ? 'bg-[#05070b] text-emerald-400 border-x border-t border-white/10'
                      : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {lang}
                </button>
              ))}
            </div>

            <div className="p-6 md:p-8 space-y-8 bg-[#05070b]/80">
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs font-mono text-slate-500 uppercase">
                  <Mic className="w-3 h-3"/> Raw Ingestion
                </div>
                <p className="text-lg text-white font-medium italic">"{DIALECT_SAMPLES[activeTab].speech}"</p>
              </div>

              <div className="space-y-4 pt-6 border-t border-white/5">
                <div className="flex items-center gap-2 text-xs font-mono text-emerald-500 uppercase">
                  <Cpu className="w-3 h-3"/> Structured Output
                </div>
                
                <div className="grid md:grid-cols-3 gap-4">
                   <div className="bg-white/5 border border-white/10 rounded-lg p-4">
                      <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-3">Symptoms</span>
                      <div className="space-y-2">
                        {DIALECT_SAMPLES[activeTab].entities.symptoms.map(s => (
                          <div key={s} className="text-sm font-medium text-emerald-100 flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400"></div>{s}
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="bg-white/5 border border-white/10 rounded-lg p-4">
                      <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-3">Vitals / Context</span>
                      <div className="space-y-2">
                        {DIALECT_SAMPLES[activeTab].entities.vitals.map(v => (
                          <div key={v} className="text-sm font-medium text-blue-200 flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-blue-400"></div>{v}
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="bg-white/5 border border-white/10 rounded-lg p-4">
                      <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-3">Negated</span>
                      <div className="space-y-2">
                        {DIALECT_SAMPLES[activeTab].entities.negated.map(n => (
                          <div key={n} className="text-sm font-medium text-slate-500 line-through flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-slate-600"></div>{n}
                          </div>
                        ))}
                      </div>
                    </div>
                </div>
              </div>

              <div className="pt-6 border-t border-white/5">
                 <div className="flex items-center gap-2 text-xs font-mono text-amber-500 uppercase mb-2">
                  <Activity className="w-3 h-3"/> State Engine Resolution
                </div>
                <p className="text-sm text-slate-300 leading-relaxed">
                  {DIALECT_SAMPLES[activeTab].resolution}
                </p>
              </div>

            </div>
          </motion.div>
        </div>
      </section>

      {/* Architecture & Future */}
      <section id="architecture" className="py-24 px-6">
         <div className="max-w-6xl mx-auto grid lg:grid-cols-2 gap-16 items-center">
            <div className="space-y-8">
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white">The architecture is local. The roadmap is proprietary.</h2>
              <p className="text-slate-400 leading-relaxed">
                Lipi is not a wrapper around a generic chatbot. The platform creates the data interface, expert review loop, and safety boundary needed to build proprietary AI systems for high-stakes professional workflows — without handing sensitive content to generic model providers.
              </p>
              <ul className="space-y-4">
                {[
                  'Local NLP extraction (spaCy + domain rules) prevents cloud leakage.',
                  'Source-linked audit trails preserve professional trust and accountability.',
                  'Roadmap: private domain-specific LLMs for health, law, and government.'
                ].map((item, i) => (
                  <motion.li 
                    key={i} 
                    initial={{ opacity: 0, x: -20 }} 
                    whileInView={{ opacity: 1, x: 0 }} 
                    viewport={{ once: true }} 
                    transition={{ delay: i * 0.1 }}
                    className="flex items-start gap-3 text-slate-300 text-sm"
                  >
                    <div className="mt-1 w-5 h-5 rounded-full bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-400"></div>
                    </div>
                    {item}
                  </motion.li>
                ))}
              </ul>
            </div>
            <div className="relative">
               <div className="glass-panel rounded-2xl p-6 border-glow shadow-2xl">
                  <div className="space-y-6">
                    {/* Pipeline Mockup */}
                    <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/5">
                      <span className="text-sm font-semibold text-white">1. Audio Ingestion</span>
                      <span className="text-xs text-slate-500 font-mono bg-black/50 px-2 py-1 rounded">Edge / Browser</span>
                    </div>
                    <div className="h-4 w-px bg-emerald-500/30 mx-auto"></div>
                     <div className="flex items-center justify-between p-4 bg-emerald-500/10 rounded-lg border border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
                      <span className="text-sm font-semibold text-emerald-400">2. Structured Extraction</span>
                      <span className="text-xs text-emerald-500/70 font-mono bg-emerald-500/10 px-2 py-1 rounded">Local Engine</span>
                    </div>
                    <div className="h-4 w-px bg-white/10 mx-auto"></div>
                     <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/5">
                      <span className="text-sm font-semibold text-white">3. Format & Review</span>
                      <span className="text-xs text-slate-500 font-mono bg-black/50 px-2 py-1 rounded">Expert Review UI</span>
                    </div>
                  </div>
               </div>
            </div>
         </div>
      </section>

      {/* Safety Banner */}
      <section id="safety" className="py-12 px-6 bg-red-950/20 border-y border-red-900/30">
        <div className="max-w-4xl mx-auto text-center space-y-4">
           <ShieldCheck className="w-8 h-8 text-red-400 mx-auto" />
           <h3 className="text-lg font-bold text-red-200">Important Notice</h3>
           <p className="text-sm text-red-200/70 leading-relaxed">
             Lipi is an assistive documentation tool. AI-generated drafts require review and sign-off by the relevant professional — physician, officer, or advocate — before any official or clinical use. Output is not a substitute for professional judgment.
           </p>
        </div>
      </section>

      {/* Pricing / Access */}
      <section className="py-32 px-6 bg-glow-slate relative overflow-hidden">
         <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-5 pointer-events-none mix-blend-overlay"></div>
         <div className="max-w-4xl mx-auto text-center space-y-12 relative z-10">
            <h2 className="text-4xl font-bold tracking-tight text-white">Ready for evaluation.</h2>
            <p className="text-slate-400">We onboard early teams across health, government, and legal directly.</p>

            <div className="glass-panel border-glow p-8 md:p-12 rounded-3xl max-w-2xl mx-auto text-center space-y-8 shadow-[0_0_50px_rgba(0,0,0,0.5)]">
               <h3 className="text-2xl font-semibold text-white">Enterprise & Accelerator Access</h3>
               <p className="text-slate-300 text-sm leading-relaxed">
                 Access the live Lipi platform, evaluate the local extraction architecture, and review the multi-domain AI roadmap.
               </p>
               <button
                  onClick={() => setShowAccessModal(true)}
                  className="w-full sm:w-auto px-8 py-4 bg-white text-slate-950 hover:bg-slate-200 rounded-lg font-bold text-sm transition-all shadow-lg hover:shadow-[0_0_20px_rgba(255,255,255,0.3)] cursor-pointer"
                >
                  Request Full Briefing
                </button>
            </div>
         </div>
      </section>

      {/* Footer */}
      <footer className="py-8 text-center text-xs text-slate-600 border-t border-white/5 space-y-1">
        <p>© 2026 Lipi · Backed by Sarvam AI · Speak in any language — Lipi writes the document.</p>
        <p>
          <a href="/privacy" className="underline hover:text-slate-400 transition-colors">
            Privacy Policy
          </a>
        </p>
      </footer>

      {/* Access Modal */}
      {showAccessModal && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-[#0b0f19] rounded-2xl p-8 max-w-md w-full border border-white/10 relative shadow-2xl"
          >
            <button
              onClick={closeAccessModal}
              className="absolute top-6 right-6 text-slate-500 hover:text-white transition-colors cursor-pointer"
            >
              ✕
            </button>
            <h3 className="text-xl font-bold text-white mb-2">Request Access</h3>
            <p className="text-sm text-slate-400 mb-6">Enter details to evaluate the platform.</p>
            
            <form onSubmit={handleAccessSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1 uppercase tracking-wider">Name</label>
                <input required type="text" value={depName} onChange={e => setDepName(e.target.value)} className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500/50 transition-colors" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1 uppercase tracking-wider">Email</label>
                <input required type="email" value={depEmail} onChange={e => setDepEmail(e.target.value)} className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500/50 transition-colors" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1 uppercase tracking-wider">Organization</label>
                <input required type="text" value={depOrg} onChange={e => setDepOrg(e.target.value)} className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500/50 transition-colors" />
              </div>
              <button type="submit" className="w-full bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold py-3 rounded-lg mt-4 transition-colors cursor-pointer">
                Submit Request
              </button>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
}
