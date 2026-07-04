import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';

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
  const [availability, setAvailability] = useState<AvailSlot[]>(DEFAULT_AVAIL);
  const [availSaved, setAvailSaved] = useState(false);

  useEffect(() => {
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

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-text-dark">
      <header className="border-b border-slate-200/80 sticky top-0 bg-white/90 backdrop-blur-md z-10 shadow-sm">
        <div className="max-w-3xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-slate-500 hover:text-primary transition-colors flex items-center text-xs font-semibold cursor-pointer"
            >
              <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Dashboard
            </button>
            <div className="h-4 w-px bg-slate-200" />
            <button onClick={() => navigate('/dashboard')} className="flex items-center gap-2 cursor-pointer group">
              <div className="w-6 h-6 bg-primary rounded-md flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform">
                <span className="font-bold text-white text-[10px]">श</span>
              </div>
              <span className="text-sm font-bold text-text-dark tracking-tight">Lipi</span>
            </button>
            <div className="h-4 w-px bg-slate-200" />
            <h1 className="text-sm font-bold text-slate-800">Appointment Availability</h1>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-10">
        <div className="border border-slate-200/80 rounded-2xl bg-white shadow-sm p-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-slate-800">Appointment Availability</h2>
              <p className="text-xs text-slate-500 mt-1">Patients can book slots via WhatsApp using your clinic code.</p>
            </div>
            <button
              type="button"
              onClick={saveAvailability}
              className="px-4 py-2 rounded-lg bg-primary hover:bg-primary-dark text-white text-xs font-bold transition-all cursor-pointer"
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
                  className={`px-3 py-1.5 rounded-full text-[12px] font-semibold transition-all cursor-pointer ${active ? 'bg-primary text-white' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}
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

        <div className="mt-6 border border-amber-100 rounded-xl bg-amber-50 p-4">
          <p className="text-xs text-amber-700 font-semibold flex items-start gap-2">
            <svg className="w-4 h-4 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Your schedule is stored securely with your account and used only for WhatsApp appointment booking.
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
        select.input-field {
          cursor: pointer;
        }
      `}</style>
    </div>
  );
}
