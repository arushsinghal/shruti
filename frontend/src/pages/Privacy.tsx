import { useNavigate } from 'react-router-dom';

const EFFECTIVE_DATE = 'June 2026';
const CONTACT_EMAIL = 'privacy@shruti.health';

export default function Privacy() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-bg-warm font-sans">
      <header className="border-b border-slate-200/80 bg-white/90 backdrop-blur-md shadow-sm">
        <div className="max-w-3xl mx-auto px-6 h-14 flex items-center justify-between">
          <button
            onClick={() => navigate(-1)}
            className="text-slate-400 hover:text-primary transition-colors flex items-center text-xs font-semibold"
          >
            <svg className="w-4 h-4 mr-1 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back
          </button>
          <div className="flex items-center gap-2">
            <span className="font-bold text-primary text-base">श</span>
            <span className="text-sm font-bold text-text-dark">Lipi</span>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-12 space-y-10 text-text-dark">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Privacy Policy</h1>
          <p className="text-xs text-slate-400 mt-1">Effective: {EFFECTIVE_DATE}</p>
        </div>

        <section className="border border-emerald-200 rounded-lg bg-emerald-50 p-5 space-y-2">
          <h2 className="text-sm font-bold text-emerald-800">The short version</h2>
          <ul className="text-sm text-emerald-700 space-y-1 list-disc list-inside">
            <li>Audio is sent to a third-party India-based speech-to-text provider for transcription only.</li>
            <li>Transcript identifiers (names, dates, locations) are scrubbed before storage.</li>
            <li>Raw audio is deleted after successful transcription. Incomplete or failed sessions may be retained up to 48 hours.</li>
            <li>A doctor reviews every AI-generated note before it is used clinically.</li>
            <li>Your data is never sold or shared with advertisers.</li>
          </ul>
        </section>

        <Section title="1. Who we are">
          <p>
            Lipi is an OPD administration service developed for doctors practicing in India. It
            transcribes multilingual (Hindi / Hinglish / English) patient consultations and generates
            doctor-reviewed SOAP notes, prescriptions, investigation orders, and follow-up messages.
          </p>
          <p className="mt-2">
            Lipi is a research prototype and is <strong>not a certified medical device</strong>.
            All AI outputs must be reviewed and confirmed by a licensed clinician before clinical use.
          </p>
        </Section>

        <Section title="2. What data we collect">
          <dl className="space-y-3 text-sm">
            <DataRow term="Audio recordings">
              Captured during a consultation session when the doctor (and patient) provides consent.
              Audio is transmitted to a third-party India-based speech-to-text provider's servers for transcription and
              is <strong>deleted from our systems after successful transcription</strong>. Files from
              incomplete or failed sessions may be retained for up to 48 hours.
            </DataRow>
            <DataRow term="Transcripts">
              The text returned by the speech-to-text service. Before storage, a local PHI scrubber
              removes personal identifiers including names, absolute dates, locations, and phone numbers.
              Relative clinical descriptions ("fever for 3 days", "since this morning") are preserved
              because they are medically necessary. Manual text transcript input follows the same
              consent, storage, and PHI scrubbing rules.
            </DataRow>
            <DataRow term="SOAP notes and clinical facts">
              AI-generated structured documentation derived from the scrubbed transcript. These are
              stored associated with the session and are accessible only to the treating doctor.
            </DataRow>
            <DataRow term="Session metadata">
              Session creation time, doctor name (as entered), patient name (as entered), and
              processing status. This metadata is not shared externally.
            </DataRow>
          </dl>
        </Section>

        <Section title="3. Third-party services">
          <p className="text-sm">
            <strong>India-based speech recognition provider</strong> — We use a third-party multilingual ASR
            (automatic speech recognition) API, operated from servers located in India, to convert audio to text.
            Audio is sent only after the doctor confirms patient consent. The provider's
            processing is subject to its own data processing agreement; raw audio is not retained
            beyond the duration of the API call as per its terms of service.
          </p>
          <p className="text-sm mt-2">
            No other third-party AI services receive patient audio or transcript data.
          </p>
        </Section>

        <Section title="4. How we use your data">
          <ul className="text-sm list-disc list-inside space-y-1">
            <li>To generate, display, and store SOAP notes for the treating doctor.</li>
            <li>
              To improve Lipi's accuracy and clinical coverage — only using anonymised, scrubbed
              transcripts and only with appropriate data-processing safeguards in place.
            </li>
            <li>To diagnose software issues and monitor system health (server logs; no patient data).</li>
          </ul>
        </Section>

        <Section title="5. Patient consent">
          <p className="text-sm">
            Lipi requires the treating doctor to explicitly confirm that the patient has been informed
            about audio recording and has provided verbal consent before any audio recording or
            upload is permitted. The consent confirmation is logged with a timestamp. Doctors are
            responsible for obtaining and documenting consent in accordance with applicable law and
            their institution's policy.
          </p>
        </Section>

        <Section title="6. Data retention">
          <dl className="space-y-3 text-sm">
            <DataRow term="Raw audio">Deleted after successful transcription; incomplete or failed sessions may be retained up to 48 hours.</DataRow>
            <DataRow term="Scrubbed transcripts and SOAP notes">Retained for the duration of the session and deleted on doctor request.</DataRow>
            <DataRow term="Session metadata">Retained for 90 days after last access unless the doctor requests earlier deletion.</DataRow>
          </dl>
        </Section>

        <Section title="7. Security">
          <p className="text-sm">
            All data is transmitted over HTTPS/TLS. PHI scrubbing runs locally on our servers before
            any data is written to the database. The application does not use browser local storage for
            patient data. CORS is restricted to configured origins only.
          </p>
        </Section>

        <Section title="8. Your rights">
          <p className="text-sm">
            Doctors may request deletion of any session and its associated data at any time by
            contacting us at{' '}
            <a href={`mailto:${CONTACT_EMAIL}`} className="text-primary underline">
              {CONTACT_EMAIL}
            </a>
            . Requests are fulfilled within 30 days.
          </p>
        </Section>

        <Section title="9. Changes to this policy">
          <p className="text-sm">
            We will update this page when our data practices change and notify active users by email.
            The effective date at the top of this page always reflects the latest revision.
          </p>
        </Section>

        <Section title="10. Contact">
          <p className="text-sm">
            Questions, concerns, or deletion requests:{' '}
            <a href={`mailto:${CONTACT_EMAIL}`} className="text-primary underline">
              {CONTACT_EMAIL}
            </a>
          </p>
        </Section>
      </main>

      <footer className="border-t border-slate-200 mt-16 py-6">
        <p className="text-center text-xs text-slate-400">
          © {new Date().getFullYear()} Lipi · Research prototype · Not a certified medical device
        </p>
      </footer>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="text-base font-bold text-slate-800 border-b border-slate-200 pb-1">{title}</h2>
      <div className="text-slate-600 leading-relaxed">{children}</div>
    </section>
  );
}

function DataRow({ term, children }: { term: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[160px_1fr] gap-3">
      <dt className="font-semibold text-slate-700 pt-0.5">{term}</dt>
      <dd className="text-slate-600">{children}</dd>
    </div>
  );
}
