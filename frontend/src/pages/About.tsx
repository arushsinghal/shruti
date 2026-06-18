import { useNavigate } from 'react-router-dom';

export default function About() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#05070b] font-sans text-slate-100 pb-20">
      <nav className="w-full px-6 py-4 border-b border-white/10 flex items-center justify-between bg-[#05070b]/88 backdrop-blur-xl sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary rounded-md flex items-center justify-center shadow-[0_0_24px_rgba(27,94,59,0.45)]">
            <span className="text-white font-bold text-lg">श</span>
          </div>
          <div className="flex flex-col">
            <span className="text-base font-bold text-white tracking-tight leading-none mb-1">Lipi Health</span>
            <span className="text-[10px] text-slate-400 font-medium">Clinical AI infrastructure company</span>
          </div>
        </div>
        <button
          onClick={() => navigate('/dashboard')}
          className="text-xs font-semibold bg-white hover:bg-slate-200 text-slate-950 px-3.5 py-1.5 rounded-md transition-all cursor-pointer"
        >
          Launch Console
        </button>
      </nav>

      <main className="max-w-4xl mx-auto px-6 pt-12 space-y-12">
        <button
          onClick={() => navigate(-1)}
          className="text-xs font-bold text-slate-500 hover:text-white transition-colors flex items-center gap-1 cursor-pointer"
        >
          <svg className="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back
        </button>

        <section className="space-y-6">
          <div className="space-y-3">
            <p className="text-xs font-bold text-accent uppercase tracking-widest">Company</p>
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-white leading-[0.95]">
              About Lipi Health
            </h1>
          </div>

          <div className="relative rounded-xl overflow-hidden shadow-2xl border border-white/10 bg-white/[0.04]">
            <img
              src="/lipi_app_mockup.png"
              alt="Lipi clinician console showing SOAP documentation workflow"
              className="w-full object-cover object-left-top"
              style={{ maxHeight: '360px' }}
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />
            <div className="absolute bottom-0 left-0 right-0 p-4">
              <p className="text-white text-[11px] font-bold uppercase tracking-wider drop-shadow-sm">
                Voice2SOAP is live. The broader clinical AI platform is in build.
              </p>
            </div>
          </div>

          <p className="text-slate-300 leading-relaxed">
            Lipi Health is building clinical AI infrastructure for India. Voice2SOAP is the first live product: multilingual consultations become physician-reviewed SOAP records, CDS alerts, printable reports, and FHIR exports.
          </p>
          <p className="text-slate-400 leading-relaxed">
            The bigger company is not a documentation wrapper. Lipi is building toward private clinical speech models, domain-specific documentation LLMs, local safety engines, and operating intelligence for clinics, hospitals, and provider networks.
          </p>
          <div className="rounded-lg border border-primary/30 bg-primary/10 p-4 text-xs text-slate-300 leading-relaxed">
            <p className="font-bold uppercase tracking-wider text-emerald-300 mb-1">Current access</p>
            <p>
              Lipi is available for clinical teams and platform partners evaluating Voice2SOAP today and the broader clinical AI stack as it develops.
            </p>
          </div>
        </section>

        <section className="space-y-4 border-t border-white/10 pt-8">
          <h2 className="text-2xl font-bold tracking-tight text-white">Why documentation is the wedge</h2>
          <p className="text-slate-400 leading-relaxed">
            Documentation is the highest-frequency workflow in outpatient care. Every consultation creates clinical notes, medication decisions, follow-up instructions, and interoperability needs. Owning this workflow creates the record layer that makes later products possible.
          </p>
          <p className="text-slate-400 leading-relaxed">
            The expansion path is clinical memory, referrals, coding, population analytics, and private model infrastructure for provider networks. Voice2SOAP earns the workflow; the platform compounds around it.
          </p>
        </section>

        <section className="space-y-4 border-t border-white/10 pt-8">
          <h2 className="text-2xl font-bold tracking-tight text-white">Operating principles</h2>
          <ul className="grid md:grid-cols-3 gap-4 text-sm">
            <li className="rounded-lg border border-white/10 bg-white/[0.035] p-4">
              <strong className="text-white block mb-2">Workflow first</strong>
              <span className="text-slate-400">Products must fit real clinical throughput before they can become intelligent systems.</span>
            </li>
            <li className="rounded-lg border border-white/10 bg-white/[0.035] p-4">
              <strong className="text-white block mb-2">Local by default</strong>
              <span className="text-slate-400">Clinical extraction, memory resolution, and conflict detection run locally before optional formatting.</span>
            </li>
            <li className="rounded-lg border border-white/10 bg-white/[0.035] p-4">
              <strong className="text-white block mb-2">Models with accountability</strong>
              <span className="text-slate-400">Lipi's model roadmap keeps physicians in control and links every clinical fact back to source evidence.</span>
            </li>
          </ul>
        </section>

        <div className="rounded-md bg-red-950/25 border border-red-400/25 text-slate-300 p-4 text-xs space-y-1">
          <p className="font-bold uppercase tracking-wider text-red-300">Clinical Safety Notice</p>
          <p className="leading-relaxed">
            Lipi is an assistive clinical AI platform. It is not a certified medical device and does not replace professional clinical evaluation. All diagnostics, prescriptions, and notes remain under the sole signature and authority of the attending licensed provider.
          </p>
        </div>
      </main>
    </div>
  );
}
