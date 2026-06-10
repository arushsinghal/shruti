import { useNavigate } from 'react-router-dom';

export default function About() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-bg-warm font-sans text-text-dark pb-20">
      {/* Navigation */}
      <nav className="w-full px-6 py-4 border-b border-slate-200/80 flex items-center justify-between bg-white/80 backdrop-blur-md sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary rounded flex items-center justify-center shadow-sm">
            <span className="text-white font-serif font-bold text-lg">श</span>
          </div>
          <div className="flex flex-col">
            <span className="text-base font-bold text-text-dark tracking-tight leading-none mb-1">SHRUTI Health</span>
            <span className="text-[10px] text-slate-500 font-medium">Clinic-deployed documentation infrastructure</span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-xs font-semibold bg-primary hover:bg-primary-dark text-white px-3.5 py-1.5 rounded transition-all shadow-sm cursor-pointer"
          >
            Launch Console
          </button>
        </div>
      </nav>

      <main className="max-w-3xl mx-auto px-6 pt-12 space-y-12">
        {/* Back Button */}
        <button
          onClick={() => navigate(-1)}
          className="text-xs font-bold text-slate-500 hover:text-primary transition-colors flex items-center gap-1 cursor-pointer"
        >
          <svg className="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back
        </button>

        {/* Project About Section */}
        <section className="space-y-4">
          <h1 className="text-3xl font-serif font-bold text-text-dark">About the SHRUTI Venture</h1>
          <div className="h-1 w-20 bg-accent rounded"></div>

          {/* Contextual Camp Photo */}
          <div className="relative rounded-xl overflow-hidden shadow-lg border border-slate-200 my-6">
            <img
              src="/rural_doctor_hero.png"
              alt="Indian physician examining a patient at a rural health camp"
              className="w-full object-cover"
              style={{ maxHeight: '300px' }}
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent" />
            <div className="absolute bottom-0 left-0 right-0 p-3">
              <p className="text-white text-[11px] font-medium drop-shadow-sm">
                Rural health camps and small clinics — where SHRUTI is built to make clinical documentation usable.
              </p>
            </div>
          </div>

          <p className="text-slate-600 leading-relaxed font-light mt-4">
            SHRUTI is a field-deployed social venture addressing the documentation burden in rural, low-resource clinics across India. In high-throughput settings where one physician may consult dozens of patients in a session, the platform turns Hindi, English, and Hinglish conversations into structured, doctor-reviewed SOAP documentation.
          </p>
          <p className="text-slate-600 leading-relaxed font-light">
            The product combines a clinician console, audio ingestion, local clinical extraction, safety alerts, editable SOAP notes, printable reports, and HL7 FHIR export. It is built around a non-negotiable human-in-the-loop workflow: SHRUTI assists documentation, but the physician remains the final clinical authority.
          </p>
          <div className="rounded-lg border border-accent/30 bg-accent/10 p-4 text-xs text-slate-700 leading-relaxed">
            <p className="font-bold uppercase tracking-wider text-accent-dark mb-1">Deployment & Partnerships</p>
            <p>
              SHRUTI is deployed in clinical workflows and available for clinic, NGO, and public-health partnerships. Public pages keep partner identities private unless a partner chooses to be named.
            </p>
          </div>
        </section>

        {/* Why This Exists */}
        <section className="space-y-4 border-t border-slate-200 pt-8">
          <h2 className="text-xl font-serif font-bold text-text-dark">Why This Exists: The Rural Healthcare Crisis</h2>
          <p className="text-slate-600 leading-relaxed font-light">
            In rural India, the healthcare ecosystem operates under severe resource constraints, with a doctor-to-patient ratio standing at an alarming <strong>1 to 1,457</strong>. Under such demanding conditions, overloaded clinical practitioners at temporary health camps routinely consult with 80 to 100 patients daily.
          </p>
          <p className="text-slate-600 leading-relaxed font-light">
            Studies show that clinicians spend <strong>30% to 40% of their total consultation time</strong> manually typing or writing clinical notes. SHRUTI starts with this urgent wedge: returning clinician attention to patients while creating structured records that can later support follow-up, referrals, and public-health visibility.
          </p>
        </section>

        {/* Our Approach to Deployment Safety & Challenges */}
        <section className="space-y-4 border-t border-slate-200 pt-8">
          <h2 className="text-xl font-serif font-bold text-text-dark">Our Approach to Safety, Scale & Field Challenges</h2>
          <p className="text-slate-600 leading-relaxed font-light">
            Deploying AI systems in remote healthcare environments involves addressing several unique challenges. Our technical team works continuously on these core engineering pillars:
          </p>
          <ul className="list-disc list-inside space-y-2.5 text-sm text-slate-600 pl-2">
            <li>
              <strong className="text-text-dark">Linguistic Diversity & Hinglish Support:</strong> Standard NLP tools struggle when clinicians code-switch mid-sentence. SHRUTI uses local entity mapping and transcript evidence to keep Hindi, English, and Hinglish documentation reviewable.
            </li>
            <li>
              <strong className="text-text-dark">Clinical Safety & Physician Control:</strong> The system is doctor-assistive, not autonomous. It flags risks and drafts notes, but every output requires physician review before use.
            </li>
            <li>
              <strong className="text-text-dark">Scalable Social Venture Path:</strong> SHRUTI is designed to grow through clinics, NGO health camps, and public-health partners while keeping privacy and field usability at the center.
            </li>
          </ul>
        </section>

        {/* Clinical Safety Disclaimer Banner */}
        <div className="rounded bg-accent/10 border border-accent/30 text-slate-800 p-4 text-xs space-y-1 shadow-sm">
          <p className="font-bold uppercase tracking-wider text-accent-dark">Clinical Safety & Interoperability Protocol</p>
          <p className="leading-relaxed text-slate-700">
            SHRUTI is an assistive documentation platform. It is not a certified medical device and does not replace professional clinical evaluation. All diagnostics, prescriptions, and notes remain under the sole signature and authority of the attending licensed provider. Standardized outputs align with HL7 FHIR standards for public health registry synchronization.
          </p>
        </div>
      </main>
    </div>
  );
}
