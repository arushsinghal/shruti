import { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, X, Send, FileText } from 'lucide-react';
import client from '../lib/api';

/**
 * Persistent per-doctor clinical memory assistant. Phase 1 (context-stuffing,
 * single-patient scope) per docs/obsidian/27_CLINICAL_MEMORY_ASSISTANT_SPEC.md.
 * Retrieval only — never writes anything. Every answer carries citations back
 * to the specific visits it drew from.
 */

type Citation = { session_id: string; visit_date: string };
type Message = { role: 'user' | 'assistant'; text: string; citations?: Citation[] };

function patientNameFromPath(pathname: string): string {
  const match = pathname.match(/^\/(?:patient|timeline)\/([^/]+)/);
  return match ? decodeURIComponent(match[1]) : '';
}

export default function ClinicalMemoryAssistant() {
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [patientName, setPatientName] = useState('');
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const threadRef = useRef<HTMLDivElement>(null);

  // Pick up patient context from the URL when navigating between patient pages.
  useEffect(() => {
    const fromPath = patientNameFromPath(location.pathname);
    if (fromPath) setPatientName(fromPath);
  }, [location.pathname]);

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, loading]);

  async function handleAsk() {
    if (!question.trim() || !patientName.trim() || loading) return;
    const q = question.trim();
    setMessages(m => [...m, { role: 'user', text: q }]);
    setQuestion('');
    setLoading(true);
    setError(null);
    try {
      const res = await client.post('/assistant/query', { question: q, patient_name: patientName });
      setMessages(m => [...m, { role: 'assistant', text: res.data.answer, citations: res.data.citations }]);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'The assistant is unavailable right now.';
      setError(detail);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {/* Collapsed trigger */}
      <AnimatePresence>
        {!open && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setOpen(true)}
            className="fixed bottom-6 right-6 z-[200] grid place-items-center w-14 h-14 rounded-full bg-primary text-white shadow-[0_12px_32px_-8px_rgba(27,94,59,0.5)] cursor-pointer"
            aria-label="Open clinical memory assistant"
          >
            <Sparkles className="w-5 h-5" strokeWidth={1.8} />
          </motion.button>
        )}
      </AnimatePresence>

      {/* Expanded panel */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 24, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 24, scale: 0.97 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            className="fixed bottom-6 right-6 z-[200] w-[380px] max-w-[calc(100vw-3rem)] h-[520px] max-h-[calc(100vh-6rem)] rounded-3xl border border-slate-200/80 bg-white shadow-[0_40px_90px_-40px_rgba(27,94,59,0.35)] flex flex-col overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-100 bg-white/95">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary" strokeWidth={1.8} />
                <span className="text-[13px] font-semibold text-text-dark">Clinical memory</span>
              </div>
              <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer" aria-label="Close">
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Patient context strip */}
            <div className="px-5 py-2.5 border-b border-slate-100 bg-[#FCFDFC]">
              <input
                value={patientName}
                onChange={e => setPatientName(e.target.value)}
                placeholder="Patient name"
                className="w-full text-[13px] font-medium text-text-dark bg-transparent outline-none placeholder:text-slate-400 placeholder:font-normal"
              />
            </div>

            {/* Thread */}
            <div ref={threadRef} className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
              {messages.length === 0 && (
                <p className="text-[13px] text-slate-400 leading-relaxed">
                  Ask about a past case, or a patient's history. Every answer traces back to the actual visit.
                </p>
              )}
              {messages.map((m, i) => (
                <div key={i} className={m.role === 'user' ? 'text-right' : ''}>
                  <div
                    className={`inline-block max-w-[90%] text-left rounded-2xl px-3.5 py-2.5 text-[13px] leading-relaxed ${
                      m.role === 'user' ? 'bg-primary text-white' : 'bg-slate-50 text-text-dark border border-slate-100'
                    }`}
                  >
                    {m.text}
                  </div>
                  {m.citations && m.citations.length > 0 && (
                    <div className="mt-1.5 flex flex-wrap gap-1.5">
                      {m.citations.map(c => (
                        <span
                          key={c.session_id}
                          className="inline-flex items-center gap-1 text-[10.5px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full"
                        >
                          <FileText className="w-2.5 h-2.5" /> {c.visit_date}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {loading && (
                <div className="flex items-center gap-1.5 text-[12px] text-slate-400">
                  {[0, 1, 2].map(i => (
                    <motion.span
                      key={i}
                      className="w-1.5 h-1.5 rounded-full bg-slate-300"
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 1.1, repeat: Infinity, delay: i * 0.18 }}
                    />
                  ))}
                </div>
              )}
              {error && <p className="text-[12px] text-red-500">{error}</p>}
            </div>

            {/* Input */}
            <div className="px-4 py-3 border-t border-slate-100 flex items-center gap-2">
              <input
                value={question}
                onChange={e => setQuestion(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleAsk()}
                placeholder="How did I treat this before?"
                className="flex-1 text-[13px] bg-slate-50 border border-slate-200 rounded-full px-4 py-2 outline-none focus:border-primary/40 transition-colors"
              />
              <button
                onClick={handleAsk}
                disabled={!question.trim() || !patientName.trim() || loading}
                className="grid place-items-center w-9 h-9 rounded-full bg-primary text-white disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer transition-opacity flex-shrink-0"
                aria-label="Ask"
              >
                <Send className="w-3.5 h-3.5" strokeWidth={2} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
