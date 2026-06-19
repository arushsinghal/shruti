import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export default function SupportModal({ isOpen, onClose }: Props) {
  const [subject, setSubject] = useState('');
  const [query, setQuery] = useState('');

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    const mailto = `mailto:arushsinghal98@gmail.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(query)}`;
    window.location.href = mailto;
    setSubject('');
    setQuery('');
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
            onClick={onClose}
            className="absolute inset-0 bg-[#000000] bg-opacity-70 backdrop-blur-sm"
          />
          
          {/* Modal Content */}
          <motion.div 
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.2 }}
            className="relative w-full max-w-lg bg-[#111827] rounded-2xl shadow-2xl overflow-hidden border border-white/10"
          >
            <div className="px-6 py-4 border-b border-white/10 flex justify-between items-center bg-[#1F2937]/50">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
                Help & Support
              </h3>
              <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors cursor-pointer">
                ✕
              </button>
            </div>
            <form onSubmit={handleSend} className="p-6 space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Subject</label>
                <input 
                  type="text" 
                  required 
                  value={subject} 
                  onChange={e => setSubject(e.target.value)}
                  className="w-full px-4 py-2.5 border border-gray-700 rounded-xl bg-gray-900/50 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-shadow"
                  placeholder="e.g. Issue with generating SOAP note"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Describe your query / issue</label>
                <textarea 
                  required 
                  rows={4}
                  value={query} 
                  onChange={e => setQuery(e.target.value)}
                  className="w-full px-4 py-2.5 border border-gray-700 rounded-xl bg-gray-900/50 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-shadow resize-none"
                  placeholder="Please describe what you need help with..."
                />
              </div>
              <div className="pt-2 flex justify-end gap-3">
                <button 
                  type="button" 
                  onClick={onClose}
                  className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  className="px-6 py-2 text-sm font-medium text-white bg-gradient-to-r from-indigo-600 to-cyan-600 rounded-lg hover:from-indigo-500 hover:to-cyan-500 transition-colors shadow-lg shadow-indigo-500/25 cursor-pointer flex items-center gap-2"
                >
                  Send Message
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
