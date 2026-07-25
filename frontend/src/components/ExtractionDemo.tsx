import { useState } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { Play, Loader2, ThermometerSun, Pill, ShieldAlert, Stethoscope, FlaskConical, CalendarClock, Sparkles } from 'lucide-react';
import { runExtractionDemo, type ExtractionDemoResult } from '../lib/api';

const EXAMPLES = [
  {
    label: 'Fever with allergy',
    text: '3 din se bukhar hai, 101 F tak gaya, khansi nahi hai. BP 150/95. Paracetamol 500mg twice daily khane ke baad. Allergy to penicillin hai.',
  },
  {
    label: 'Joint pain, new order',
    text: 'Patient ghutno mein 2 hafte se dard bata rahi hai, subah zyada hota hai. Weight 68 kg. CBC aur ESR karwao. Diclofenac 50mg BD start karo.',
  },
  {
    label: 'Diabetes follow-up',
    text: 'Purana metformin 500mg continue karo, ab glimepiride 1mg subah bhi add karo. Koi ulti nahi, koi chakkar nahi. 2 hafte baad follow up.',
  },
];

const EMPTY: ExtractionDemoResult = {
  symptoms: [], medications: [], vitals: [], allergies: [],
  investigations: [], diagnoses: [], follow_up: [], contexts: {},
};

type CategoryKey = 'symptoms' | 'vitals' | 'medications' | 'allergies' | 'diagnoses' | 'investigations' | 'follow_up';

const CATEGORY_META: Record<CategoryKey, { label: string; icon: React.ElementType }> = {
  symptoms: { label: 'Symptoms', icon: Stethoscope },
  vitals: { label: 'Vitals', icon: ThermometerSun },
  medications: { label: 'Medications', icon: Pill },
  allergies: { label: 'Allergies', icon: ShieldAlert },
  diagnoses: { label: 'Diagnoses', icon: FlaskConical },
  investigations: { label: 'Investigations', icon: FlaskConical },
  follow_up: { label: 'Follow-up', icon: CalendarClock },
};

function medLabel(m: ExtractionDemoResult['medications'][number]): string {
  const parts = [m.name];
  if (m.dosage) parts.push(m.dosage);
  if (m.frequency) parts.push(m.frequency);
  return parts.join(' · ');
}

