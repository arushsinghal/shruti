import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../lib/api';

interface AppointmentInfo {
  appointment_id: string;
  patient_name: string | null;
  slot_datetime: string;
  status: string;
  already_submitted: boolean;
}

function formatSlot(iso: string): string {
  try {
    return new Date(iso).toLocaleString('en-IN', { weekday: 'long', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
  } catch {
    return iso;
  }
}

export default function PreVisitForm() {
  const { appointmentId } = useParams<{ appointmentId: string }>();
  const [info, setInfo] = useState<AppointmentInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const [chiefComplaint, setChiefComplaint] = useState('');
  const [currentMedications, setCurrentMedications] = useState('');
  const [allergies, setAllergies] = useState('');
  const [additionalNotes, setAdditionalNotes] = useState('');

  useEffect(() => {
    if (!appointmentId) return;
    api.get(`/public/appointments/${appointmentId}`)
      .then(r => setInfo(r.data))
      .catch(() => setError('This link is invalid or has expired.'))
      .finally(() => setLoading(false));
  }, [appointmentId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      await api.post(`/public/appointments/${appointmentId}/pre-visit-form`, {
        chief_complaint: chiefComplaint,
        current_medications: currentMedications,
        allergies,
        additional_notes: additionalNotes,
      });
      setSubmitted(true);
    } catch {
      setError('Could not submit right now. Please try again in a moment.');
    } finally {
      setSubmitting(false);
    }
  }

  const inputCls = 'w-full px-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-[14px] text-text-dark placeholder-slate-400 focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/15 transition-all resize-none';

  if (loading) {
    return (
      <div className="min-h-[100dvh] bg-bg-warm flex items-center justify-center px-6">
        <div className="w-full max-w-md space-y-3">
          <div className="h-6 w-40 bg-slate-100 rounded-lg animate-pulse" />
          <div className="h-32 bg-slate-100 rounded-2xl animate-pulse" />
        </div>
      </div>
    );
  }

  if (error && !info) {
    return (
      <div className="min-h-[100dvh] bg-bg-warm flex items-center justify-center px-6 text-center">
        <div className="max-w-sm">
          <p className="text-[15px] font-semibold text-text-dark mb-1.5">Link not found</p>
          <p className="text-[13.5px] text-slate-500">{error}</p>
        </div>
      </div>
    );
  }

  const alreadyDone = submitted || info?.already_submitted;

  return (
    <div className="min-h-[100dvh] bg-bg-warm flex items-center justify-center px-6 py-10">
      <div className="w-full max-w-md">
        <div className="flex items-center gap-2.5 mb-6 justify-center">
          <span className="grid place-items-center w-8 h-8 rounded-xl bg-primary text-white font-bold text-sm">श</span>
          <span className="text-[16px] font-bold tracking-tight text-text-dark">Lipi</span>
        </div>

        {alreadyDone ? (
          <div className="bg-white rounded-3xl border border-slate-200/80 p-7 text-center">
            <p className="text-[15px] font-semibold text-text-dark mb-1.5">Thank you</p>
            <p className="text-[13.5px] text-slate-500 leading-relaxed">
              Your doctor has this ahead of your visit{info ? ` on ${formatSlot(info.slot_datetime)}` : ''}.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="bg-white rounded-3xl border border-slate-200/80 p-6 space-y-4">
            <div>
              <p className="text-[15px] font-bold text-text-dark">Before your visit</p>
              <p className="text-[12.5px] text-slate-500 mt-0.5">
                {info?.patient_name ? `${info.patient_name}, ` : ''}
                {info ? `your appointment is ${formatSlot(info.slot_datetime)}.` : ''} A few quick details help your doctor prepare.
              </p>
            </div>

            <div>
              <label className="block text-[12px] font-semibold text-slate-600 mb-1.5">What's the main reason for your visit?</label>
              <textarea
                value={chiefComplaint}
                onChange={e => setChiefComplaint(e.target.value)}
                rows={2}
                className={inputCls}
                placeholder="e.g. fever since 2 days, follow-up checkup"
              />
            </div>

            <div>
              <label className="block text-[12px] font-semibold text-slate-600 mb-1.5">Medications you're currently taking</label>
              <textarea
                value={currentMedications}
                onChange={e => setCurrentMedications(e.target.value)}
                rows={2}
                className={inputCls}
                placeholder="e.g. Telmisartan 40mg, once daily"
              />
            </div>

            <div>
              <label className="block text-[12px] font-semibold text-slate-600 mb-1.5">Any allergies?</label>
              <input
                value={allergies}
                onChange={e => setAllergies(e.target.value)}
                className={inputCls}
                placeholder="e.g. penicillin, none"
              />
            </div>

            <div>
              <label className="block text-[12px] font-semibold text-slate-600 mb-1.5">Anything else your doctor should know?</label>
              <textarea
                value={additionalNotes}
                onChange={e => setAdditionalNotes(e.target.value)}
                rows={2}
                className={inputCls}
              />
            </div>

            {error && <p className="text-[12.5px] text-alert-critical">{error}</p>}

            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-primary hover:bg-primary-dark text-white font-semibold text-[14px] py-3 rounded-full transition-colors disabled:opacity-60 cursor-pointer"
            >
              {submitting ? 'Sending...' : 'Send to my doctor'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
