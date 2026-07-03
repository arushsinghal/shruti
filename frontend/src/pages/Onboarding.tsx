import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { completeOnboarding, getClinicInviteCode } from '../lib/api';
import api from '../lib/api';

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

export default function Onboarding() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [nmcNumber, setNmcNumber] = useState('');
  const [specialization, setSpecialization] = useState('');
  const [clinicName, setClinicName] = useState('');
  const [clinicAddress, setClinicAddress] = useState('');
  const [clinicPhone, setClinicPhone] = useState('');
  const [whatsappPhone, setWhatsappPhone] = useState('');
  const [clinicCode, setClinicCode] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const nmcValid = /^[A-Z]{2,3}-?\d{4,7}$/i.test(nmcNumber.trim());

  async function handleComplete() {
    if (!nmcValid) { setError('NMC number format invalid (e.g. MH-12345)'); return; }
    if (!specialization) { setError('Please select a specialization'); return; }
    setError('');
    setSaving(true);
    try {
      await completeOnboarding({
        nmc_number: nmcNumber.trim(),
        specialization,
        clinic_name: clinicName || undefined,
        clinic_address: clinicAddress || undefined,
        clinic_phone: clinicPhone || undefined,
      });
      // Save WhatsApp number to doctor profile
      if (whatsappPhone.trim()) {
        await api.put('/auth/doctor-profile', { whatsapp_phone: whatsappPhone.trim() }).catch(() => {});
      }
      // Get clinic code for the "you're live" step
      const code = await getClinicInviteCode().catch(() => ({ code: '' }));
      setClinicCode(code.code || '');
      setStep(2);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save. Please try again.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        {/* Progress */}
        <div className="flex items-center justify-center gap-2 mb-8">
          {[0, 1, 2].map(i => (
            <div key={i} className={`h-1.5 rounded-full transition-all ${i <= step ? 'w-16 bg-indigo-600' : 'w-8 bg-slate-200'}`} />
          ))}
        </div>

        <div className="bg-white rounded-2xl border border-indigo-100 shadow-sm overflow-hidden">
          {/* Header */}
          <div className="px-8 py-6 bg-gradient-to-r from-indigo-50 to-cyan-50 border-b border-indigo-100">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-cyan-500 rounded-xl flex items-center justify-center shadow-md">
                <span className="font-bold text-white text-sm">श</span>
              </div>
              <div>
                <h1 className="text-lg font-bold text-slate-800">Welcome to Lipi</h1>
                <p className="text-xs text-slate-500">Complete your profile to start using the OPD administration service</p>
              </div>
            </div>
          </div>

          <div className="p-8">
            {error && (
              <div className="mb-6 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 font-semibold">{error}</div>
            )}

            {step === 0 && (
              <div className="space-y-5">
                <div>
                  <label className="block text-xs font-bold text-slate-600 uppercase tracking-wide mb-1.5">
                    NMC / SMC Registration Number <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="text"
                    value={nmcNumber}
                    onChange={e => setNmcNumber(e.target.value)}
                    placeholder="MH-12345"
                    className="w-full border border-slate-200 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent"
                  />
                  <p className="text-[11px] text-slate-400 mt-1.5">
                    Your National Medical Commission or State Medical Council registration number.
                    {nmcNumber && (nmcValid
                      ? <span className="text-emerald-600 font-semibold ml-1">Valid format</span>
                      : <span className="text-red-500 font-semibold ml-1">Invalid — expected format: XX-NNNNN</span>
                    )}
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-600 uppercase tracking-wide mb-1.5">
                    Specialization <span className="text-red-400">*</span>
                  </label>
                  <select
                    value={specialization}
                    onChange={e => setSpecialization(e.target.value)}
                    className="w-full border border-slate-200 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent bg-white cursor-pointer"
                  >
                    <option value="">Select your specialization</option>
                    {SPECIALIZATIONS.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>

                <button
                  onClick={() => { if (nmcValid && specialization) setStep(1); else setError('Fill all required fields'); }}
                  disabled={!nmcValid || !specialization}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-700 hover:to-cyan-700 disabled:opacity-40 text-white text-sm font-bold transition-all shadow-md"
                >
                  Next — Clinic Details
                </button>
              </div>
            )}

            {step === 1 && (
              <div className="space-y-5">
                <p className="text-xs text-slate-500 font-medium">Optional — this appears on printed prescriptions.</p>

                <div>
                  <label className="block text-xs font-bold text-slate-600 uppercase tracking-wide mb-1.5">Clinic / Hospital Name</label>
                  <input
                    type="text"
                    value={clinicName}
                    onChange={e => setClinicName(e.target.value)}
                    placeholder="City Care Clinic"
                    className="w-full border border-slate-200 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-600 uppercase tracking-wide mb-1.5">Address</label>
                  <textarea
                    value={clinicAddress}
                    onChange={e => setClinicAddress(e.target.value)}
                    placeholder="123, MG Road, Pune 411001"
                    rows={2}
                    className="w-full border border-slate-200 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent resize-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-600 uppercase tracking-wide mb-1.5">Phone</label>
                  <input
                    type="tel"
                    value={clinicPhone}
                    onChange={e => setClinicPhone(e.target.value)}
                    placeholder="+91 98765 43210"
                    className="w-full border border-slate-200 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-600 uppercase tracking-wide mb-1.5">
                    Your WhatsApp Number <span className="text-slate-400 font-normal normal-case">(for voice-note consultations)</span>
                  </label>
                  <input
                    type="tel"
                    value={whatsappPhone}
                    onChange={e => setWhatsappPhone(e.target.value)}
                    placeholder="+91 98765 43210"
                    className="w-full border border-slate-200 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Send voice notes to Lipi from this number after each consultation.</p>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => setStep(0)}
                    className="px-6 py-3 rounded-xl border border-slate-200 text-slate-600 text-sm font-semibold hover:bg-slate-50"
                  >
                    Back
                  </button>
                  <button
                    onClick={handleComplete}
                    disabled={saving}
                    className="flex-1 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-700 hover:to-cyan-700 disabled:opacity-50 text-white text-sm font-bold transition-all shadow-md"
                  >
                    {saving ? 'Setting up your clinic…' : 'Complete Setup'}
                  </button>
                </div>
              </div>
            )}

            {/* Step 2 — You're live */}
            {step === 2 && (
              <div className="space-y-6 text-center">
                <div className="w-16 h-16 bg-emerald-100 rounded-full grid place-items-center mx-auto">
                  <svg className="w-8 h-8 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-xl font-bold text-slate-800">Your clinic is live!</h2>
                  <p className="text-[13px] text-slate-500 mt-1">Share your clinic code with patients and staff.</p>
                </div>

                {clinicCode && (
                  <div className="bg-slate-50 border border-slate-200 rounded-2xl p-6">
                    <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">Your clinic code</p>
                    <p className="font-mono text-4xl font-bold tracking-[0.25em] text-slate-800">{clinicCode}</p>
                    <p className="text-[11px] text-slate-400 mt-3">Patients text this code to Lipi's WhatsApp number to send their pre-visit brief.</p>
                  </div>
                )}

                <div className="space-y-2 text-left text-[13px] text-slate-600">
                  <p className="font-semibold text-slate-700 mb-2">What's next:</p>
                  <p>✅ Send a voice note to Lipi on WhatsApp after your first consultation</p>
                  <p>✅ Share your clinic code with patients — they text before they arrive</p>
                  <p>✅ Check your dashboard after the first consult</p>
                </div>

                <button
                  onClick={() => navigate('/dashboard')}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 text-white text-sm font-bold shadow-md"
                >
                  Go to Dashboard →
                </button>
              </div>
            )}
          </div>
        </div>

        <p className="text-center text-[11px] text-slate-400 mt-4">
          Your NMC number is verified for format only. ABDM registry verification coming soon.
        </p>
      </div>
    </div>
  );
}
