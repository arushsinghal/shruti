import { useEffect, useState } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { Mic, ShieldCheck, ArrowRight, Sparkles, FlaskConical, MessageSquare, Database } from 'lucide-react';

/**
 * Light, premium hero showcase of the Lipi flow:
 * spoken consultation → evidence-backed facts → every downstream record filed.
 * Deliberately cycles past the SOAP note into investigation order, patient
 * follow-up, and the ABDM record so the hero never reads as "just notes."
 * Auto-loops; settles to the final state under reduced-motion.
 */

const TRANSCRIPT = 'Patient ko teen din se bukhar hai, 102 ke around. Khaansi bhi hai. Chest pain nahi hai. BP 128 by 82.';

type Fact = { label: string; value: string; tone: 'primary' | 'slate' | 'accent'; evidence: string };

const FACTS: Fact[] = [
  { label: 'Symptom', value: 'Fever · 3 days', tone: 'primary', evidence: 'teen din se bukhar' },
  { label: 'Vital', value: 'Temp 102°F', tone: 'slate', evidence: '102 ke around' },
  { label: 'Symptom', value: 'Cough', tone: 'primary', evidence: 'khaansi bhi hai' },
  { label: 'Medication', value: 'Paracetamol 500mg', tone: 'accent', evidence: 'suggested' },
];

type OutputState = { icon: typeof ShieldCheck; label: string };

const OUTPUTS: OutputState[] = [
  { icon: ShieldCheck, label: 'Record ready · awaiting doctor sign-off' },
  { icon: FlaskConical, label: 'Investigation order dispatched to lab' },
  { icon: MessageSquare, label: 'Follow-up sent to patient on WhatsApp' },
  { icon: Database, label: 'ABHA-linked record filed with ABDM' },
];

const OUTPUT_DWELL_MS = 1500;

const TONE: Record<Fact['tone'], string> = {
  primary: 'bg-primary/8 text-primary-dark border-primary/15',
  slate: 'bg-slate-50 text-slate-700 border-slate-200',
  accent: 'bg-accent/10 text-accent-dark border-accent/20',
};
const DOT: Record<Fact['tone'], string> = {
  primary: 'bg-primary',
  slate: 'bg-slate-400',
  accent: 'bg-accent',
};

