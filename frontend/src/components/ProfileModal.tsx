import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../lib/api';

interface Profile {
  name: string;
  mci_number: string;
  clinic_name: string;
  clinic_address: string;
  clinic_phone: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSaved: (profile: Profile) => void;
}

const inputCls =
  'w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-[13.5px] text-text-dark placeholder-slate-400 focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/10 focus:bg-white transition-all';
const labelCls = 'block text-[11.5px] font-semibold text-slate-500 mb-1.5 uppercase tracking-wide';

export default function ProfileModal({ isOpen, onClose, onSaved }: Props) {
  const [form, setForm] = useState<Profile>({
    name: '', mci_number: '', clinic_name: '', clinic_address: '', clinic_phone: '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isOpen) return;
    api.get('/auth/doctor-profile').then(r => {
      if (r.data && r.data.name) setForm(r.data);
    }).catch(() => {});
  }, [isOpen]);

  const set = (k: keyof Profile) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim()) { setError('Doctor name is required'); return; }
    setSaving(true);
    setError('');
    try {
      await api.put('/auth/doctor-profile', form);
      onSaved(form);
      onClose();
    } catch {
      setError('Failed to save profile. Please try again.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          onClick={e => { if (e.target === e.currentTarget) onClose(); }}
        >
          <motion.div
            className="bg-white rounded-2xl shadow-2xl w-full max-w-lg border border-slate-100"
            initial={{ opacity: 0, y: 16, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.97 }}
            transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
          >
            {/* Header */}
            <div className="px-6 pt-6 pb-4 border-b border-slate-100 flex items-start justify-between">
              <div>
                <h2 className="text-[16px] font-bold text-text-dark tracking-tight">Doctor Profile</h2>
                <p className="text-[13px] text-slate-400 mt-0.5">Used on prescription headers and lab orders</p>
              </div>
              <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors mt-0.5 cursor-pointer">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleSave} className="px-6 py-5 space-y-4">
              {error && (
                <div className="bg-red-50 border border-red-100 text-red-600 px-3.5 py-2.5 rounded-xl text-[13px]">
                  {error}
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className={labelCls}>Full Name *</label>
                  <input
                    type="text" required value={form.name} onChange={set('name')}
                    placeholder="Dr. Priya Sharma" className={inputCls}
                  />
                </div>
                <div>
                  <label className={labelCls}>MCI / State Reg. No.</label>
                  <input
                    type="text" value={form.mci_number} onChange={set('mci_number')}
                    placeholder="MH-12345" className={inputCls}
                  />
                </div>
                <div>
                  <label className={labelCls}>Clinic Phone</label>
                  <input
                    type="tel" value={form.clinic_phone} onChange={set('clinic_phone')}
                    placeholder="+91 98765 43210" className={inputCls}
                  />
                </div>
                <div className="col-span-2">
                  <label className={labelCls}>Clinic / Hospital Name</label>
                  <input
                    type="text" value={form.clinic_name} onChange={set('clinic_name')}
                    placeholder="Medanta The Medicity, Gurugram" className={inputCls}
                  />
                </div>
                <div className="col-span-2">
                  <label className={labelCls}>Clinic Address</label>
                  <textarea
                    rows={2} value={form.clinic_address} onChange={set('clinic_address')}
                    placeholder="Sector 38, Gurugram, Haryana 122001"
                    className={inputCls + ' resize-none'}
                  />
                </div>
              </div>

              <div className="flex items-center gap-3 pt-1">
                <button
                  type="submit" disabled={saving}
                  className="flex-1 bg-primary hover:bg-primary-dark disabled:opacity-60 text-white font-semibold text-[13.5px] py-2.5 rounded-xl transition-all active:scale-[0.98] cursor-pointer"
                >
                  {saving ? 'Saving…' : 'Save Profile'}
                </button>
                <button
                  type="button" onClick={onClose}
                  className="px-4 py-2.5 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 text-[13.5px] font-medium transition-all cursor-pointer"
                >
                  Later
                </button>
              </div>

              <p className="text-[11px] text-slate-400 text-center">
                Your profile is stored securely and only used to generate prescription headers.
              </p>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
