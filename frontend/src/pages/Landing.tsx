import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useScrollReveal, useCountUp } from '../lib/animations';

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

export default function Landing() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'hinglish' | 'hindi' | 'english'>('hinglish');
  const [scrollPct, setScrollPct] = useState(0);

  useScrollReveal();

  // Scroll progress bar
  useEffect(() => {
    const onScroll = () => {
      const el = document.documentElement;
      const scrolled = el.scrollTop;
      const total = el.scrollHeight - el.clientHeight;
      setScrollPct(total > 0 ? (scrolled / total) * 100 : 0);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Animated counters
  const countRatio = useCountUp(1457, 2000);
  const countTime = useCountUp(40, 1600, '%');
  const countDialects = useCountUp(22, 1400, '+');
  
  // Modals state
  const [showDeploymentModal, setShowDeploymentModal] = useState(false);
  const [showSponsorModal, setShowSponsorModal] = useState(false);
  
  // Submit state
  const [deploymentSubmitted, setDeploymentSubmitted] = useState(false);
  const [sponsorSubmitted, setSponsorSubmitted] = useState(false);

  // Form inputs
  const [depName, setDepName] = useState('');
  const [depEmail, setDepEmail] = useState('');
  const [depOrg, setDepOrg] = useState('');
  const [depState, setDepState] = useState('Uttar Pradesh');
  const [depRole, setDepRole] = useState('NGO Partner');

  const [sponName, setSponName] = useState('');
  const [sponEmail, setSponEmail] = useState('');
  const [sponQuantity, setSponQuantity] = useState(1);

  const handleNavClick = (e: React.MouseEvent<HTMLAnchorElement>, id: string) => {
    e.preventDefault();
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleDeploymentSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const subject = encodeURIComponent(`SHRUTI deployment inquiry from ${depOrg || depName}`);
    const body = encodeURIComponent(
      [
        `Name: ${depName}`,
        `Email: ${depEmail}`,
        `Organization: ${depOrg}`,
        `Target state: ${depState}`,
        `Role: ${depRole}`,
        '',
        'I would like to discuss SHRUTI clinic deployment.'
      ].join('\n')
    );
    window.location.href = `mailto:arushsinghal98@gmail.com?subject=${subject}&body=${body}`;
    setDeploymentSubmitted(true);
  };

  const handleSponsorSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const subject = encodeURIComponent(`SHRUTI camp kit sponsorship from ${sponName}`);
    const body = encodeURIComponent(
      [
        `Sponsor: ${sponName}`,
        `Email: ${sponEmail}`,
        `Camp kits pledged: ${sponQuantity}`,
        `Estimated pledge: $${sponQuantity * 250}`,
        '',
        'I would like to discuss SHRUTI camp kit sponsorship.'
      ].join('\n')
    );
    window.location.href = `mailto:arushsinghal98@gmail.com?subject=${subject}&body=${body}`;
    setSponsorSubmitted(true);
  };

  const closeDeploymentModal = () => {
    setShowDeploymentModal(false);
    setDeploymentSubmitted(false);
    setDepName('');
    setDepEmail('');
    setDepOrg('');
  };

  const closeSponsorModal = () => {
    setShowSponsorModal(false);
    setSponsorSubmitted(false);
    setSponName('');
    setSponEmail('');
    setSponQuantity(1);
  };

  // DisclaimerBar removed from section footers — now only in main footer


  return (
    <div className="min-h-screen bg-bg-warm selection:bg-primary/10 font-sans text-text-dark antialiased">

      {/* Scroll Progress Bar */}
      <div
        className="fixed top-0 left-0 z-50 h-[3px] bg-gradient-to-r from-primary via-accent to-primary transition-all duration-100"
        style={{ width: `${scrollPct}%` }}
      />
      
      {/* Sticky Navigation */}
      <nav className="w-full px-6 py-3 border-b border-slate-200/80 flex flex-col md:flex-row items-center justify-between bg-white/90 backdrop-blur-md sticky top-0 z-40 gap-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary rounded flex items-center justify-center shadow-xs">
            <span className="text-white font-serif font-bold text-lg">श</span>
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="text-base font-bold text-text-dark tracking-tight">SHRUTI Health</span>
              <span className="bg-primary/10 text-primary border border-primary/20 px-1.5 py-0.2 rounded text-[8px] font-bold uppercase tracking-wider">
                Field-Deployed Venture
              </span>
            </div>
            <div className="hidden lg:flex items-center gap-2">
              <span className="text-[10px] text-slate-500 font-semibold">
                Voice-first clinical infrastructure for underserved clinics
              </span>
            </div>
          </div>
        </div>
        
        {/* Navigation Links */}
        <div className="flex items-center flex-wrap justify-center gap-x-5 gap-y-2 text-xs font-bold text-slate-600">
          <a href="#mission" onClick={(e) => handleNavClick(e, 'mission')} className="hover:text-primary transition-colors">Our Mission</a>
          <a href="#crisis" onClick={(e) => handleNavClick(e, 'crisis')} className="hover:text-primary transition-colors">The Crisis</a>
          <a href="#solution" onClick={(e) => handleNavClick(e, 'solution')} className="hover:text-primary transition-colors">Our Solution</a>
          <a href="#safety-tech" onClick={(e) => handleNavClick(e, 'safety-tech')} className="hover:text-primary transition-colors">Safety & Tech</a>
          <a href="#scale" onClick={(e) => handleNavClick(e, 'scale')} className="hover:text-primary transition-colors">Scaling Impact</a>
        </div>

        <div className="flex items-center gap-2">
          <a
            href="mailto:arushsinghal98@gmail.com?subject=SHRUTI Demo Request"
            className="text-xs font-semibold border border-primary text-primary hover:bg-primary/5 px-3 py-2 rounded transition-all hidden md:block"
          >
            Book a Demo
          </a>
          <button
            onClick={() => navigate('/dashboard')}
            className="text-xs font-semibold bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded transition-all shadow-sm cursor-pointer"
          >
            Launch Console
          </button>
        </div>
      </nav>

      {/* SECTION 1: OUR MISSION */}
      <section id="mission" className="hero-mesh min-h-[calc(100vh-56px)] flex flex-col justify-between pt-16">
        <div className="max-w-5xl mx-auto px-6 flex-grow flex flex-col justify-center">
          <div className="reveal inline-flex flex-wrap items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-bold uppercase tracking-widest mb-6 w-fit">
            <span className="flex h-2 w-2 rounded-full bg-accent animate-pulse"></span>
            Clinic-Deployed Social Venture
            <span className="text-slate-300">|</span>
            <span className="text-accent-dark">Available for clinic partnerships</span>
          </div>

          <div className="grid lg:grid-cols-[1.2fr_0.8fr] gap-10 items-center mb-12">
            <div className="reveal-left space-y-6">
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-text-dark tracking-tight leading-tight" style={{ fontFamily: '"Playfair Display", Georgia, serif' }}>
                Voice-to-SOAP infrastructure for clinics that cannot wait.
              </h1>
              <p className="text-base md:text-lg text-slate-600 leading-relaxed font-light">
                <span className="font-semibold text-primary">SHRUTI</span> is a field-deployed social venture helping clinicians in rural and high-throughput clinics turn Hindi, English, and Hinglish consultations into doctor-reviewed SOAP records. The product combines passive voice capture, local clinical extraction, safety checks, and FHIR-ready export so providers can spend more time with patients and less time writing notes.
              </p>

              {/* Live processing indicator */}
              <div className="grid sm:grid-cols-3 gap-2 py-2">
                <div className="flex items-center gap-2 bg-slate-900 text-white px-3 py-2 rounded text-[11px] font-bold">
                  <span className="flex h-2 w-2 rounded-full bg-accent animate-pulse"></span>
                  <span>Live Clinic Workflow</span>
                </div>
                <div className="flex items-center gap-2 bg-white border border-slate-200 text-slate-700 px-3 py-2 rounded text-[11px] font-bold">
                  <span className="text-primary">✓</span>
                  <span>Doctor Review Required</span>
                </div>
                <div className="flex items-center gap-2 bg-white border border-slate-200 text-slate-700 px-3 py-2 rounded text-[11px] font-bold">
                  <span className="text-primary">✓</span>
                  <span>Partnering With Clinics</span>
                </div>
              </div>
              

              <div className="flex flex-wrap items-center gap-4 pt-2">
                <button
                  onClick={() => navigate('/dashboard')}
                  className="px-6 py-3 bg-primary hover:bg-primary-dark text-white rounded font-bold text-sm transition-all shadow-md hover:shadow-lg flex items-center gap-2 cursor-pointer"
                >
                  Launch Clinician Console
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
                <a
                  href="#scale"
                  onClick={(e) => handleNavClick(e, 'scale')}
                  className="px-6 py-3 bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 rounded font-bold text-sm transition-all shadow-xs text-center"
                >
                  See Traction & Scale
                </a>
              </div>
            </div>


            {/* Hero Image: Rural Health Camp */}
            <div className="reveal-right relative rounded-xl overflow-hidden shadow-xl border border-slate-200 group">
              <img
                src="/rural_doctor_hero.png"
                alt="Doctor examining a patient at a rural health camp in India"
                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                style={{ maxHeight: '380px' }}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
              <div className="absolute top-4 left-4 flex flex-col gap-2">
                <span className="w-fit bg-white/95 text-primary border border-white/70 px-2.5 py-1 rounded text-[10px] font-extrabold uppercase tracking-wider shadow-sm">
                  Clinic-deployed venture
                </span>
                <span className="w-fit bg-slate-950/85 text-white px-2.5 py-1 rounded text-[10px] font-bold uppercase tracking-wider">
                  Hindi / Hinglish / English
                </span>
              </div>
              <div className="absolute bottom-0 left-0 right-0 p-4">
                <p className="text-white text-[11px] font-semibold leading-relaxed drop-shadow-sm">
                  A clinician-facing system built for rural health camps, small clinics, and high-volume outpatient settings.
                </p>
              </div>
            </div>
          </div>

          {/* Field traction strip */}
          <div className="grid md:grid-cols-3 gap-4 mb-8">
            {[
              {
                label: 'Deployment Signal',
                value: 'Clinic deployment',
                body: 'SHRUTI is already deployed in clinical workflows and available for clinic, NGO, and public-health partnerships.'
              },
              {
                label: 'Product Signal',
                value: 'Working console',
                body: 'Audio capture, transcript review, structured extraction, SOAP editing, CDS alerts, PDF export, and FHIR payloads.'
              },
              {
                label: 'Validation Signal',
                value: 'Field feedback loop',
                body: 'The product is shaped around doctor workflow constraints, clinic throughput, and responsible physician-in-the-loop use.'
              },
            ].map(({ label, value, body }) => (
              <div key={label} className="reveal bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
                <p className="text-[9px] font-extrabold text-primary uppercase tracking-widest mb-1">{label}</p>
                <h3 className="font-serif font-bold text-text-dark text-base mb-1">{value}</h3>
                <p className="text-[11px] text-slate-500 leading-relaxed">{body}</p>
              </div>
            ))}
          </div>

          <div className="mb-8 rounded-lg border border-accent/30 bg-accent/10 p-4 grid md:grid-cols-[1.1fr_0.9fr] gap-4 items-center">
            <div>
              <p className="text-[10px] font-extrabold uppercase tracking-widest text-accent-dark mb-1">Deployment & Partnerships</p>
              <h3 className="font-serif font-bold text-text-dark text-lg">Deployed in clinics and open for new partnerships.</h3>
              <p className="text-xs text-slate-600 leading-relaxed mt-2">
                SHRUTI is being used in clinical workflows and is now expanding through clinic, NGO, and health-camp partnerships. Public pages keep partner identities private unless a partner chooses to be named.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div className="bg-white border border-accent/20 rounded p-3">
                <span className="font-bold text-primary block">Clinic-deployed</span>
                <span className="text-slate-500">Live workflow</span>
              </div>
              <div className="bg-white border border-accent/20 rounded p-3">
                <span className="font-bold text-primary block">Partnership-ready</span>
                <span className="text-slate-500">Clinics and NGOs</span>
              </div>
              <div className="bg-white border border-accent/20 rounded p-3">
                <span className="font-bold text-primary block">Founder-led</span>
                <span className="text-slate-500">Built by Arush</span>
              </div>
              <div className="bg-white border border-accent/20 rounded p-3">
                <span className="font-bold text-primary block">Privacy held</span>
                <span className="text-slate-500">Names shared privately</span>
              </div>
            </div>
          </div>

          {/* Home Stats — Animated Counters */}
          <div className="grid md:grid-cols-3 gap-6 py-10 border-t border-slate-150">
            <div className="reveal reveal-delay-1 bg-bg-warm/50 border border-slate-200/80 rounded p-6 shadow-2xs hover:shadow-xs transition-shadow">
              <h3 className="text-3xl font-bold font-mono mb-1 stat-number">
                1 : <span ref={countRatio}>0</span>
              </h3>
              <p className="text-xs text-slate-500 font-semibold mb-1">Rural Doctor Shortage</p>
              <p className="text-xs text-slate-400">The structural shortage that turns documentation into a care-time crisis.</p>
            </div>
            
            <div className="reveal reveal-delay-2 bg-bg-warm/50 border border-slate-200/80 rounded p-6 shadow-2xs hover:shadow-xs transition-shadow">
              <h3 className="text-3xl font-bold font-mono mb-1 stat-number">
                <span ref={countTime}>0</span>
              </h3>
              <p className="text-xs text-slate-500 font-semibold mb-1">Documentation Burden</p>
              <p className="text-xs text-slate-400">Estimated share of clinician time often lost to writing, typing, and formatting records.</p>
            </div>
            
            <div className="reveal reveal-delay-3 bg-bg-warm/50 border border-slate-200/80 rounded p-6 shadow-2xs hover:shadow-xs transition-shadow">
              <h3 className="text-3xl font-bold font-mono mb-1" style={{ color: 'var(--color-accent)' }}>
                <span ref={countDialects}>0</span>
              </h3>
              <p className="text-xs text-slate-500 font-semibold mb-1">Language Expansion Target</p>
              <p className="text-xs text-slate-400">A scale goal for dialect-inclusive documentation across underserved Indian care settings.</p>
            </div>
          </div>

          {/* Tech credibility strip */}
          <div className="border-t border-slate-100 pt-8 pb-4">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest text-center mb-4">Powered by & Compatible with</p>
            <div className="flex flex-wrap items-center justify-center gap-6">
              {[
                { label: 'Local NLP Core', icon: '✦', color: 'text-blue-600' },
                { label: 'Sarvam AI', icon: '◈', color: 'text-purple-600' },
                { label: 'HL7 FHIR R4', icon: '⬡', color: 'text-green-700' },
                { label: 'India ABDM', icon: '◎', color: 'text-orange-600' },
                { label: 'FastAPI', icon: '⚡', color: 'text-teal-600' },
                { label: 'Physician Review', icon: '⊛', color: 'text-slate-700' },
              ].map(({ label, icon, color }) => (
                <div key={label} className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white border border-slate-200 shadow-2xs hover:shadow-xs transition-shadow">
                  <span className={`text-sm font-bold ${color}`}>{icon}</span>
                  <span className="text-[11px] font-semibold text-slate-600">{label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 2: THE CRISIS */}
      <section id="crisis" className="min-h-screen flex flex-col justify-between pt-20 bg-bg-warm">
        <div className="max-w-5xl mx-auto px-6 py-10 flex-grow space-y-12">
          <div className="space-y-3">
            <h2 className="text-xs font-bold text-primary uppercase tracking-widest">Section 02</h2>
            <h1 className="text-3xl font-serif font-bold text-text-dark">The Documentation Crisis in Rural Health Camps</h1>
            <div className="h-1 w-20 bg-accent rounded"></div>
          </div>

          <div className="grid md:grid-cols-[1fr_1fr] gap-10 items-start">
            <div className="space-y-6 text-sm text-slate-600 leading-relaxed font-light">
              <div className="p-4 rounded-md border border-alert-critical/20 bg-red-50/20 text-alert-critical font-semibold text-xs leading-relaxed">
                80+ patients. 1 clinician. Mixed-language consultations. Patchy internet. This is the operating environment SHRUTI was built for.
              </div>
              <p>
                Temporary health camps and small clinics are the primary care front door for millions of patients. A single physician can see <strong>80 to 100 patients in a session</strong>, often switching between Hindi, Hinglish, and English while still needing structured records for follow-up, referrals, and digital health systems.
              </p>
              <p>
                Existing EHR tools were not designed for this reality. They assume stable connectivity, English-heavy typing, and slow documentation time. SHRUTI attacks the wedge where the pain is sharpest: passive voice capture and doctor-reviewed note generation for clinics that cannot afford paperwork bottlenecks.
              </p>
              
              {/* Doctor Testimonial Card */}
              <div className="bg-white border border-slate-200/80 rounded-lg p-5 shadow-2xs space-y-3">
                <span className="text-[9px] font-bold text-accent-dark uppercase tracking-widest block">Practitioner Feedback from the Field</span>
                <p className="text-xs italic text-slate-600 leading-relaxed font-light">
                  "In our camps, patients walk for hours to see us. If documentation can happen in the background while I examine the patient, that changes the pace of the clinic."
                </p>
                <p className="text-[10px] font-bold text-text-dark uppercase tracking-wider text-right">
                  - Field feedback from clinic deployment
                </p>
              </div>
            </div>

            {/* Colloquial Dialect Processing Simulator (Interactive Terminal) */}
            <div className="space-y-4">
              <div className="bg-slate-900 rounded-lg p-5 font-mono text-[11px] text-slate-350 border border-slate-800 shadow-md">
                
                {/* Simulated Header */}
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3 select-none">
                  <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full bg-alert-critical"></div>
                    <div className="w-2.5 h-2.5 rounded-full bg-accent"></div>
                    <div className="w-2.5 h-2.5 rounded-full bg-primary"></div>
                    <span className="text-[9px] text-slate-500 ml-2">SHRUTI Dialect Ingestion Engine</span>
                  </div>
                  <span className="text-[8px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded font-bold uppercase tracking-wider animate-pulse">Live</span>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-slate-800/80 gap-1.5 pb-2 mb-3">
                  {(['hinglish', 'hindi', 'english'] as const).map((lang) => (
                    <button
                      key={lang}
                      onClick={() => setActiveTab(lang)}
                      className={`px-2.5 py-1 rounded text-[9px] font-bold uppercase tracking-wider transition-colors cursor-pointer ${
                        activeTab === lang
                          ? 'bg-primary text-white'
                          : 'bg-slate-800/40 text-slate-400 hover:bg-slate-800 hover:text-slate-300'
                      }`}
                    >
                      {lang}
                    </button>
                  ))}
                </div>

                {/* Tab Content */}
                <div className="space-y-4">
                  <div className="space-y-1">
                    <span className="text-emerald-400 font-bold block">Input Speech (Audio Ingestion):</span>
                    <p className="pl-3 leading-relaxed text-slate-200 italic">
                      "{DIALECT_SAMPLES[activeTab].speech}"
                    </p>
                  </div>
                  
                  <div className="space-y-1 border-t border-slate-800/60 pt-2.5">
                    <span className="text-accent font-bold block">Engine Translation (EMR English):</span>
                    <p className="pl-3 leading-relaxed text-slate-300">
                      {DIALECT_SAMPLES[activeTab].translation}
                    </p>
                  </div>

                  <div className="border-t border-slate-850 pt-2.5 text-[10px] text-slate-400 space-y-2">
                    <span className="font-bold text-slate-200 uppercase text-[9px] tracking-wider block">Structured Parsing Output:</span>
                    <div className="grid grid-cols-3 gap-2">
                      <div className="bg-slate-950 p-2 rounded border border-slate-800">
                        <span className="text-primary font-bold text-[8px] uppercase block mb-1">Symptoms</span>
                        <div className="space-y-0.5 text-slate-300 font-semibold">
                          {DIALECT_SAMPLES[activeTab].entities.symptoms.map(s => (
                            <div key={s}>• {s}</div>
                          ))}
                        </div>
                      </div>
                      <div className="bg-slate-950 p-2 rounded border border-slate-800">
                        <span className="text-accent font-bold text-[8px] uppercase block mb-1">Vitals/Info</span>
                        <div className="space-y-0.5 text-slate-300 font-semibold">
                          {DIALECT_SAMPLES[activeTab].entities.vitals.map(v => (
                            <div key={v}>• {v}</div>
                          ))}
                        </div>
                      </div>
                      <div className="bg-slate-950 p-2 rounded border border-slate-800">
                        <span className="text-alert-critical font-bold text-[8px] uppercase block mb-1">Negated</span>
                        <div className="space-y-0.5 text-slate-400 line-through">
                          {DIALECT_SAMPLES[activeTab].entities.negated.map(n => (
                            <div key={n}>• {n}</div>
                          ))}
                        </div>
                      </div>
                    </div>
                    
                    <p className="text-[9px] text-slate-450 leading-relaxed pt-1.5 border-t border-slate-850">
                      <strong className="text-white">State Resolution:</strong> {DIALECT_SAMPLES[activeTab].resolution}
                    </p>
                  </div>
                </div>

              </div>
              <p className="text-xs text-slate-500 italic text-center font-medium">
                Interact with the tabs above to see why ordinary English-first health software misses the real consultation.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 3: OUR SOLUTION */}
      <section id="solution" className="min-h-screen flex flex-col justify-between pt-20 bg-white">
        <div className="max-w-5xl mx-auto px-6 py-10 flex-grow space-y-12">
          <div className="space-y-3">
            <h2 className="text-xs font-bold text-primary uppercase tracking-widest">Section 03</h2>
            <h1 className="text-3xl font-serif font-bold text-text-dark">A Usable Product, Not a Slide Deck</h1>
            <div className="h-1 w-20 bg-accent rounded"></div>
          </div>

          {/* Pipeline Flowchart Grid */}
          <div className="space-y-6">
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest text-center">Secure Ingestion-to-FHIR Venture Workflow</h3>
            
            <div className="grid md:grid-cols-3 lg:grid-cols-4 gap-4">
              
              <div className="border border-slate-200/80 rounded p-4 bg-bg-warm/65 shadow-2xs hover:shadow-xs hover:border-primary/30 transition-all space-y-2">
                <div className="flex items-center gap-2.5">
                  <span className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center text-primary font-bold text-xs">1</span>
                  <h4 className="font-bold text-text-dark text-xs uppercase tracking-wider">Audio Ingestion</h4>
                </div>
                <p className="text-[11px] text-slate-500 leading-normal">
                  Captures consultations through a browser workflow clinicians can use during real outpatient interactions.
                </p>
              </div>

              <div className="border border-slate-200/80 rounded p-4 bg-bg-warm/65 shadow-2xs hover:shadow-xs hover:border-primary/30 transition-all space-y-2">
                <div className="flex items-center gap-2.5">
                  <span className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center text-primary font-bold text-xs">2</span>
                  <h4 className="font-bold text-text-dark text-xs uppercase tracking-wider">Dialect ASR</h4>
                </div>
                <p className="text-[11px] text-slate-500 leading-normal">
                  Routes speech through multilingual ASR with a fallback path for demos and low-connectivity evaluation.
                </p>
              </div>

              <div className="border border-slate-200/80 rounded p-4 bg-bg-warm/65 shadow-2xs hover:shadow-xs hover:border-primary/30 transition-all space-y-2">
                <div className="flex items-center gap-2.5">
                  <span className="w-6 h-6 bg-accent/20 rounded-full flex items-center justify-center text-accent-dark font-bold text-xs">3</span>
                  <h4 className="font-bold text-text-dark text-xs uppercase tracking-wider">Local De-Identification</h4>
                </div>
                <p className="text-[11px] text-slate-500 leading-normal">
                  Scrubs names, contact details, dates, and location markers locally before structured clinical review.
                </p>
              </div>

              <div className="border border-slate-200/80 rounded p-4 bg-bg-warm/65 shadow-2xs hover:shadow-xs hover:border-primary/30 transition-all space-y-2">
                <div className="flex items-center gap-2.5">
                  <span className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center text-primary font-bold text-xs">4</span>
                  <h4 className="font-bold text-text-dark text-xs uppercase tracking-wider">Clinical Extraction</h4>
                </div>
                <p className="text-[11px] text-slate-500 leading-normal">
                  Identifies symptoms, vitals, allergies, investigations, medications, and source evidence using local rules.
                </p>
              </div>

              <div className="border border-slate-200/80 rounded p-4 bg-bg-warm/65 shadow-2xs hover:shadow-xs hover:border-primary/30 transition-all space-y-2">
                <div className="flex items-center gap-2.5">
                  <span className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center text-primary font-bold text-xs">5</span>
                  <h4 className="font-bold text-text-dark text-xs uppercase tracking-wider">State Resolution</h4>
                </div>
                <p className="text-[11px] text-slate-500 leading-normal">
                  Keeps the latest explicit clinician instruction active while preserving source context for review.
                </p>
              </div>

              <div className="border border-slate-200/80 rounded p-4 bg-bg-warm/65 shadow-2xs hover:shadow-xs hover:border-primary/30 transition-all space-y-2">
                <div className="flex items-center gap-2.5">
                  <span className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center text-primary font-bold text-xs">6</span>
                  <h4 className="font-bold text-text-dark text-xs uppercase tracking-wider">SOAP Note Assembly</h4>
                </div>
                <p className="text-[11px] text-slate-500 leading-normal">
                  Compiles editable SOAP drafts for physician validation before any record is finalized.
                </p>
              </div>

              <div className="border border-slate-200/80 rounded p-4 bg-bg-warm/65 shadow-2xs hover:shadow-xs hover:border-primary/30 transition-all space-y-2">
                <div className="flex items-center gap-2.5">
                  <span className="w-6 h-6 bg-accent/20 rounded-full flex items-center justify-center text-accent-dark font-bold text-xs">7</span>
                  <h4 className="font-bold text-text-dark text-xs uppercase tracking-wider">CDS Safety Alerts</h4>
                </div>
                <p className="text-[11px] text-slate-500 leading-normal">
                  Flags missing medication details, drug-allergy risks, and outlier vitals for physician review.
                </p>
              </div>

              <div className="border border-slate-200/80 rounded p-4 bg-bg-warm/65 shadow-2xs hover:shadow-xs hover:border-primary/30 transition-all space-y-2">
                <div className="flex items-center gap-2.5">
                  <span className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center text-primary font-bold text-xs">8</span>
                  <h4 className="font-bold text-text-dark text-xs uppercase tracking-wider">HL7 FHIR Interop</h4>
                </div>
                <p className="text-[11px] text-slate-500 leading-normal">
                  Generates HL7 FHIR R4 JSON bundles for interoperability when clinics reconnect to larger systems.
                </p>
              </div>

            </div>
          </div>

          {/* App Mockup Screenshot */}
          <div className="pt-6 space-y-3">
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest text-center">The Clinician Console — In Action</h3>
            <div className="relative rounded-xl overflow-hidden shadow-2xl border border-slate-200 group cursor-pointer" onClick={() => navigate('/dashboard')}>
              <img
                src="/shruti_app_mockup.png"
                alt="SHRUTI clinician console showing SOAP note generation and drug interaction alerts"
                className="w-full object-cover transition-transform duration-700 group-hover:scale-[1.02]"
              />
              <div className="absolute inset-0 bg-primary/0 group-hover:bg-primary/10 transition-colors duration-300 flex items-center justify-center">
                <span className="opacity-0 group-hover:opacity-100 transition-opacity bg-white/90 text-primary font-bold text-sm px-5 py-2.5 rounded-full shadow-lg backdrop-blur-sm">
                  Launch Clinician Console →
                </span>
              </div>
            </div>
            <p className="text-[11px] text-slate-400 text-center italic">
              Real-time transcription, structured SOAP drafting, safety alerts, printable reports, and EMR-ready export in one clinician console.
            </p>
          </div>

          {/* 4 Feature Cards */}
          <div className="grid sm:grid-cols-2 gap-6 pt-6">
            <div className="bg-slate-50 border border-slate-200/80 rounded p-5 space-y-2 hover:shadow-2xs transition-shadow">
              <h3 className="font-bold text-text-dark font-serif text-sm">Deployment-First Build</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                The product is organized around clinic throughput: quick session creation, audio upload or dictation, transcript override, clinical processing, and note export.
              </p>
            </div>
            <div className="bg-slate-50 border border-slate-200/80 rounded p-5 space-y-2 hover:shadow-2xs transition-shadow">
              <h3 className="font-bold text-text-dark font-serif text-sm">Multilingual Accent Adaptation</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Maps colloquial Hinglish and regional symptom terms into standard clinical language while preserving the source transcript for auditability.
              </p>
            </div>
            <div className="bg-slate-50 border border-slate-200/80 rounded p-5 space-y-2 hover:shadow-2xs transition-shadow">
              <h3 className="font-bold text-text-dark font-serif text-sm">Clinician Safety Net (CDS)</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                An active rules engine flags drug-allergy interactions, elevated vital readings, and missing medication parameters before notes are signed.
              </p>
            </div>
            <div className="bg-slate-50 border border-slate-200/80 rounded p-5 space-y-2 hover:shadow-2xs transition-shadow">
              <h3 className="font-bold text-text-dark font-serif text-sm">National Health Registry Ready</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Outputs standard HL7 FHIR R4 JSON bundles so patient records can move from camp documentation into interoperable health infrastructure.
              </p>
            </div>
          </div>

          {/* Tech Framework List */}
          <div className="border-t border-slate-100 pt-6">
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Venture Technology Framework</h3>
            <div className="flex flex-wrap gap-2 text-[11px] font-mono font-semibold">
              <span className="bg-slate-100 border border-slate-200 px-2 py-0.5 rounded text-slate-700">FastAPI (Python Async)</span>
              <span className="bg-slate-100 border border-slate-200 px-2 py-0.5 rounded text-slate-700">React</span>
              <span className="bg-slate-100 border border-slate-200 px-2 py-0.5 rounded text-slate-700">TypeScript</span>
              <span className="bg-slate-100 border border-slate-200 px-2 py-0.5 rounded text-slate-700">Tailwind CSS</span>
              <span className="bg-slate-100 border border-slate-200 px-2 py-0.5 rounded text-slate-700">spaCy NLP (NER Models)</span>
              <span className="bg-slate-100 border border-slate-200 px-2 py-0.5 rounded text-slate-700">Human-in-the-loop review</span>
              <span className="bg-slate-100 border border-slate-200 px-2 py-0.5 rounded text-slate-700">Sarvam STT SDK</span>
              <span className="bg-slate-100 border border-slate-200 px-2 py-0.5 rounded text-slate-700">aiosqlite (Local Storage)</span>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 4: SAFETY & TECH (RESTRUCTURED) */}
      <section id="safety-tech" className="min-h-screen flex flex-col justify-between pt-20 bg-bg-warm">
        <div className="max-w-5xl mx-auto px-6 py-10 flex-grow space-y-12">
          <div className="space-y-3">
            <h2 className="text-xs font-bold text-primary uppercase tracking-widest">Section 04</h2>
            <h1 className="text-3xl font-serif font-bold text-text-dark">Responsible Clinical AI, Built for the Field</h1>
            <div className="h-1 w-20 bg-accent rounded"></div>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-white border border-slate-200 rounded p-5 space-y-2.5 shadow-2xs hover:shadow-xs transition-shadow">
              <span className="text-[10px] font-bold text-primary bg-primary/10 border border-primary/20 px-2 py-0.5 rounded uppercase tracking-wider">Dialect Integrity</span>
              <h3 className="font-bold text-text-dark font-serif text-sm">Low-Resource Language Adaptation</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Standard English-first systems fail when providers switch dialects mid-sentence. SHRUTI uses local entity mappings and source-linked transcript context to make mixed-language consultations reviewable.
              </p>
            </div>
            
            <div className="bg-white border border-slate-200 rounded p-5 space-y-2.5 shadow-2xs hover:shadow-xs transition-shadow">
              <span className="text-[10px] font-bold text-primary bg-primary/10 border border-primary/20 px-2 py-0.5 rounded uppercase tracking-wider">AI Safety Protocols</span>
              <h3 className="font-bold text-text-dark font-serif text-sm">Doctor-in-the-Loop by Design</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                SHRUTI does not autonomously diagnose or prescribe. It drafts documentation from captured facts, flags safety issues, and requires physician review before anything becomes a clinical record.
              </p>
            </div>

            <div className="bg-white border border-slate-200 rounded p-5 space-y-2.5 shadow-2xs hover:shadow-xs transition-shadow">
              <span className="text-[10px] font-bold text-accent-dark bg-accent/15 border border-accent/30 px-2 py-0.5 rounded uppercase tracking-wider">Offline Trust</span>
              <h3 className="font-bold text-text-dark font-serif text-sm">Local De-Identification</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Patient privacy is paramount. SHRUTI supports edge-first workflows and local de-identification so sensitive clinic data is handled conservatively in low-connectivity settings.
              </p>
            </div>
          </div>

          {/* Active Field Focus Areas */}
          <div className="border-t border-slate-250 pt-8 space-y-6 bg-white border border-slate-200 rounded p-6 shadow-sm">
            <h3 className="text-xs font-bold text-primary uppercase tracking-widest">Why This Can Become a Large Social Venture</h3>
            <ol className="list-decimal list-inside space-y-4 text-xs text-slate-700 font-medium leading-relaxed pl-2">
              <li>
                <span className="text-text-dark font-bold">A wedge into underserved healthcare:</span> Start with the painful documentation burden, then expand into longitudinal records, referrals, and population-health reporting.
              </li>
              <li>
                <span className="text-text-dark font-bold">A defensible field data advantage:</span> Real-world mixed-language clinical workflows create product insight that generic hospital software does not capture.
              </li>
              <li>
                <span className="text-text-dark font-bold">A responsible scale path:</span> The product grows through clinics, NGO camps, and public-health partners while keeping physicians as final authority.
              </li>
            </ol>
          </div>

          {/* Safety disclaimer card */}
          <div className="rounded border border-red-200 bg-red-50 p-4 text-xs space-y-1 shadow-2xs">
            <span className="font-bold text-alert-critical uppercase tracking-wider text-[10px] block">Public Health Safety & Registry Protocol</span>
            <p className="text-slate-700 leading-relaxed">
              This platform serves as an assistive documentation utility. It is not a certified medical device and does not substitute professional clinical evaluation. Attending physicians retain sole accountability for all patient notes, diagnostics, and prescriptions.
            </p>
          </div>
        </div>
      </section>

      {/* SECTION 5: SCALING IMPACT (GET INVOLVED) */}
      <section id="scale" className="min-h-screen flex flex-col justify-between pt-20 bg-white">
        <div className="max-w-5xl mx-auto px-6 py-10 flex-grow space-y-12">
          
          <div className="space-y-3">
            <h2 className="text-xs font-bold text-primary uppercase tracking-widest">Section 05</h2>
            <h1 className="text-3xl font-serif font-bold text-text-dark">From Clinic Deployment to National-Scale Impact</h1>
            <div className="h-1 w-20 bg-accent rounded"></div>
          </div>

          {/* Founder Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col sm:flex-row items-start sm:items-center gap-5 max-w-2xl">
            <div className="w-14 h-14 rounded-full bg-primary/10 border-2 border-primary/20 flex items-center justify-center flex-shrink-0">
              <span className="text-primary font-serif font-bold text-2xl">A</span>
            </div>
            <div className="space-y-1">
              <p className="text-xs font-bold text-primary uppercase tracking-widest">Founder & Lead Engineer</p>
              <h3 className="font-bold text-text-dark text-base font-serif">Arush Singhal</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Building SHRUTI as a venture-backed social impact platform for multilingual clinical documentation in underserved care settings.
              </p>
              <a
                href="mailto:arushsinghal98@gmail.com"
                className="text-xs font-semibold text-primary hover:underline transition-colors"
              >
                arushsinghal98@gmail.com
              </a>
            </div>
          </div>

          {/* Clinic Pilot Program Banner */}
          <div className="bg-primary/5 border border-primary/20 rounded-xl p-6 space-y-4 max-w-3xl">
            <div className="flex items-center gap-2">
              <span className="flex h-2.5 w-2.5 rounded-full bg-accent animate-pulse"></span>
              <span className="text-[10px] font-bold text-primary uppercase tracking-widest">Field Deployment Track — Clinics, Camps, NGO Partners</span>
            </div>
            <h3 className="font-bold text-text-dark font-serif text-lg">Scaling a Working Product Through Clinic Partnerships</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              SHRUTI is being shaped through active clinic workflows, partner feedback, and a clear venture model for social impact. The next phase is disciplined scale: more deployment sites, more regional language coverage, stronger safety evaluation, and measurable time returned to physicians.
            </p>
            <ul className="text-xs text-slate-600 space-y-1.5 pl-1">
              <li className="flex items-center gap-2"><span className="text-primary font-bold">✓</span> Clinic-ready workflow with live console and physician sign-off</li>
              <li className="flex items-center gap-2"><span className="text-primary font-bold">✓</span> Offline-first architecture for low-connectivity care sites</li>
              <li className="flex items-center gap-2"><span className="text-primary font-bold">✓</span> Hindi, Hinglish, and English documentation pathway</li>
              <li className="flex items-center gap-2"><span className="text-primary font-bold">✓</span> FHIR-ready export for future public-health integration</li>
              <li className="flex items-center gap-2"><span className="text-primary font-bold">✓</span> Open for clinic, NGO, and public-health partnerships</li>
            </ul>
            <a
              href="mailto:arushsinghal98@gmail.com?subject=SHRUTI Clinic Pilot Partnership"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary hover:bg-primary-dark text-white rounded font-bold text-xs transition-all shadow-md"
            >
              Start a Clinic Partnership
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
            </a>
          </div>

          {/* Description Block */}
          <div className="max-w-3xl space-y-4 text-sm text-slate-600 leading-relaxed font-light">
            <p>
              The goal is not just a better note-taking tool. SHRUTI is a wedge into clinical infrastructure for communities left behind by English-first, internet-dependent healthcare software. The venture begins with documentation, but the long-term opportunity is safer longitudinal records, referrals, follow-up, and public-health visibility for underserved clinics.
            </p>
          </div>

          {/* Get Involved Grid with interactive modal buttons */}
          <div className="grid md:grid-cols-3 gap-6 pt-6">
            
            <div className="bg-bg-warm border border-slate-200 p-5 rounded-lg flex flex-col justify-between hover:shadow-xs transition-shadow">
              <div className="space-y-3 mb-4">
                <span className="text-[9px] font-bold text-primary bg-primary/10 border border-primary/20 px-2 py-0.5 rounded uppercase tracking-wider">Health Camps & NGOs</span>
                <h4 className="font-bold text-text-dark text-sm font-serif">Deploy in Your Clinic</h4>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Implement SHRUTI in your rural consultations. Save hours of writing and instantly digitize records in regional dialects.
                </p>
              </div>
              <button 
                onClick={() => setShowDeploymentModal(true)}
                className="w-full text-center py-2 bg-primary hover:bg-primary-dark text-white rounded text-xs font-bold transition-colors cursor-pointer"
              >
                Request Deployment Kit
              </button>
            </div>

            <div className="bg-bg-warm border border-slate-200 p-5 rounded-lg flex flex-col justify-between hover:shadow-xs transition-shadow">
              <div className="space-y-3 mb-4">
                <span className="text-[9px] font-bold text-primary bg-primary/10 border border-primary/20 px-2 py-0.5 rounded uppercase tracking-wider">Clinics & Hospitals</span>
                <h4 className="font-bold text-text-dark text-sm font-serif">Book a Demo Call</h4>
                <p className="text-xs text-slate-500 leading-relaxed">
                  See SHRUTI live in a 20-minute walkthrough. We'll show you exactly how it works in a camp setting and answer all your questions.
                </p>
              </div>
              <a
                href="mailto:arushsinghal98@gmail.com?subject=SHRUTI Demo Request"
                className="w-full text-center py-2 bg-slate-800 hover:bg-slate-900 text-white rounded text-xs font-bold transition-colors block"
              >
                Schedule a Demo →
              </a>
            </div>

            <div className="bg-bg-warm border border-slate-200 p-5 rounded-lg flex flex-col justify-between hover:shadow-xs transition-shadow">
              <div className="space-y-3 mb-4">
                <span className="text-[9px] font-bold text-accent-dark bg-accent/15 border border-accent/30 px-2 py-0.5 rounded uppercase tracking-wider">Supporters</span>
                <h4 className="font-bold text-text-dark text-sm font-serif">Sponsor A Camp Kit</h4>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Support deployment hardware. A $250 kit equips a clinician with a tablet, solar charger, and offline-enabled storage.
                </p>
              </div>
              <button 
                onClick={() => setShowSponsorModal(true)}
                className="w-full text-center py-2 bg-accent hover:bg-accent-dark text-white rounded text-xs font-bold transition-colors cursor-pointer"
              >
                Sponsor a Camp Kit
              </button>
            </div>

          </div>
        </div>

        {/* Global Footer */}
        <footer className="w-full bg-slate-900 text-slate-450 py-12 px-6 border-t border-slate-800 text-xs mt-12">
          <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-start justify-between gap-8">
            <div className="space-y-3 max-w-sm">
              <div className="flex items-center gap-2 text-white font-bold text-sm">
                <span className="font-serif text-primary text-base">श</span> SHRUTI Initiative
              </div>
              <p className="text-[11px] leading-relaxed text-slate-400">
                Empowering healthcare providers and improving patient outcomes in rural communities through passive, dialect-inclusive clinical synthesis.
              </p>
              <a
                href="mailto:arushsinghal98@gmail.com"
                className="text-primary hover:text-white transition-colors font-semibold block text-[11px]"
              >
                arushsinghal98@gmail.com
              </a>
            </div>
            <div className="space-y-3 text-[11px] max-w-xs">
              <span className="text-slate-200 font-semibold block uppercase tracking-wider text-[10px]">Quick Links</span>
              <a href="#mission" onClick={(e) => handleNavClick(e, 'mission')} className="hover:text-white transition-colors block">Our Mission</a>
              <a href="#crisis" onClick={(e) => handleNavClick(e, 'crisis')} className="hover:text-white transition-colors block">The Crisis</a>
              <a href="#solution" onClick={(e) => handleNavClick(e, 'solution')} className="hover:text-white transition-colors block">Our Solution</a>
              <a href="#safety-tech" onClick={(e) => handleNavClick(e, 'safety-tech')} className="hover:text-white transition-colors block">Safety & Tech</a>
              <a href="#scale" onClick={(e) => handleNavClick(e, 'scale')} className="hover:text-white transition-colors block">Partner With Us</a>
            </div>
            <div className="space-y-3 text-[11px] max-w-xs">
              <span className="text-slate-200 font-semibold block uppercase tracking-wider text-[10px]">Contact & Partnership</span>
              <a href="mailto:arushsinghal98@gmail.com?subject=SHRUTI Clinic Pilot Partnership" className="hover:text-white transition-colors block">Apply for Clinic Pilot</a>
              <a href="mailto:arushsinghal98@gmail.com?subject=SHRUTI Demo Request" className="hover:text-white transition-colors block">Request a Demo</a>
              <a href="mailto:arushsinghal98@gmail.com?subject=SHRUTI Sponsorship" className="hover:text-white transition-colors block">Sponsor a Camp Kit</a>
              <p className="leading-relaxed text-slate-500 pt-2 border-t border-slate-800">
                Assistive documentation tool. All clinical decisions remain with the attending physician.
              </p>
            </div>
          </div>
          <div className="max-w-5xl mx-auto text-center border-t border-slate-800 mt-8 pt-6 text-[10px] text-slate-500">
            &copy; {new Date().getFullYear()} SHRUTI Initiative · Arush Singhal · arushsinghal98@gmail.com · Empowering rural health camps across India.
          </div>
        </footer>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* MODALS */}
      {/* ------------------------------------------------------------- */}
      
      {/* Deployment Modal */}
      {showDeploymentModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <div className="bg-white rounded-lg p-6 max-w-md w-full shadow-xl border border-slate-200 relative animate-fade-in">
            <button 
              onClick={closeDeploymentModal}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 cursor-pointer"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            
            {!deploymentSubmitted ? (
              <form onSubmit={handleDeploymentSubmit} className="space-y-4">
                <div className="border-b border-slate-100 pb-2">
                  <h3 className="text-base font-bold text-text-dark font-serif">Request Deployment Kit</h3>
                  <p className="text-[11px] text-slate-500 mt-0.5">Please provide your organization details to initialize field integration.</p>
                </div>
                
                <div className="space-y-1.5">
                  <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">Full Name</label>
                  <input 
                    type="text" 
                    required 
                    value={depName} 
                    onChange={e => setDepName(e.target.value)}
                    placeholder="Dr. Rajesh Kumar" 
                    className="w-full text-xs border border-slate-200 rounded p-2 focus:outline-none focus:border-primary"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">Email Address</label>
                  <input 
                    type="email" 
                    required 
                    value={depEmail} 
                    onChange={e => setDepEmail(e.target.value)}
                    placeholder="contact@ruralhealthngo.org" 
                    className="w-full text-xs border border-slate-200 rounded p-2 focus:outline-none focus:border-primary"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">NGO / Hospital Name</label>
                  <input 
                    type="text" 
                    required 
                    value={depOrg} 
                    onChange={e => setDepOrg(e.target.value)}
                    placeholder="Seva Rural Healthcare Trust" 
                    className="w-full text-xs border border-slate-200 rounded p-2 focus:outline-none focus:border-primary"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">Primary Target State</label>
                    <select 
                      value={depState} 
                      onChange={e => setDepState(e.target.value)}
                      className="w-full text-xs border border-slate-200 rounded p-2 focus:outline-none focus:border-primary bg-white"
                    >
                      <option>Uttar Pradesh</option>
                      <option>Bihar</option>
                      <option>Madhya Pradesh</option>
                      <option>Rajasthan</option>
                      <option>Other</option>
                    </select>
                  </div>
                  
                  <div className="space-y-1.5">
                    <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">Clinical Role</label>
                    <select 
                      value={depRole} 
                      onChange={e => setDepRole(e.target.value)}
                      className="w-full text-xs border border-slate-200 rounded p-2 focus:outline-none focus:border-primary bg-white"
                    >
                      <option>Clinician Provider</option>
                      <option>NGO Administrator</option>
                      <option>Public Health Officer</option>
                      <option>Technical Advisor</option>
                    </select>
                  </div>
                </div>

                <button 
                  type="submit" 
                  className="w-full py-2.5 bg-primary hover:bg-primary-dark text-white rounded text-xs font-bold transition-all shadow-sm cursor-pointer"
                >
                  Request Deployment Details
                </button>
              </form>
            ) : (
              <div className="py-6 text-center space-y-4">
                <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto text-primary">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div className="space-y-2">
                  <h3 className="font-bold text-text-dark font-serif text-sm">Deployment Ingestion Pending</h3>
                  <p className="text-xs text-slate-500 leading-relaxed px-4">
                    Thank you, <strong className="text-text-dark">{depName}</strong>! Our field coordination team will reach out to <strong className="text-text-dark">{depEmail}</strong> with node hardware setups and local SQLite integration schemas.
                  </p>
                </div>
                <button 
                  onClick={closeDeploymentModal}
                  className="px-4 py-2 border border-slate-200 rounded text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors cursor-pointer"
                >
                  Close Window
                </button>
              </div>
            )}

          </div>
        </div>
      )}

      {/* Sponsor Modal */}
      {showSponsorModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <div className="bg-white rounded-lg p-6 max-w-md w-full shadow-xl border border-slate-200 relative animate-fade-in">
            <button 
              onClick={closeSponsorModal}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 cursor-pointer"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            {!sponsorSubmitted ? (
              <form onSubmit={handleSponsorSubmit} className="space-y-4">
                <div className="border-b border-slate-100 pb-2">
                  <h3 className="text-base font-bold text-text-dark font-serif">Sponsor Camp Hardware Kits</h3>
                  <p className="text-[11px] text-slate-500 mt-0.5">Help supply offline digital records packages to remote medical camp providers.</p>
                </div>

                <div className="p-3 bg-bg-warm border border-slate-200 rounded text-[11px] text-slate-650 leading-relaxed space-y-1.5">
                  <span className="font-bold text-primary block uppercase tracking-wider text-[9px]">Included Camp Hardware Node Package:</span>
                  <p>• <strong>1x Edge Tablet (10")</strong> with pre-loaded offline transcription framework & local SQLite DB.</p>
                  <p>• <strong>1x High-Gain Condenser Mic</strong> for accurate speech acquisition in noisy setups.</p>
                  <p>• <strong>1x Solar Power Bank (20,000mAh)</strong> to ensure constant operation during camp load-shedding.</p>
                  <span className="font-bold text-text-dark block pt-1 border-t border-slate-200/60">Estimated Unit Cost: $250 / camp package</span>
                </div>

                <div className="space-y-1.5">
                  <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">Sponsor Name</label>
                  <input 
                    type="text" 
                    required 
                    value={sponName} 
                    onChange={e => sponName.length < 50 && setSponName(e.target.value)}
                    placeholder="Anita Sengupta" 
                    className="w-full text-xs border border-slate-200 rounded p-2 focus:outline-none focus:border-primary"
                  />
                </div>

                <div className="grid grid-cols-3 gap-3 items-end">
                  <div className="col-span-2 space-y-1.5">
                    <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">Email Address</label>
                    <input 
                      type="email" 
                      required 
                      value={sponEmail} 
                      onChange={e => setSponEmail(e.target.value)}
                      placeholder="sponsor@impactventures.com" 
                      className="w-full text-xs border border-slate-200 rounded p-2 focus:outline-none focus:border-primary"
                    />
                  </div>
                  
                  <div className="space-y-1.5">
                    <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">Quantity</label>
                    <input 
                      type="number" 
                      required 
                      min={1} 
                      max={100}
                      value={sponQuantity} 
                      onChange={e => setSponQuantity(parseInt(e.target.value) || 1)}
                      className="w-full text-xs border border-slate-200 rounded p-2 focus:outline-none focus:border-primary bg-white"
                    />
                  </div>
                </div>

                <div className="flex justify-between items-center bg-slate-50 p-2.5 rounded border border-slate-100 text-xs">
                  <span className="font-semibold text-slate-500">Total Sponsorship Pledge:</span>
                  <span className="font-extrabold text-primary font-mono">${sponQuantity * 250}</span>
                </div>

                <button 
                  type="submit" 
                  className="w-full py-2.5 bg-accent hover:bg-accent-dark text-white rounded text-xs font-bold transition-all shadow-sm cursor-pointer"
                >
                  Pledge Support
                </button>
              </form>
            ) : (
              <div className="py-6 text-center space-y-4">
                <div className="w-12 h-12 bg-accent/15 rounded-full flex items-center justify-center mx-auto text-accent-dark">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                  </svg>
                </div>
                <div className="space-y-2">
                  <h3 className="font-bold text-text-dark font-serif text-sm">Thank You for Your Support!</h3>
                  <p className="text-xs text-slate-500 leading-relaxed px-4">
                    Dear <strong className="text-text-dark">{sponName}</strong>, thank you for pledging to sponsor <strong className="text-text-dark">{sponQuantity}</strong> camp kit(s) (${sponQuantity * 250} total support). We have sent validation steps to <strong className="text-text-dark">{sponEmail}</strong>.
                  </p>
                </div>
                <button 
                  onClick={closeSponsorModal}
                  className="px-4 py-2 border border-slate-200 rounded text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors cursor-pointer"
                >
                  Close Window
                </button>
              </div>
            )}

          </div>
        </div>
      )}

    </div>
  );
}
