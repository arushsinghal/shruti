import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDoctorProfile, updateDoctorProfile } from '../lib/api';
import api from '../lib/api';

export interface DoctorProfile {
  name: string;
  mci_number: string;
  specialization: string;
  clinic_name: string;
  clinic_address: string;
  clinic_phone: string;
  clinic_email: string;
  whatsapp_phone: string;
}

const EMPTY_PROFILE: DoctorProfile = { name: '', mci_number: '', specialization: '', clinic_name: '', clinic_address: '', clinic_phone: '', clinic_email: '', whatsapp_phone: '' };

const SPECIALIZATIONS = [
  'General Physician / Family Medicine',
  'Internal Medicine',
  'Paediatrics',
  'Gynaecology & Obstetrics',
  'Orthopaedics',
  'ENT',
  'Dermatology',
  'Ophthalmology',
  'Cardiology',
  'Neurology',
  'Gastroenterology',
  'Pulmonology',
  'Nephrology',
  'Endocrinology',
  'Psychiatry',
  'General Surgery',
  'Dentistry',
  'Other',
];

const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

interface AvailSlot { day_of_week: number; start_time: string; end_time: string; slot_duration_minutes: number; }

const DEFAULT_AVAIL: AvailSlot[] = [
  { day_of_week: 0, start_time: '09:00', end_time: '13:00', slot_duration_minutes: 15 },
  { day_of_week: 1, start_time: '09:00', end_time: '13:00', slot_duration_minutes: 15 },
  { day_of_week: 2, start_time: '09:00', end_time: '13:00', slot_duration_minutes: 15 },
  { day_of_week: 3, start_time: '09:00', end_time: '13:00', slot_duration_minutes: 15 },
  { day_of_week: 4, start_time: '09:00', end_time: '13:00', slot_duration_minutes: 15 },
];

