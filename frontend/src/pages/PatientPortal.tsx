import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

interface Medication {
  name?: string;
  dose?: string;
  frequency?: string;
  duration?: string;
}

interface Prescription {
  session_id: string;
  patient_name: string | null;
  doctor_name: string | null;
  status: string;
  created_at: string;
  diagnosis: string | null;
  medications: Medication[];
}

interface LabOrder {
  session_id: string;
  labs: string[];
  dispatched_at: string;
  status: string;
}

interface FollowUp {
  reminder_id: string;
  follow_up_text: string;
  follow_up_date: string | null;
  doctor_name: string | null;
  status: string;
}

interface PatientSummary {
  phone_last4: string;
  prescription: Prescription | null;
  lab_order: LabOrder | null;
  follow_up: FollowUp | null;
  patient_id: string | null;
  doctor_user_id: string | null;
}

interface Slot {
  datetime: string;
  label: string;
}

interface Visit {
  session_id: string;
  doctor_name: string | null;
  created_at: string;
  diagnosis: string | null;
  medication_count: number;
}

function fmt(iso: string | null): string {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' });
  } catch {
    return iso;
  }
}

export default function PatientPortal() {
  const { phone } = useParams<{ phone: string }>();
  const [summary, setSummary] = useState<PatientSummary | null>(null);
  const [visits, setVisits] = useState<Visit[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [showBooking, setShowBooking] = useState(false);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [booked, setBooked] = useState<string | null>(null);
  const [bookingError, setBookingError] = useState('');

  useEffect(() => {
    if (!phone) return;
    const digits = phone.replace(/\D/g, '');
    fetch(`/api/public/patient-summary?phone=${digits}`)
      .then(async r => {
        if (!r.ok) {
          const body = await r.json().catch(() => ({}));
          throw new Error(body.detail || 'Records not found');
        }
        return r.json() as Promise<PatientSummary>;
      })
      .then(setSummary)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));

    // History is a separate, non-blocking fetch — a patient with only one
    // visit simply won't see the history section, no error shown for that.
    fetch(`/api/public/patient-history?phone=${digits}`)
      .then(async r => (r.ok ? (r.json() as Promise<{ visits: Visit[] }>) : { visits: [] }))
      .then(data => setVisits(data.visits || []))
      .catch(() => {});
  }, [phone]);

  async function handleShowBooking() {
    if (!summary?.patient_id || !summary?.doctor_user_id) return;
    setShowBooking(true);
    setSlotsLoading(true);
    try {
      const r = await fetch(`/api/public/patients/${summary.patient_id}/available-slots?doctor_user_id=${summary.doctor_user_id}`);
      const data = await r.json();
      setSlots(data.slots || []);
    } catch {
      setBookingError('Could not load available slots.');
    } finally {
      setSlotsLoading(false);
    }
  }

  async function handleBookSlot(slot: Slot) {
    if (!summary?.patient_id || !summary?.doctor_user_id) return;
    setBookingError('');
    try {
      const r = await fetch(`/api/public/patients/${summary.patient_id}/book-appointment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ doctor_user_id: summary.doctor_user_id, slot_datetime: slot.datetime }),
      });
      if (!r.ok) throw new Error();
      setBooked(slot.label);
      setShowBooking(false);
    } catch {
      setBookingError('Could not book this slot. Please try another.');
    }
  }

  return (
    <div className="min-h-screen bg-[#FAFAF7] px-4 py-10">
      <div className="max-w-xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-2 mb-2">
          <span className="grid place-items-center w-9 h-9 rounded-xl bg-primary text-white font-bold text-base">श</span>
          <span className="text-xl font-bold text-text-dark tracking-tight">Lipi</span>
        </div>
        <h1 className="text-[1.35rem] font-bold tracking-tight text-text-dark">Your health summary</h1>

        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map(i => <div key={i} className="h-28 bg-slate-100 rounded-2xl animate-pulse" />)}
          </div>
        )}

        {error && (
          <div className="rounded-2xl bg-red-50 border border-red-100 px-5 py-4 text-[13.5px] text-red-700">
            {error}
          </div>
        )}

        {summary && (
          <>
            <p className="text-[13px] text-slate-500">Number ending in •••{summary.phone_last4}</p>

            {/* Prescription card */}
            {summary.prescription && (
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
                  <p className="font-semibold text-[14px] text-text-dark">Prescription</p>
                  {summary.prescription.doctor_name && (
                    <p className="text-[12px] text-slate-500">Dr. {summary.prescription.doctor_name}</p>
                  )}
                </div>
                <div className="px-5 py-4 space-y-3">
                  {summary.prescription.diagnosis && (
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-0.5">Diagnosis</p>
                      <p className="text-[13.5px] text-text-dark">{summary.prescription.diagnosis}</p>
                    </div>
                  )}
                  {summary.prescription.medications.length > 0 && (
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Medicines</p>
                      <div className="space-y-1.5">
                        {summary.prescription.medications.map((m, i) => (
                          <div key={i} className="flex items-start gap-2 text-[13px]">
                            <span className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0" />
                            <span className="text-text-dark font-medium">{m.name || 'Unknown'}</span>
                            {(m.dose || m.frequency || m.duration) && (
                              <span className="text-slate-500">
                                {[m.dose, m.frequency, m.duration].filter(Boolean).join(' · ')}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  <p className="text-[11px] text-slate-400 pt-1">{fmt(summary.prescription.created_at)}</p>
                </div>
              </div>
            )}

            {/* Lab order card */}
            {summary.lab_order && summary.lab_order.labs.length > 0 && (
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="px-5 py-4 border-b border-slate-100">
                  <p className="font-semibold text-[14px] text-text-dark">Lab tests ordered</p>
                </div>
                <div className="px-5 py-4 space-y-1.5">
                  {summary.lab_order.labs.map((lab, i) => (
                    <div key={i} className="flex items-center gap-2 text-[13px]">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                      <span className="text-text-dark">{lab}</span>
                    </div>
                  ))}
                  <p className="text-[11px] text-slate-400 pt-1">{fmt(summary.lab_order.dispatched_at)}</p>
                </div>
              </div>
            )}

            {/* Follow-up card */}
            {summary.follow_up && (
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
                  <p className="font-semibold text-[14px] text-text-dark">Follow-up appointment</p>
                  {summary.follow_up.status === 'confirmed' && (
                    <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">Confirmed</span>
                  )}
                </div>
                <div className="px-5 py-4 space-y-1">
                  <p className="text-[13.5px] text-text-dark">{summary.follow_up.follow_up_text}</p>
                  {summary.follow_up.follow_up_date && (
                    <p className="text-[12px] text-slate-500">{fmt(summary.follow_up.follow_up_date)}</p>
                  )}
                  {summary.follow_up.doctor_name && (
                    <p className="text-[12px] text-slate-400">Dr. {summary.follow_up.doctor_name}</p>
                  )}
                </div>
              </div>
            )}

            {/* Visit history */}
            {visits.length > 1 && (
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <button
                  onClick={() => setShowHistory(!showHistory)}
                  className="w-full px-5 py-4 border-b border-slate-100 flex items-center justify-between cursor-pointer"
                >
                  <p className="font-semibold text-[14px] text-text-dark">Your visit history</p>
                  <span className="text-[12px] text-slate-400">{showHistory ? 'Hide' : `${visits.length} visits`}</span>
                </button>
                {showHistory && (
                  <div className="px-5 py-2">
                    {visits.map((v, i) => (
                      <div key={v.session_id} className={`py-3 flex items-start justify-between gap-3 ${i > 0 ? 'border-t border-slate-100' : ''}`}>
                        <div>
                          <p className="text-[13px] font-medium text-text-dark">{v.diagnosis || 'Consultation'}</p>
                          <p className="text-[11.5px] text-slate-400">
                            {fmt(v.created_at)}{v.doctor_name ? ` · Dr. ${v.doctor_name}` : ''}
                          </p>
                        </div>
                        {v.medication_count > 0 && (
                          <span className="text-[11px] text-slate-400 shrink-0">{v.medication_count} medicine{v.medication_count !== 1 ? 's' : ''}</span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Book next appointment */}
            {summary.patient_id && summary.doctor_user_id && (
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="px-5 py-4 border-b border-slate-100">
                  <p className="font-semibold text-[14px] text-text-dark">Book your next visit</p>
                </div>
                <div className="px-5 py-4">
                  {booked ? (
                    <p className="text-[13px] text-emerald-700">Booked for {booked}. Your doctor has been notified.</p>
                  ) : !showBooking ? (
                    <button
                      onClick={handleShowBooking}
                      className="text-[13px] font-semibold text-primary hover:text-primary-dark transition-colors cursor-pointer"
                    >
                      See available times →
                    </button>
                  ) : slotsLoading ? (
                    <div className="space-y-2">
                      {[1, 2].map(i => <div key={i} className="h-10 bg-slate-100 rounded-xl animate-pulse" />)}
                    </div>
                  ) : slots.length === 0 ? (
                    <p className="text-[13px] text-slate-400">No slots available right now. Please contact the clinic directly.</p>
                  ) : (
                    <div className="space-y-2">
                      {slots.map(s => (
                        <button
                          key={s.datetime}
                          onClick={() => handleBookSlot(s)}
                          className="w-full text-left text-[13px] text-text-dark bg-slate-50 hover:bg-primary/5 border border-slate-200 hover:border-primary/30 rounded-xl px-4 py-2.5 transition-colors cursor-pointer"
                        >
                          {s.label}
                        </button>
                      ))}
                    </div>
                  )}
                  {bookingError && <p className="text-[11.5px] text-alert-critical mt-2">{bookingError}</p>}
                </div>
              </div>
            )}

            <p className="text-[11px] text-slate-400 text-center pt-2 leading-relaxed">
              This summary is for your reference only. Always consult your doctor before changing medicines.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