export default function ExtractionDemo() {
  const reduce = useReducedMotion();
  const [text, setText] = useState('');
  const [result, setResult] = useState<ExtractionDemoResult>(EMPTY);
  const [status, setStatus] = useState<'idle' | 'loading' | 'error' | 'done'>('idle');
  const [errorMsg, setErrorMsg] = useState('');

  async function run(input: string) {
    const trimmed = input.trim();
    if (!trimmed) return;
    setStatus('loading');
    setErrorMsg('');
    try {
      const r = await runExtractionDemo(trimmed);
      setResult(r);
      setStatus('done');
    } catch (err: unknown) {
      const message =
        (err as { response?: { status?: number } })?.response?.status === 429
          ? 'This demo is popular right now. Wait a moment and try again.'
          : 'Could not reach the extraction pipeline. Try again shortly.';
      setErrorMsg(message);
      setStatus('error');
    }
  }

  const categories: CategoryKey[] = ['symptoms', 'vitals', 'medications', 'allergies', 'diagnoses', 'investigations', 'follow_up'];
  const hasAnyResult = categories.some((c) => (result[c] as unknown[]).length > 0);

  return (
    <motion.section
      initial={reduce ? false : 'hidden'}
      whileInView="visible"
      viewport={{ once: true, amount: 0.15 }}
      variants={{ hidden: { opacity: 0, y: 24 }, visible: { opacity: 1, y: 0, transition: { duration: 0.55, ease: [0.16, 1, 0.3, 1] } } }}
      className="py-16 border-t border-slate-200/60"
    >
      <div className="mb-8 max-w-[60ch]">
        <h2 className="text-[1.9rem] md:text-[2.2rem] font-bold tracking-tight leading-[1.06] mb-3">
          Try the extraction pipeline yourself
        </h2>
        <p className="text-[15px] text-slate-500 leading-relaxed">
          This is the real deterministic engine running in production, not a mock. Type an OPD
          line in Hinglish, Hindi, or English, and watch it pull structured clinical facts,
          silently dropping anything negated, with no model guessing involved.
        </p>
      </div>

      <div className="rounded-3xl border border-slate-200/80 bg-white p-6 md:p-8">
        <div className="grid lg:grid-cols-[1fr_1.1fr] gap-8">
          {/* Input column */}
          <div className="flex flex-col">
            <label htmlFor="extract-demo-input" className="text-[12.5px] font-semibold text-text-dark mb-2">
              Doctor-patient line
            </label>
            <textarea
              id="extract-demo-input"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="e.g. 3 din se bukhar hai, khansi nahi hai. BP 150/95."
              rows={5}
              className="w-full rounded-2xl border border-slate-200 bg-slate-50/60 px-4 py-3 text-[14px] text-text-dark placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/40 resize-none transition-colors"
            />

            <div className="mt-3 flex flex-wrap gap-2">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex.label}
                  onClick={() => { setText(ex.text); run(ex.text); }}
                  className="text-[12px] font-medium text-primary bg-primary/[0.06] border border-primary/15 hover:bg-primary/[0.1] px-3 py-1.5 rounded-full transition-colors cursor-pointer"
                >
                  {ex.label}
                </button>
              ))}
            </div>

            <button
              onClick={() => run(text)}
              disabled={status === 'loading' || !text.trim()}
              className="mt-5 inline-flex items-center justify-center gap-2 bg-primary hover:bg-primary-dark disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold text-[13.5px] px-5 py-2.5 rounded-full transition-colors cursor-pointer w-fit"
            >
              {status === 'loading' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
              Run extraction
            </button>

            <p className="mt-4 text-[11.5px] text-slate-400 leading-relaxed">
              Runs against a public, rate-limited endpoint. No account, no session, nothing is
              stored. This is not a diagnostic tool and is not medical advice.
            </p>
          </div>

          {/* Output column */}
          <div className="rounded-2xl bg-slate-50/60 border border-slate-100 p-5 md:p-6 min-h-[280px]">
            {status === 'idle' && (
              <div className="h-full flex flex-col items-center justify-center text-center py-10 gap-3">
                <div className="w-10 h-10 rounded-2xl bg-primary/8 grid place-items-center">
                  <Sparkles className="w-5 h-5 text-primary" strokeWidth={1.8} />
                </div>
                <p className="text-[13.5px] text-slate-500 max-w-[32ch]">
                  Pick an example or type your own line, then run extraction to see structured facts appear here.
                </p>
              </div>
            )}

            {status === 'loading' && (
              <div className="space-y-3 animate-pulse">
                {[0, 1, 2].map((i) => (
                  <div key={i} className="h-9 rounded-xl bg-slate-200/70" style={{ width: `${70 - i * 12}%` }} />
                ))}
              </div>
            )}

            {status === 'error' && (
              <div className="h-full flex items-center justify-center py-10">
                <p className="text-[13.5px] text-red-500 text-center max-w-[32ch]">{errorMsg}</p>
              </div>
            )}

            {status === 'done' && !hasAnyResult && (
              <div className="h-full flex items-center justify-center py-10">
                <p className="text-[13.5px] text-slate-500 text-center max-w-[32ch]">
                  No structured facts found in that line. Negated or uncertain mentions
                  ("nahi", "shayad") are dropped on purpose, try a more explicit line.
                </p>
              </div>
            )}

            {status === 'done' && hasAnyResult && (
              <AnimatePresence mode="wait">
                <motion.div
                  key={JSON.stringify(result)}
                  initial={reduce ? false : { opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-4"
                >
                  {categories.map((cat) => {
                    const items = result[cat] as unknown[];
                    if (!items.length) return null;
                    const meta = CATEGORY_META[cat];
                    const Icon = meta.icon;
                    return (
                      <div key={cat}>
                        <div className="flex items-center gap-1.5 mb-2">
                          <Icon className="w-3.5 h-3.5 text-primary/70" strokeWidth={2} />
                          <span className="text-[10.5px] font-bold uppercase tracking-wider text-slate-400">{meta.label}</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {cat === 'medications'
                            ? (result.medications).map((m, i) => (
                                <span key={i} className="text-[12.5px] font-medium text-text-dark bg-white border border-slate-200 px-2.5 py-1 rounded-lg">
                                  {medLabel(m)}
                                  {m.status && <span className="text-slate-400 font-normal"> · {m.status}</span>}
                                </span>
                              ))
                            : (items as string[]).map((item, i) => (
                                <span key={i} className="text-[12.5px] font-medium text-text-dark bg-white border border-slate-200 px-2.5 py-1 rounded-lg">
                                  {item}
                                </span>
                              ))}
                        </div>
                      </div>
                    );
                  })}
                </motion.div>
              </AnimatePresence>
            )}
          </div>
        </div>
      </div>
    </motion.section>
  );
}
