import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CalendarClock, Clock, Plus, Trash2, ArrowLeft, Phone, ClipboardList } from 'lucide-react';
import api from '../lib/api';

interface PreVisitForm {
  chief_complaint: string;
  current_medications: string;
  allergies: string;
  additional_notes: string;
  submitted_at: string;
}

interface Appointment {
  id: string;
  patient_name: string;
  patient_phone: string;
  slot_datetime: string;
  chief_complaint: string;
  status: string;
  pre_visit_form: PreVisitForm | null;
}

interface AvailabilitySlot {
  id?: string;
  day_of_week: number;
  start_time: string;
  end_time: string;
  slot_duration_minutes: number;
}

const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

function formatSlot(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString('en-IN', { weekday: 'short', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
}

export default function Appointments() {
  const navigate = useNavigate();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [availability, setAvailability] = useState<AvailabilitySlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedForm, setExpandedForm] = useState<string | null>(null);
  const [savingAvailability, setSavingAvailability] = useState(false);
  const [showAddSlot, setShowAddSlot] = useState(false);
  const [newSlot, setNewSlot] = useState<AvailabilitySlot>({ day_of_week: 0, start_time: '09:00', end_time: '13:00', slot_duration_minutes: 15 });

  const load = async () => {
    setLoading(true);
    try {
      const [apptRes, availRes] = await Promise.all([
        api.get('/doctor/appointments'),
        api.get('/doctor/availability'),
      ]);
      setAppointments(apptRes.data.appointments || []);
      setAvailability(availRes.data.slots || []);
    } catch {
      // Non-fatal — page still renders with empty state.
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  async function saveAvailability(slots: AvailabilitySlot[]) {
    setSavingAvailability(true);
    try {
      await api.put('/doctor/availability', slots.map(s => ({
        day_of_week: s.day_of_week, start_time: s.start_time, end_time: s.end_time, slot_duration_minutes: s.slot_duration_minutes,
      })));
      setAvailability(slots);
    } finally {
      setSavingAvailability(false);
    }
  }

  function handleAddSlot() {
    saveAvailability([...availability, newSlot]);
    setShowAddSlot(false);
    setNewSlot({ day_of_week: 0, start_time: '09:00', end_time: '13:00', slot_duration_minutes: 15 });
  }

  function handleRemoveSlot(index: number) {
    saveAvailability(availability.filter((_, i) => i !== index));
  }

  return (
    <div className="min-h-screen bg-bg-warm">
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center gap-3 sticky top-0 z-10">
        <button onClick={() => navigate('/dashboard')} className="text-slate-400 hover:text-slate-700 transition-colors cursor-pointer">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-[15px] font-bold text-slate-900 leading-tight">Appointments</h1>
          <p className="text-[11px] text-slate-400">Weekly availability and upcoming bookings</p>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* Weekly availability */}
        <section className="bg-white rounded-3xl border border-slate-200/80 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-[14px] font-bold text-slate-800">Weekly availability</h2>
            <button
              onClick={() => setShowAddSlot(true)}
              className="flex items-center gap-1 text-[12.5px] font-semibold text-primary hover:text-primary-dark transition-colors cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" /> Add slot
            </button>
          </div>

          {loading ? (
            <div className="space-y-2">
              {[1, 2].map(i => <div key={i} className="h-14 bg-slate-100 rounded-2xl animate-pulse" />)}
            </div>
          ) : availability.length === 0 ? (
            <div className="text-center py-8">
              <Clock className="w-7 h-7 text-slate-300 mx-auto mb-2" />
              <p className="text-[13px] font-medium text-slate-500">No availability set yet</p>
              <p className="text-[11.5px] text-slate-400 mt-1">Patients can't book until you add weekly hours.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {availability.map((slot, i) => (
                <div key={slot.id || i} className="flex items-center justify-between bg-slate-50 border border-slate-200/80 rounded-2xl px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-primary/8 grid place-items-center shrink-0">
                      <CalendarClock className="w-4.5 h-4.5 text-primary" strokeWidth={1.8} />
                    </div>
                    <div>
                      <p className="text-[13.5px] font-semibold text-slate-800">{DAY_NAMES[slot.day_of_week]}</p>
                      <p className="text-[12px] text-slate-500">{slot.start_time} to {slot.end_time} · {slot.slot_duration_minutes} min slots</p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleRemoveSlot(i)}
                    disabled={savingAvailability}
                    className="text-slate-300 hover:text-red-500 transition-colors cursor-pointer disabled:opacity-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {showAddSlot && (
            <div className="mt-4 pt-4 border-t border-slate-100 grid sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-[11.5px] font-semibold text-slate-600 mb-1">Day</label>
                <select
                  value={newSlot.day_of_week}
                  onChange={e => setNewSlot({ ...newSlot, day_of_week: Number(e.target.value) })}
                  className="w-full text-[13px] border border-slate-200 rounded-xl px-3 py-2 bg-white text-slate-700 focus:outline-none focus:border-primary/50"
                >
                  {DAY_NAMES.map((d, i) => <option key={d} value={i}>{d}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-[11.5px] font-semibold text-slate-600 mb-1">Slot length</label>
                <select
                  value={newSlot.slot_duration_minutes}
                  onChange={e => setNewSlot({ ...newSlot, slot_duration_minutes: Number(e.target.value) })}
                  className="w-full text-[13px] border border-slate-200 rounded-xl px-3 py-2 bg-white text-slate-700 focus:outline-none focus:border-primary/50"
                >
                  {[10, 15, 20, 30].map(m => <option key={m} value={m}>{m} minutes</option>)}
                </select>
              </div>
              <div>
                <label className="block text-[11.5px] font-semibold text-slate-600 mb-1">Start time</label>
                <input
                  type="time"
                  value={newSlot.start_time}
                  onChange={e => setNewSlot({ ...newSlot, start_time: e.target.value })}
                  className="w-full text-[13px] border border-slate-200 rounded-xl px-3 py-2 bg-white text-slate-700 focus:outline-none focus:border-primary/50"
                />
              </div>
              <div>
                <label className="block text-[11.5px] font-semibold text-slate-600 mb-1">End time</label>
                <input
                  type="time"
                  value={newSlot.end_time}
                  onChange={e => setNewSlot({ ...newSlot, end_time: e.target.value })}
                  className="w-full text-[13px] border border-slate-200 rounded-xl px-3 py-2 bg-white text-slate-700 focus:outline-none focus:border-primary/50"
                />
              </div>
              <div className="sm:col-span-2 flex justify-end gap-2 pt-1">
                <button onClick={() => setShowAddSlot(false)} className="text-[12.5px] font-medium text-slate-400 hover:text-slate-600 transition-colors cursor-pointer px-3 py-2">Cancel</button>
                <button
                  onClick={handleAddSlot}
                  disabled={savingAvailability}
                  className="text-[12.5px] font-semibold bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-full transition-colors cursor-pointer disabled:opacity-60"
                >
                  {savingAvailability ? 'Saving...' : 'Save slot'}
                </button>
              </div>
            </div>
          )}
        </section>

        {/* Upcoming appointments */}
        <section className="bg-white rounded-3xl border border-slate-200/80 p-6">
          <h2 className="text-[14px] font-bold text-slate-800 mb-4">Upcoming appointments</h2>

          {loading ? (
            <div className="space-y-2">
              {[1, 2, 3].map(i => <div key={i} className="h-16 bg-slate-100 rounded-2xl animate-pulse" />)}
            </div>
          ) : appointments.length === 0 ? (
            <div className="text-center py-10">
              <CalendarClock className="w-7 h-7 text-slate-300 mx-auto mb-2" />
              <p className="text-[13px] font-medium text-slate-500">No appointments booked yet</p>
              <p className="text-[11.5px] text-slate-400 mt-1">Bookings from WhatsApp or the patient portal will show up here.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {appointments.map((a, i) => (
                <motion.div
                  key={a.id}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.03 }}
                  className="bg-slate-50 border border-slate-200/80 rounded-2xl px-4 py-3"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-[13.5px] font-semibold text-slate-800">{a.patient_name || 'Patient'}</p>
                      <p className="text-[12px] text-slate-500 flex items-center gap-1.5">
                        <Clock className="w-3 h-3" /> {formatSlot(a.slot_datetime)}
                        {a.patient_phone && <span className="flex items-center gap-1"><Phone className="w-3 h-3" /> {a.patient_phone.slice(-10)}</span>}
                      </p>
                      {a.chief_complaint && <p className="text-[11.5px] text-slate-400 mt-0.5">{a.chief_complaint}</p>}
                    </div>
                    <span className={`text-[10.5px] font-bold uppercase tracking-wider px-2 py-1 rounded-full shrink-0 ${
                      a.status === 'confirmed' ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' : 'bg-slate-100 text-slate-500 border border-slate-200'
                    }`}>
                      {a.status}
                    </span>
                  </div>

                  {a.pre_visit_form && (
                    <button
                      onClick={() => setExpandedForm(expandedForm === a.id ? null : a.id)}
                      className="mt-2.5 flex items-center gap-1.5 text-[11.5px] font-semibold text-primary hover:text-primary-dark transition-colors cursor-pointer"
                    >
                      <ClipboardList className="w-3.5 h-3.5" />
                      {expandedForm === a.id ? 'Hide pre-visit form' : 'Pre-visit form submitted'}
                    </button>
                  )}
                  {a.pre_visit_form && expandedForm === a.id && (
                    <div className="mt-2 pt-2.5 border-t border-slate-200/80 space-y-1.5 text-[12px]">
                      {a.pre_visit_form.chief_complaint && <p><span className="font-semibold text-slate-600">Reason for visit: </span><span className="text-slate-500">{a.pre_visit_form.chief_complaint}</span></p>}
                      {a.pre_visit_form.current_medications && <p><span className="font-semibold text-slate-600">Current medications: </span><span className="text-slate-500">{a.pre_visit_form.current_medications}</span></p>}
                      {a.pre_visit_form.allergies && <p><span className="font-semibold text-slate-600">Allergies: </span><span className="text-slate-500">{a.pre_visit_form.allergies}</span></p>}
                      {a.pre_visit_form.additional_notes && <p><span className="font-semibold text-slate-600">Additional notes: </span><span className="text-slate-500">{a.pre_visit_form.additional_notes}</span></p>}
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
