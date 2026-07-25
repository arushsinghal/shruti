import { useNavigate } from 'react-router-dom';
import { CheckCircle2, Circle, ArrowLeft } from 'lucide-react';

interface ReadinessItem {
  label: string;
  detail: string;
  done: boolean;
}

const ITEMS: ReadinessItem[] = [
  {
    label: 'Consent capture on every session',
    detail: 'Verbal consent recorded and timestamped before any recording or transcription begins.',
    done: true,
  },
  {
    label: 'Immutable audit logging',
    detail: 'Every access to a clinical record is logged with who, what, and when — visible on the Audit Logs page.',
    done: true,
  },
  {
    label: 'Time-bound, signed patient links',
    detail: 'Prescription and record links use short-lived signed tokens, not bare phone numbers or session ids.',
    done: true,
  },
  {
    label: 'HL7 FHIR R4 export',
    detail: 'Every confirmed consultation exports as a standard FHIR Bundle (Patient, Condition, Medication, AllergyIntolerance).',
    done: true,
  },
  {
    label: 'ICD-10 coded diagnoses',
    detail: 'Diagnoses are mapped to ICD-10 codes automatically for insurance and interoperability use.',
    done: true,
  },
  {
    label: 'ABHA number capture',
    detail: "A patient's existing Ayushman Bharat Health Account id can be recorded at intake or session start.",
    done: true,
  },
  {
    label: 'NHCX-shaped claim export',
    detail: 'TPA claims export as an HL7 FHIR Claim resource, ready for pre-authorization submission.',
    done: true,
  },
  {
    label: 'NHCX Health Information Provider registration',
    detail: 'Sandbox registration with the National Health Authority, required before live claims submission.',
    done: false,
  },
  {
    label: 'ABDM Health Information Provider registration',
    detail: 'Required before pushing signed records into a patient’s Aarogya Setu / ABHA vault via HIE-CM consent flow.',
    done: false,
  },
];

export default function AbdmReadiness() {
  const navigate = useNavigate();
  const doneCount = ITEMS.filter((i) => i.done).length;

  return (
    <div className="min-h-screen bg-bg-warm font-sans text-text-dark antialiased">
      <div className="max-w-2xl mx-auto px-5 py-10">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-1.5 text-[13px] font-semibold text-slate-500 hover:text-primary transition-colors cursor-pointer mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>

        <div className="flex items-center gap-2.5 mb-2">
          <span className="grid place-items-center w-9 h-9 rounded-xl bg-primary text-white font-bold text-base shadow-sm">श</span>
          <span className="text-[18px] font-bold tracking-tight text-text-dark">Lipi</span>
        </div>

        <h1 className="text-[1.6rem] font-bold tracking-tight leading-snug mt-4">ABDM readiness</h1>
        <p className="mt-2 text-[14px] leading-relaxed text-slate-500 max-w-[52ch]">
          Where Lipi stands against India's Ayushman Bharat Digital Mission standards, built in code today versus pending external registration with the National Health Authority.
        </p>

        <div className="mt-6 rounded-2xl bg-white border border-slate-200/80 overflow-hidden">
          <div className="px-5 py-3.5 bg-primary/5 border-b border-slate-200/80 flex items-center justify-between">
            <span className="text-[12px] font-semibold text-slate-600">{doneCount} of {ITEMS.length} complete</span>
            <span className="text-[12px] font-semibold text-primary">{Math.round((doneCount / ITEMS.length) * 100)}%</span>
          </div>
          <div className="divide-y divide-slate-100">
            {ITEMS.map((item) => (
              <div key={item.label} className="flex gap-3 px-5 py-4">
                {item.done ? (
                  <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                ) : (
                  <Circle className="w-5 h-5 text-slate-300 shrink-0 mt-0.5" />
                )}
                <div>
                  <p className={`text-[14px] font-semibold ${item.done ? 'text-text-dark' : 'text-slate-500'}`}>{item.label}</p>
                  <p className="text-[12.5px] text-slate-500 mt-0.5 leading-relaxed">{item.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <p className="mt-5 text-[12px] text-slate-400 leading-relaxed">
          The last two items require external approval from the National Health Authority and are not gated on engineering effort alone.
        </p>
      </div>
    </div>
  );
}