export default function DoctorProfilePage() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<DoctorProfile>(EMPTY_PROFILE);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [availability, setAvailability] = useState<AvailSlot[]>(DEFAULT_AVAIL);
  const [availSaved, setAvailSaved] = useState(false);

  useEffect(() => {
    getDoctorProfile()
      .then((data) => {
        if (data && Object.keys(data).length > 0) {
          setProfile({ ...EMPTY_PROFILE, ...data } as DoctorProfile);
        }
      })
      .catch(() => {});
    api.get('/doctor/availability').then(r => {
      if (r.data?.slots?.length > 0) setAvailability(r.data.slots);
    }).catch(() => {});
  }, []);

  async function saveAvailability() {
    await api.put('/doctor/availability', availability);
    setAvailSaved(true);
    setTimeout(() => setAvailSaved(false), 3000);
  }

  function updateAvailSlot(idx: number, field: keyof AvailSlot, value: string | number) {
    setAvailability(prev => prev.map((s, i) => i === idx ? { ...s, [field]: value } : s));
  }

  function toggleDay(dow: number) {
    const exists = availability.find(s => s.day_of_week === dow);
    if (exists) {
      setAvailability(prev => prev.filter(s => s.day_of_week !== dow));
    } else {
      setAvailability(prev => [...prev, { day_of_week: dow, start_time: '09:00', end_time: '13:00', slot_duration_minutes: 15 }].sort((a, b) => a.day_of_week - b.day_of_week));
    }
  }

  useEffect(() => { setSaved(false); }, [profile]);

  function handleChange(field: keyof DoctorProfile, value: string) {
    setProfile((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await updateDoctorProfile(profile as unknown as Record<string, string>);
      setSaved(true);
    } catch {
      alert('Failed to save profile. Please try again.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-text-dark">
      <header className="border-b border-slate-200/80 sticky top-0 bg-white/90 backdrop-blur-md z-10 shadow-sm">
        <div className="max-w-3xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-slate-500 hover:text-indigo-600 transition-colors flex items-center text-xs font-semibold cursor-pointer"
            >
              <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Dashboard
            </button>
            <div className="h-4 w-px bg-slate-200" />
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-gradient-to-br from-indigo-600 to-cyan-500 rounded-md flex items-center justify-center shadow-sm">
                <span className="font-bold text-white text-[10px]">श</span>
              </div>
              <span className="text-sm font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-700 to-cyan-700">Lipi</span>
            </div>
            <div className="h-4 w-px bg-slate-200" />
            <h1 className="text-sm font-bold text-slate-800">Doctor Profile</h1>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-10">
        <div className="border border-indigo-100 rounded-2xl bg-white shadow-sm p-8">
          <div className="mb-6">
            <h2 className="text-lg font-bold text-slate-800">Your clinical profile</h2>
            <p className="text-xs text-slate-500 mt-1">This information appears on printed prescriptions. Stored locally on this device only.</p>
          </div>

          <form onSubmit={handleSave} className="space-y-5">
            <div className="grid sm:grid-cols-2 gap-5">
              <Field label="Full Name" required>
                <input
                  type="text"
                  value={profile.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  placeholder="Dr. Priya Sharma"
                  required
                  className="input-field"
                />
              </Field>
              <Field label="MCI / SMC Registration No." required>
                <input
                  type="text"
                  value={profile.mci_number}
                  onChange={(e) => handleChange('mci_number', e.target.value)}
                  placeholder="MH-12345"
                  required
                  className="input-field"
                />
              </Field>
            </div>

            <Field label="Specialization">
              <select
                value={profile.specialization}
                onChange={(e) => handleChange('specialization', e.target.value)}
                className="input-field"
              >
                <option value="">Select specialization</option>
                {SPECIALIZATIONS.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </Field>

            <div className="pt-2 border-t border-slate-100">
              <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Clinic Details</p>
              <div className="space-y-4">
                <Field label="Clinic / Hospital Name">
                  <input
                    type="text"
                    value={profile.clinic_name}
                    onChange={(e) => handleChange('clinic_name', e.target.value)}
                    placeholder="City Care Clinic"
                    className="input-field"
                  />
                </Field>
                <Field label="Address">
                  <textarea
                    value={profile.clinic_address}
                    onChange={(e) => handleChange('clinic_address', e.target.value)}
                    placeholder="123, MG Road, Pune, Maharashtra 411001"
                    rows={2}
                    className="input-field resize-none"
                  />
                </Field>
                <div className="grid sm:grid-cols-2 gap-4">
                  <Field label="Phone">
                    <input
                      type="tel"
                      value={profile.clinic_phone}
                      onChange={(e) => handleChange('clinic_phone', e.target.value)}
                      placeholder="+91 98765 43210"
                      className="input-field"
                    />
                  </Field>
                  <Field label="Email">
                    <input
                      type="email"
                      value={profile.clinic_email}
                      onChange={(e) => handleChange('clinic_email', e.target.value)}
                      placeholder="doctor@clinic.in"
                      className="input-field"
                    />
                  </Field>
                </div>

                <Field label="WhatsApp Number (for voice-note consultations)">
                  <input
                    type="tel"
                    value={profile.whatsapp_phone}
                    onChange={(e) => handleChange('whatsapp_phone', e.target.value)}
                    placeholder="+91 98765 43210 (same number you send voice notes from)"
                    className="input-field"
                  />
                </Field>
              </div>
            </div>

            {/* ── Appointment availability ──────────────────────────── */}
            <div className="section-card mt-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-base font-bold text-slate-800">Appointment Availability</h2>
                  <p className="text-[12px] text-slate-500 mt-0.5">Patients can book slots via WhatsApp using your clinic code.</p>
                </div>
                <button
                  type="button"
                  onClick={saveAvailability}
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all"
                >
                  {availSaved ? '✓ Saved' : 'Save Schedule'}
                </button>
              </div>

              <div className="flex flex-wrap gap-2 mb-4">
                {DAY_NAMES.map((day, dow) => {
                  const active = availability.some(s => s.day_of_week === dow);
                  return (
                    <button
                      key={dow}
                      type="button"
                      onClick={() => toggleDay(dow)}
                      className={`px-3 py-1.5 rounded-full text-[12px] font-semibold transition-all ${active ? 'bg-primary text-white' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}
                    >
                      {day.slice(0, 3)}
                    </button>
                  );
                })}
              </div>

              <div className="space-y-2">
                {availability.sort((a, b) => a.day_of_week - b.day_of_week).map((slot, idx) => (
                  <div key={slot.day_of_week} className="flex items-center gap-3 text-[13px]">
                    <span className="w-20 font-medium text-slate-700 shrink-0">{DAY_NAMES[slot.day_of_week]}</span>
                    <input type="time" value={slot.start_time} onChange={e => updateAvailSlot(idx, 'start_time', e.target.value)} className="input-field w-28 text-[12px] py-1.5" />
                    <span className="text-slate-400">to</span>
                    <input type="time" value={slot.end_time} onChange={e => updateAvailSlot(idx, 'end_time', e.target.value)} className="input-field w-28 text-[12px] py-1.5" />
                    <select value={slot.slot_duration_minutes} onChange={e => updateAvailSlot(idx, 'slot_duration_minutes', Number(e.target.value))} className="input-field w-24 text-[12px] py-1.5">
                      <option value={10}>10 min</option>
                      <option value={15}>15 min</option>
                      <option value={20}>20 min</option>
                      <option value={30}>30 min</option>
                    </select>
                  </div>
                ))}
                {availability.length === 0 && (
                  <p className="text-[12px] text-slate-400">No days selected. Click days above to add availability.</p>
                )}
              </div>
            </div>

            <div className="pt-4 flex items-center gap-4">
              <button
                type="submit"
                disabled={saving}
                className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-700 hover:to-cyan-700 disabled:opacity-50 text-white text-sm font-bold transition-all shadow-md cursor-pointer"
              >
                {saving ? 'Saving…' : 'Save Profile'}
              </button>
              {saved && (
                <span className="text-xs text-emerald-600 font-bold flex items-center gap-1.5">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                  Saved
                </span>
              )}
            </div>
          </form>
        </div>

        <div className="mt-6 border border-amber-100 rounded-xl bg-amber-50 p-4">
          <p className="text-xs text-amber-700 font-semibold flex items-start gap-2">
            <svg className="w-4 h-4 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Your profile data is stored securely with your account. It appears on printed prescriptions only.
          </p>
        </div>
      </main>

      <style>{`
        .input-field {
          width: 100%;
          border: 1px solid #e2e8f0;
          border-radius: 0.5rem;
          padding: 0.5rem 0.75rem;
          font-size: 0.875rem;
          color: #1e293b;
          background: white;
          transition: border-color 0.15s;
          outline: none;
          font-family: inherit;
        }
        .input-field:focus {
          border-color: #818cf8;
          box-shadow: 0 0 0 3px rgba(129,140,248,0.15);
        }
        .input-field::placeholder {
          color: #94a3b8;
        }
        select.input-field {
          cursor: pointer;
        }
      `}</style>
    </div>
  );
}

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <label className="text-xs font-bold text-slate-600 uppercase tracking-wide">
        {label}{required && <span className="text-red-400 ml-0.5">*</span>}
      </label>
      {children}
    </div>
  );
}
