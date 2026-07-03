import type { ProcessClinicalResponse } from '../types/clinical';

interface Props {
  results: ProcessClinicalResponse;
  patientName?: string;
}

export default function AudioRecap({ results, patientName }: Props) {
  const { facts, soap } = results;

  // Build 5 bullet points from existing extracted data — no LLM
  const bullets: { label: string; value: string; color: string }[] = [];

  // 1. Chief complaint / symptoms
  const symptoms = facts?.symptoms ?? [];
  if (symptoms.length > 0) {
    bullets.push({
      label: 'Presenting With',
      value: symptoms.slice(0, 3).join(', ') + (symptoms.length > 3 ? ` +${symptoms.length - 3} more` : ''),
      color: 'text-blue-700 bg-blue-50 border-blue-200',
    });
  }

  // 2. Vitals
  const vitals = facts?.vitals ?? [];
  if (vitals.length > 0) {
    bullets.push({
      label: 'Vitals',
      value: vitals.slice(0, 3).join(' · '),
      color: 'text-slate-700 bg-slate-50 border-slate-200',
    });
  }

  // 3. Diagnosis — pull from Assessment section
  const diagnosisMatch = soap?.A?.match(/(?:diagnosis|assessment|impression)[:\s]+([^.;\n]+)/i);
  const diagnosis = diagnosisMatch?.[1]?.trim() || soap?.A?.split('.')[0]?.trim();
  if (diagnosis && diagnosis.length < 120) {
    bullets.push({
      label: 'Assessment',
      value: diagnosis,
      color: 'text-purple-700 bg-purple-50 border-purple-200',
    });
  }

  // 4. Medications
  const meds = facts?.medications ?? [];
  if (meds.length > 0) {
    bullets.push({
      label: 'Medications',
      value: meds.slice(0, 3).map(m => `${m.name}${m.dosage ? ' ' + m.dosage : ''}`).join(', ') + (meds.length > 3 ? ` +${meds.length - 3}` : ''),
      color: 'text-emerald-700 bg-emerald-50 border-emerald-200',
    });
  }

  // 5. Investigations / follow-up
  const investigations = facts?.investigations ?? [];
  const followUp = (facts as any)?.follow_up ?? [];
  if (investigations.length > 0) {
    bullets.push({
      label: 'Investigations',
      value: investigations.slice(0, 3).join(', '),
      color: 'text-amber-700 bg-amber-50 border-amber-200',
    });
  } else if (followUp.length > 0) {
    bullets.push({
      label: 'Follow Up',
      value: Array.isArray(followUp) ? followUp.join(', ') : followUp,
      color: 'text-amber-700 bg-amber-50 border-amber-200',
    });
  }

  if (bullets.length === 0) return null;

  return (
    <section className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-7 h-7 rounded-md bg-primary/10 flex items-center justify-center shrink-0">
          <svg className="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        </div>
        <div>
          <h2 className="text-sm font-bold text-text-dark">Consultation Recap</h2>
          <p className="text-[11px] text-slate-400">
            {patientName ? `${patientName} · ` : ''}Key points from this session
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {bullets.map((b, i) => (
          <div key={i} className={`flex items-start gap-2.5 rounded-lg border px-3 py-2.5 ${b.color}${i === bullets.length - 1 && bullets.length % 2 !== 0 ? ' sm:col-span-2' : ''}`}>
            <span className="text-[10px] font-bold uppercase tracking-wider opacity-70 mt-0.5 shrink-0 w-20">{b.label}</span>
            <span className="text-xs font-semibold leading-snug">{b.value}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
