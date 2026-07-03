import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { sharePrescriptionViaWhatsapp } from '../lib/api';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
  patientName?: string;
  onSent?: () => void;
}

export default function ShareWhatsappModal({ isOpen, onClose, sessionId, patientName, onSent }: Props) {
  const [phone, setPhone] = useState('');
  const [consent, setConsent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [successData, setSuccessData] = useState<{ link: string } | null>(null);
  const [error, setError] = useState('');

  const handleShare = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!consent) {
      setError('Patient consent is required to share.');
      return;
    }
    setError('');
    setLoading(true);

    try {
      const res = await sharePrescriptionViaWhatsapp(sessionId, phone, consent);
      if (res.success) {
        setSuccessData({ link: res.link });
        onSent?.();
      } else {
        setError('Failed to share prescription.');
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'An error occurred during sharing.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyLink = () => {
    if (successData?.link) {
      navigator.clipboard.writeText(successData.link);
      alert('Prescription link copied to clipboard!');
    }
  };

  const resetAndClose = () => {
    setPhone('');
    setConsent(false);
    setSuccessData(null);
    setError('');
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center px-4 font-sans text-left">
          {/* Backdrop */}
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={resetAndClose}
            className="absolute inset-0 bg-[#000000] bg-opacity-70 backdrop-blur-sm"
          />
          
          {/* Modal Content */}
          <motion.div 
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.2 }}
            className="relative w-full max-w-md bg-[#111827] rounded-2xl shadow-2xl overflow-hidden border border-white/10"
          >
            <div className="px-6 py-4 border-b border-white/10 flex justify-between items-center bg-[#1F2937]/50">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <svg className="w-5 h-5 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                </svg>
                Share via WhatsApp
              </h3>
              <button onClick={resetAndClose} className="text-gray-400 hover:text-white transition-colors cursor-pointer">
                ✕
              </button>
            </div>

            {successData ? (
              <div className="p-6 space-y-5 text-center">
                <div className="w-12 h-12 bg-teal-500/10 text-teal-400 rounded-full flex items-center justify-center mx-auto">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div className="space-y-2">
                  <h4 className="text-md font-semibold text-white">Prescription Dispatched</h4>
                  <p className="text-xs text-gray-400">
                    The prescription link has been sent to the patient via WhatsApp.
                  </p>
                </div>

                <div className="bg-gray-900/80 p-3 rounded-xl border border-white/5 break-all text-xs text-gray-300 font-mono select-all">
                  {successData.link}
                </div>

                <div className="flex gap-3 justify-center pt-2">
                  <button 
                    onClick={handleCopyLink}
                    className="px-4 py-2 text-xs font-semibold text-white bg-gray-800 hover:bg-gray-700 rounded-lg cursor-pointer transition-colors"
                  >
                    Copy Link
                  </button>
                  <button 
                    onClick={resetAndClose}
                    className="px-4 py-2 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-500 rounded-lg cursor-pointer transition-colors"
                  >
                    Done
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleShare} className="p-6 space-y-5">
                {patientName && (
                  <div className="bg-white/5 p-3 rounded-xl text-xs text-gray-300 flex items-center justify-between">
                    <span>Patient Name:</span>
                    <strong className="text-white font-medium">{patientName}</strong>
                  </div>
                )}

                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1.5">
                    Patient Phone Number (WhatsApp)
                  </label>
                  <input 
                    type="tel" 
                    required 
                    value={phone} 
                    onChange={e => setPhone(e.target.value)}
                    className="w-full px-4 py-2.5 border border-gray-700 rounded-xl bg-gray-900/50 text-white text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 transition-shadow"
                    placeholder="e.g. 9876543210 or +91..."
                  />
                </div>

                <div className="flex items-start gap-3 bg-teal-950/20 border border-teal-500/20 p-3.5 rounded-xl">
                  <input 
                    type="checkbox" 
                    id="consent-check" 
                    checked={consent}
                    onChange={e => setConsent(e.target.checked)}
                    className="mt-0.5 text-teal-600 bg-gray-900 border-gray-700 rounded focus:ring-teal-500 focus:ring-offset-gray-900 cursor-pointer h-4 w-4"
                  />
                  <label htmlFor="consent-check" className="text-xs text-teal-200/90 leading-relaxed cursor-pointer select-none">
                    Patient consents to receiving their clinical summary and prescription details via WhatsApp.
                  </label>
                </div>

                {error && (
                  <div className="text-xs text-red-400 bg-red-950/20 border border-red-500/20 p-3 rounded-xl">
                    {error}
                  </div>
                )}

                <div className="flex justify-end gap-3 pt-2">
                  <button 
                    type="button" 
                    onClick={resetAndClose}
                    className="px-4 py-2 text-xs font-semibold text-gray-400 hover:text-white transition-colors cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit"
                    disabled={loading || !phone.trim() || !consent}
                    className="px-5 py-2 text-xs font-semibold text-white bg-gradient-to-r from-teal-600 to-emerald-600 rounded-lg hover:from-teal-500 hover:to-emerald-500 transition-colors shadow-lg disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer flex items-center gap-2"
                  >
                    {loading ? 'Sending...' : 'Send Prescription'}
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                  </button>
                </div>
              </form>
            )}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
