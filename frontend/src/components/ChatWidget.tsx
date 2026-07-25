import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { MessageCircle, X, Send, Loader2, Sparkles } from 'lucide-react';
import { sendLandingChatMessage, type LandingChatTurn } from '../lib/api';

const SUGGESTIONS = [
  'What does Lipi actually do?',
  'How does zero-hallucination work?',
  'What does Clinic Pro cost?',
];

export default function ChatWidget() {
  const reduce = useReducedMotion();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<LandingChatTurn[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, loading]);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;
    const nextMessages: LandingChatTurn[] = [...messages, { role: 'user', text: trimmed }];
    setMessages(nextMessages);
    setInput('');
    setLoading(true);
    try {
      const answer = await sendLandingChatMessage(trimmed, nextMessages);
      setMessages((prev) => [...prev, { role: 'assistant', text: answer }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: 'Something went wrong. Email arushsinghal98@gmail.com and the team will help directly.' },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed bottom-6 right-6 z-[200] flex flex-col items-end gap-3">
      <AnimatePresence>
        {open && (
          <motion.div
            initial={reduce ? false : { opacity: 0, y: 16, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.97 }}
            transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
            className="w-[min(92vw,380px)] h-[min(70vh,520px)] rounded-3xl border border-slate-200/80 bg-white shadow-[0_28px_80px_-24px_rgba(18,63,39,0.35)] flex flex-col overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center gap-2.5 border-b border-slate-100 bg-bg-warm px-4 py-3.5 shrink-0">
              <span className="grid h-8 w-8 place-items-center rounded-xl bg-primary text-white font-bold text-sm shadow-sm">श</span>
              <div className="min-w-0">
                <p className="text-[13px] font-bold text-text-dark">Ask about Lipi</p>
                <p className="text-[11px] text-slate-400">Product & research questions</p>
              </div>
              <button
                onClick={() => setOpen(false)}
                className="ml-auto grid h-7 w-7 place-items-center rounded-full text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors cursor-pointer"
                aria-label="Close chat"
              >
                <X className="w-4 h-4" strokeWidth={2} />
              </button>
            </div>

            {/* Messages */}
            <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
              {messages.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center text-center gap-3 px-2">
                  <div className="w-9 h-9 rounded-2xl bg-primary/8 grid place-items-center">
                    <Sparkles className="w-4.5 h-4.5 text-primary" strokeWidth={1.8} />
                  </div>
                  <p className="text-[12.5px] text-slate-500 max-w-[26ch]">
                    Ask about the product, the research, or pricing. Not for medical questions.
                  </p>
                  <div className="flex flex-col gap-1.5 w-full mt-1">
                    {SUGGESTIONS.map((s) => (
                      <button
                        key={s}
                        onClick={() => send(s)}
                        className="text-[12px] font-medium text-primary bg-primary/[0.05] border border-primary/15 hover:bg-primary/[0.09] rounded-xl px-3 py-2 text-left transition-colors cursor-pointer"
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {messages.map((m, i) => (
                <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-[13px] leading-relaxed ${
                      m.role === 'user'
                        ? 'rounded-br-md bg-primary text-white'
                        : 'rounded-bl-md bg-slate-50 border border-slate-200 text-text-dark'
                    }`}
                  >
                    {m.text}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="rounded-2xl rounded-bl-md bg-slate-50 border border-slate-200 px-3.5 py-2.5">
                    <Loader2 className="w-3.5 h-3.5 text-slate-400 animate-spin" />
                  </div>
                </div>
              )}
            </div>

            {/* Input */}
            <form
              onSubmit={(e) => { e.preventDefault(); send(input); }}
              className="flex items-center gap-2 border-t border-slate-100 p-3 shrink-0"
            >
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask a question..."
                className="flex-1 min-w-0 rounded-full border border-slate-200 bg-slate-50/60 px-4 py-2.5 text-[13px] text-text-dark placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/40 transition-colors"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="shrink-0 grid h-9 w-9 place-items-center rounded-full bg-primary hover:bg-primary-dark disabled:opacity-40 disabled:cursor-not-allowed text-white transition-colors cursor-pointer"
                aria-label="Send"
              >
                <Send className="w-4 h-4" strokeWidth={2} />
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        onClick={() => setOpen((v) => !v)}
        whileHover={reduce ? undefined : { scale: 1.05 }}
        whileTap={reduce ? undefined : { scale: 0.95 }}
        className="grid h-14 w-14 place-items-center rounded-full bg-primary hover:bg-primary-dark text-white shadow-[0_18px_42px_-16px_rgba(18,63,39,0.7)] transition-colors cursor-pointer"
        aria-label={open ? 'Close chat' : 'Open chat'}
      >
        <AnimatePresence mode="wait" initial={false}>
          <motion.span
            key={open ? 'close' : 'open'}
            initial={reduce ? false : { opacity: 0, rotate: -45 }}
            animate={{ opacity: 1, rotate: 0 }}
            exit={{ opacity: 0, rotate: 45 }}
            transition={{ duration: 0.18 }}
          >
            {open ? <X className="w-5.5 h-5.5" strokeWidth={2} /> : <MessageCircle className="w-5.5 h-5.5" strokeWidth={2} />}
          </motion.span>
        </AnimatePresence>
      </motion.button>
    </div>
  );
}
