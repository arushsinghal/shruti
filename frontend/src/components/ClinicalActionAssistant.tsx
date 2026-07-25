import { useEffect, useRef, useState } from 'react';
import { Sparkles, Send, Loader2 } from 'lucide-react';
import api from '../lib/api';
import type { GatedAction } from '../pages/ReviewNote';

// Session-scoped command router — distinct from the public-site ChatWidget.
// It never drafts clinical content: it only classifies which of four
// existing, confirmation-gated document actions the doctor means (possibly
// more than one per message), via POST /sessions/{id}/assistant, then
// triggers the same handlers the equivalent UI buttons already use.
// Referral/TPA claim still open their modal for the doctor to review before
// downloading — this widens the interface, not the safety gate. Recent
// conversation history is sent with every message so references like
// "do that for him too" resolve against an earlier turn.

interface Turn {
  role: 'user' | 'assistant';
  text: string;
}

const HELP_TEXT = 'I can generate a prescription, investigation order, referral letter, or insurance claim, or answer a question about this patient\'s recorded history. Try: "generate the insurance claim", "refer to Dr. Sharma in cardiology", or "has this patient\'s allergy status changed?"';

interface ClinicalActionAssistantProps {
  sessionId: string;
  onPrescription: () => void;
  onInvestigationOrder: () => void;
  onGatedActions: (items: GatedAction[]) => void;
}

export default function ClinicalActionAssistant({
  sessionId,
  onPrescription,
  onInvestigationOrder,
  onGatedActions,
}: ClinicalActionAssistantProps) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Turn[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, loading]);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;
    const historyBeforeThisMessage = messages;
    setMessages((prev) => [...prev, { role: 'user', text: trimmed }]);
    setInput('');
    setLoading(true);
    try {
      const resp = await api.post(`/sessions/${sessionId}/assistant`, {
        message: trimmed,
        // Recent turns only — lets the model resolve "do that for him too"
        // against an earlier message without replaying the whole thread.
        history: historyBeforeThisMessage.slice(-10).map((m) => ({ role: m.role, text: m.text })),
      });
      const { actions, clarifying_question } = resp.data as {
        actions: Array<{
          action: string;
          to_doctor: string;
          to_specialty: string;
          reason: string;
          urgency: string;
          policy_number: string;
          insurer_name: string;
          tpa_name: string;
          query_type: string;
          answer: string;
        }>;
        clarifying_question: string;
      };

      if (actions.length === 0) {
        setMessages((prev) => [...prev, { role: 'assistant', text: clarifying_question || HELP_TEXT }]);
        return;
      }

      const gated: GatedAction[] = [];
      const replies: string[] = [];
      for (const item of actions) {
        switch (item.action) {
          case 'prescription':
            replies.push('Opening the prescription.');
            onPrescription();
            break;
          case 'investigation_order':
            replies.push('Opening the investigation order.');
            onInvestigationOrder();
            break;
          case 'referral':
            replies.push('Queued the referral letter with what you told me — review and confirm before downloading.');
            gated.push({
              type: 'referral',
              trigger: {
                toDoctor: item.to_doctor,
                specialty: item.to_specialty,
                reason: item.reason,
                urgency: item.urgency === 'urgent' ? 'urgent' : 'routine',
              },
            });
            break;
          case 'tpa_claim':
            replies.push('Queued the insurance claim form with what you told me — review and confirm before downloading.');
            gated.push({
              type: 'tpa_claim',
              trigger: {
                policyNumber: item.policy_number,
                insurerName: item.insurer_name,
                tpaName: item.tpa_name,
              },
            });
            break;
          case 'patient_info':
            // Pure read — answers from already-confirmed history, never
            // opens a modal or generates a document.
            replies.push(item.answer || "I couldn't find an answer to that in this patient's recorded history.");
            break;
        }
      }
      if (gated.length > 0) onGatedActions(gated);
      setMessages((prev) => [...prev, { role: 'assistant', text: replies.join(' ') || HELP_TEXT }]);
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', text: 'Could not reach the assistant. Try again in a moment.' }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mt-3 border border-slate-200 rounded-lg bg-white overflow-hidden print:hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2 px-3 py-2.5 text-left cursor-pointer hover:bg-slate-50 transition-colors"
      >
        <span className="grid h-6 w-6 place-items-center rounded-lg bg-primary/10 shrink-0">
          <Sparkles className="w-3.5 h-3.5 text-primary" strokeWidth={1.8} />
        </span>
        <span className="text-[12px] font-semibold text-slate-700 flex-1">Ask the assistant</span>
        <span className="text-slate-400 text-[10px]">{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div className="border-t border-slate-100">
          <div ref={scrollRef} className="max-h-52 overflow-y-auto px-3 py-2.5 space-y-2">
            {messages.length === 0 && (
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Try: "generate the insurance claim", "refer this patient to Dr. Sharma, cardiology, urgent," or "what allergies does this patient have?"
              </p>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] rounded-xl px-2.5 py-1.5 text-[11.5px] leading-snug ${
                    m.role === 'user'
                      ? 'bg-primary text-white'
                      : 'bg-slate-50 border border-slate-200 text-slate-700'
                  }`}
                >
                  {m.text}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="rounded-xl bg-slate-50 border border-slate-200 px-2.5 py-1.5">
                  <Loader2 className="w-3 h-3 text-slate-400 animate-spin" />
                </div>
              </div>
            )}
          </div>
          <form
            onSubmit={(e) => { e.preventDefault(); send(input); }}
            className="flex items-center gap-1.5 border-t border-slate-100 p-2"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="e.g. fill the insurance form"
              className="flex-1 min-w-0 rounded-full border border-slate-200 bg-slate-50/60 px-3 py-1.5 text-[11.5px] text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/25"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="shrink-0 grid h-7 w-7 place-items-center rounded-full bg-primary hover:bg-primary-dark disabled:opacity-40 text-white cursor-pointer transition-colors"
              aria-label="Send"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