export function ProductShowcase() {
  const reduce = useReducedMotion();
  const [typed, setTyped] = useState(reduce ? TRANSCRIPT : '');
  const [revealed, setRevealed] = useState(reduce ? FACTS.length : 0);
  const [done, setDone] = useState(reduce ? true : false);
  const [outputIdx, setOutputIdx] = useState(reduce ? OUTPUTS.length - 1 : 0);

  // Auto-play loop: type transcript → reveal facts → cycle every downstream
  // output (record, lab order, WhatsApp follow-up, ABDM filing) → reset.
  useEffect(() => {
    if (reduce) return;
    let timers: ReturnType<typeof setTimeout>[] = [];
    let typeInt: ReturnType<typeof setInterval>;
    let outputInt: ReturnType<typeof setInterval>;

    const run = () => {
      setTyped('');
      setRevealed(0);
      setDone(false);
      setOutputIdx(0);
      let i = 0;
      typeInt = setInterval(() => {
        i++;
        setTyped(TRANSCRIPT.slice(0, i));
        if (i >= TRANSCRIPT.length) {
          clearInterval(typeInt);
          FACTS.forEach((_, idx) => {
            timers.push(setTimeout(() => setRevealed(idx + 1), 350 + idx * 480));
          });
          timers.push(setTimeout(() => {
            setDone(true);
            let o = 0;
            outputInt = setInterval(() => {
              o++;
              if (o >= OUTPUTS.length) {
                clearInterval(outputInt);
                return;
              }
              setOutputIdx(o);
            }, OUTPUT_DWELL_MS);
          }, 350 + FACTS.length * 480 + 300));
        }
      }, 34);
    };

    const cycleMs = 350 + FACTS.length * 480 + 300 + TRANSCRIPT.length * 34 + OUTPUTS.length * OUTPUT_DWELL_MS + 900;

    run();
    const loop = setInterval(() => {
      timers.forEach(clearTimeout);
      timers = [];
      clearInterval(outputInt);
      run();
    }, cycleMs);

    return () => {
      clearInterval(loop);
      clearInterval(typeInt);
      clearInterval(outputInt);
      timers.forEach(clearTimeout);
    };
  }, [reduce]);

  return (
    <div className="relative">
      {/* ambient glow */}
      <div className="absolute -inset-6 -z-10 rounded-[2.5rem] bg-gradient-to-tr from-primary/10 via-accent/5 to-primary/10 blur-2xl" />

      <div className="rounded-[1.75rem] border border-slate-200/80 bg-white shadow-[0_40px_90px_-40px_rgba(27,94,59,0.35)] overflow-hidden">
        {/* App chrome header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-100 bg-white/90">
          <div className="flex items-center gap-2.5">
            <span className="grid place-items-center w-7 h-7 rounded-lg bg-primary/10 text-primary font-bold text-xs">श</span>
            <span className="text-[13px] font-semibold text-text-dark">Live consultation</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 bg-slate-100 px-2 py-0.5 rounded-md">Hinglish</span>
            <span className="flex items-center gap-1.5 text-[11px] font-semibold text-primary bg-primary/8 px-2 py-0.5 rounded-md">
              <span className={`w-1.5 h-1.5 rounded-full bg-primary ${reduce ? '' : 'animate-pulse'}`} />
              Recording
            </span>
          </div>
        </div>

        <div className="grid md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-100">
          {/* Left: voice + transcript */}
          <div className="p-5 md:p-6">
            <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-4">
              <Mic className="w-3.5 h-3.5" /> Speech
            </div>

            {/* waveform */}
            <div className="flex items-end gap-1 h-12 mb-5">
              {Array.from({ length: 36 }).map((_, i) => (
                <motion.span
                  key={i}
                  className="flex-1 rounded-full bg-primary/30"
                  animate={reduce ? { height: 8 } : { height: [6, 8 + ((i * 7) % 30), 6] }}
                  transition={reduce ? {} : { duration: 0.9 + (i % 5) * 0.12, repeat: Infinity, ease: 'easeInOut', delay: (i % 7) * 0.05 }}
                  style={{ height: 8 }}
                />
              ))}
            </div>

            <div className="rounded-2xl bg-slate-50 border border-slate-100 p-4 min-h-[112px]">
              <p className="text-[14px] leading-relaxed text-slate-700">
                {typed}
                {!done && !reduce && <span className="inline-block w-[2px] h-[15px] bg-primary align-middle ml-0.5 animate-pulse" />}
              </p>
            </div>
          </div>

          {/* Right: extracted facts */}
          <div className="p-5 md:p-6 bg-[#FCFDFC]">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider text-primary">
                <Sparkles className="w-3.5 h-3.5" /> Evidence-backed facts
              </div>
              <span className="text-[10px] font-semibold text-slate-400 tabular-nums">{revealed}/{FACTS.length}</span>
            </div>

            <div className="space-y-2 min-h-[156px]">
              <AnimatePresence>
                {FACTS.slice(0, revealed).map((f) => (
                  <motion.div
                    key={f.value}
                    initial={reduce ? false : { opacity: 0, y: 8, scale: 0.97 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ duration: 0.32, ease: [0.16, 1, 0.3, 1] }}
                    className={`flex items-center gap-2.5 rounded-xl border px-3 py-2 ${TONE[f.tone]}`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${DOT[f.tone]}`} />
                    <div className="min-w-0 flex-1">
                      <span className="text-[10px] font-bold uppercase tracking-wider opacity-60">{f.label}</span>
                      <p className="text-[13px] font-semibold leading-tight">{f.value}</p>
                    </div>
                    <span className="text-[10px] text-slate-400 italic truncate max-w-[40%] hidden sm:block">"{f.evidence}"</span>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>
        </div>

        {/* Footer: cycles through every downstream output, not just the note */}
        <div className="px-5 py-3.5 border-t border-slate-100">
          <AnimatePresence mode="wait">
            {done ? (
              <motion.div
                key={`output-${outputIdx}`}
                initial={reduce ? false : { opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.28 }}
                className="flex items-center justify-between"
              >
                <span className="flex items-center gap-2 text-[13px] font-semibold text-primary">
                  {(() => {
                    const Icon = OUTPUTS[outputIdx].icon;
                    return <Icon className="w-4 h-4" />;
                  })()}
                  {OUTPUTS[outputIdx].label}
                </span>
                {outputIdx === 0 && (
                  <span className="hidden sm:flex items-center gap-1.5 text-[12px] font-semibold text-slate-400">
                    Review <ArrowRight className="w-3.5 h-3.5" />
                  </span>
                )}
              </motion.div>
            ) : (
              <motion.div key="working" className="flex items-center gap-2 text-[13px] font-medium text-slate-400">
                <span className="flex gap-1">
                  {[0, 1, 2].map(i => (
                    <motion.span
                      key={i}
                      className="w-1.5 h-1.5 rounded-full bg-slate-300"
                      animate={reduce ? {} : { opacity: [0.3, 1, 0.3] }}
                      transition={reduce ? {} : { duration: 1.1, repeat: Infinity, delay: i * 0.18 }}
                    />
                  ))}
                </span>
                Structuring consultation…
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
