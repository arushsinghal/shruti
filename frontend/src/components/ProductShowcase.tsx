import { useRef, type PointerEvent as ReactPointerEvent } from 'react';
import {
  motion,
  useMotionValue,
  useReducedMotion,
  useScroll,
  useSpring,
  useTransform,
} from 'framer-motion';
import {
  ArrowRight,
  BadgeCheck,
  BellPlus,
  ClipboardCheck,
  Database,
  FileText,
  FlaskConical,
  MessageSquareText,
  Mic2,
  Pill,
  SearchCheck,
  ShieldCheck,
  type LucideIcon,
} from 'lucide-react';

const SPRING = { stiffness: 150, damping: 24, mass: 0.5 };

type FactTone = 'primary' | 'slate' | 'accent' | 'rose';

type Fact = {
  label: string;
  value: string;
  evidence: string;
  tone: FactTone;
};

type Output = {
  icon: LucideIcon;
  label: string;
  detail: string;
};

const TRANSCRIPT_LINES = [
  { speaker: 'Dr', text: 'Teen din se bukhar hai, 102 ke around.' },
  { speaker: 'Pt', text: 'Khaansi bhi hai, chest pain nahi.' },
  { speaker: 'Dr', text: 'BP 128/82. Paracetamol 500mg likh do.' },
];

const FACTS: Fact[] = [
  { label: 'Symptom', value: 'Fever · 3 days', evidence: 'teen din se bukhar', tone: 'primary' },
  { label: 'Vital', value: 'Temp 102°F', evidence: '102 ke around', tone: 'slate' },
  { label: 'Negated', value: 'Chest pain', evidence: 'nahi', tone: 'rose' },
  { label: 'Medication', value: 'Paracetamol 500mg', evidence: 'likh do', tone: 'accent' },
];

const OUTPUTS: Output[] = [
  { icon: FileText, label: 'SOAP note', detail: 'Ready for review' },
  { icon: Pill, label: 'Prescription', detail: 'Drafted, unsigned' },
  { icon: FlaskConical, label: 'Lab order', detail: 'Assistant queued' },
  { icon: Database, label: 'ABDM record', detail: 'ABHA-linked bundle' },
];

const ASSISTANT_TASKS = [
  'Send prescription on WhatsApp',
  'Queue lab sample pickup',
  'Schedule fever review',
];

const ASSISTANT_QUERY = 'How many fever patients this week?';
const ASSISTANT_REPLY = '3 fever visits found.';
const ASSISTANT_CITATIONS = [
  'Jul 01 · fever 3 days',
  'Jul 02 · temp 102°F',
  'Jul 03 · fever + cough',
];

const FACT_TONE: Record<FactTone, string> = {
  primary: 'border-primary/18 bg-primary/[0.055] text-primary-dark',
  slate: 'border-slate-200 bg-slate-50 text-slate-700',
  accent: 'border-accent/24 bg-accent/[0.09] text-accent-dark',
  rose: 'border-rose-100 bg-rose-50 text-rose-700',
};

const DOT_TONE: Record<FactTone, string> = {
  primary: 'bg-primary',
  slate: 'bg-slate-400',
  accent: 'bg-accent',
  rose: 'bg-rose-500',
};

function FactPill({ fact, reduce }: { fact: Fact; reduce: boolean }) {
  return (
    <motion.div
      whileHover={reduce ? undefined : { y: -2, transition: { duration: 0.18 } }}
      className={`rounded-xl border px-2.5 py-2 shadow-[0_10px_30px_-24px_rgba(18,63,39,0.45)] ${FACT_TONE[fact.tone]}`}
    >
      <div className="flex items-center gap-2">
        <span className={`h-1.5 w-1.5 rounded-full ${DOT_TONE[fact.tone]}`} />
        <span className="text-[9px] font-bold uppercase tracking-[0.15em] opacity-60">{fact.label}</span>
      </div>
      <p className={`mt-1 text-[12px] font-bold leading-tight ${fact.tone === 'rose' ? 'line-through decoration-rose-500/55' : ''}`}>
        {fact.value}
      </p>
      <p className="mt-0.5 truncate text-[9.5px] font-medium text-slate-400">"{fact.evidence}"</p>
    </motion.div>
  );
}

function TypedText({ text, reduce, delay = 0 }: { text: string; reduce: boolean; delay?: number }) {
  if (reduce) return <>{text}</>;

  return (
    <>
      {text.split('').map((char, index) => (
        <motion.span
          key={`${char}-${index}`}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.01, delay: delay + index * 0.025 }}
        >
          {char}
        </motion.span>
      ))}
    </>
  );
}

function AssistantMemoryDemo({ reduce }: { reduce: boolean }) {
  return (
    <motion.div
      initial={reduce ? false : { opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.55, delay: 0.58, ease: [0.16, 1, 0.3, 1] as const }}
      className="mt-3 rounded-xl border border-primary/12 bg-white/88 p-2.5 shadow-[0_18px_46px_-38px_rgba(18,63,39,0.7)]"
    >
      <div className="mb-2 flex items-center justify-between">
        <span className="flex items-center gap-1.5 text-[9.5px] font-bold uppercase tracking-[0.17em] text-primary/70">
          <MessageSquareText className="h-3 w-3" strokeWidth={1.9} />
          Ask Lipi
        </span>
        <span className="rounded-full bg-primary/[0.055] px-2 py-0.5 text-[9.5px] font-bold text-primary">clinic memory, cited</span>
      </div>

      <div className="grid grid-cols-[1fr_1.02fr] gap-2">
        <div className="rounded-lg bg-primary px-2.5 py-2 text-[10.5px] font-semibold leading-snug text-white shadow-sm">
          <TypedText text={ASSISTANT_QUERY} reduce={reduce} delay={0.75} />
        </div>

        <motion.div
          initial={reduce ? false : { opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.42, delay: 1.65, ease: [0.16, 1, 0.3, 1] as const }}
          className="rounded-lg border border-slate-100 bg-bg-warm/80 px-2.5 py-2"
        >
          <div className="mb-1.5 flex items-center gap-1 text-[10.5px] font-bold text-primary-dark">
            <SearchCheck className="h-3 w-3 text-primary" strokeWidth={2} />
            <TypedText text={ASSISTANT_REPLY} reduce={reduce} delay={1.85} />
          </div>
          <div className="grid gap-1">
            {ASSISTANT_CITATIONS.map((citation, index) => (
              <motion.span
                key={citation}
                initial={reduce ? false : { opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.28, delay: 2.35 + index * 0.12, ease: [0.16, 1, 0.3, 1] as const }}
                className="truncate rounded-md border border-primary/12 bg-white px-1.5 py-0.5 text-[8.5px] font-semibold text-slate-500"
              >
                {citation}
              </motion.span>
            ))}
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}

export function ProductShowcase() {
  const reduce = useReducedMotion();
  const shouldReduceMotion = Boolean(reduce);
  const rootRef = useRef<HTMLDivElement>(null);
  const pointerX = useMotionValue(0);
  const pointerY = useMotionValue(0);

  const { scrollYProgress } = useScroll({
    target: rootRef,
    offset: ['start end', 'end start'],
  });

  const rotateX = useSpring(useTransform(pointerY, [-0.5, 0.5], [7, -7]), SPRING);
  const rotateY = useSpring(useTransform(pointerX, [-0.5, 0.5], [-8, 8]), SPRING);
  const depthY = useSpring(useTransform(scrollYProgress, [0, 0.5, 1], [26, 0, -26]), SPRING);
  const rearLayerY = useSpring(useTransform(scrollYProgress, [0, 1], [18, -18]), SPRING);
  const frontLayerY = useSpring(useTransform(scrollYProgress, [0, 1], [-14, 22]), SPRING);

  const handlePointerMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (shouldReduceMotion) return;
    const rect = event.currentTarget.getBoundingClientRect();
    pointerX.set((event.clientX - rect.left) / rect.width - 0.5);
    pointerY.set((event.clientY - rect.top) / rect.height - 0.5);
  };

  const resetTilt = () => {
    pointerX.set(0);
    pointerY.set(0);
  };

  return (
    <div ref={rootRef} className="relative mx-auto w-full max-w-[720px] lg:max-w-none py-3 lg:py-4 [perspective:1600px]">
      <div className="pointer-events-none absolute -left-12 top-14 h-72 w-72 rounded-full bg-[radial-gradient(circle_at_center,rgba(27,94,59,0.16),rgba(27,94,59,0)_68%)] blur-xl" aria-hidden />
      <div className="pointer-events-none absolute bottom-2 right-0 h-64 w-64 rounded-full bg-[radial-gradient(circle_at_center,rgba(244,164,53,0.13),rgba(244,164,53,0)_70%)] blur-xl" aria-hidden />

      <motion.div
        style={shouldReduceMotion ? undefined : { y: rearLayerY }}
        className="pointer-events-none absolute right-2 top-0 hidden w-[46%] rounded-2xl border border-primary/12 bg-white/72 p-3 shadow-[0_28px_70px_-48px_rgba(18,63,39,0.55)] backdrop-blur-sm md:block"
        aria-hidden
      >
        <div className="mb-2 flex items-center justify-between">
          <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-primary/65">ABDM bundle</span>
          <Database className="h-4 w-4 text-primary/55" strokeWidth={1.8} />
        </div>
        <div className="space-y-1.5">
          {['PatientReference', 'Encounter', 'Observation', 'MedicationRequest'].map((item) => (
            <div key={item} className="flex items-center gap-2 rounded-lg border border-slate-100 bg-bg-warm/70 px-2.5 py-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-primary/55" />
              <span className="text-[11px] font-semibold text-slate-500">{item}</span>
            </div>
          ))}
        </div>
      </motion.div>

      <motion.div
        onPointerMove={handlePointerMove}
        onPointerLeave={resetTilt}
        style={shouldReduceMotion ? undefined : { y: depthY, rotateX, rotateY, transformStyle: 'preserve-3d' }}
        className="relative overflow-hidden rounded-[2rem] border border-slate-200/80 bg-white shadow-[0_34px_100px_-52px_rgba(18,63,39,0.72)] transition-shadow duration-200 hover:shadow-[0_40px_105px_-50px_rgba(18,63,39,0.8)]"
      >
        <div className="absolute inset-x-0 top-0 h-32 bg-[radial-gradient(ellipse_at_top,rgba(27,94,59,0.09),rgba(27,94,59,0)_72%)]" aria-hidden />

        <div className="relative flex items-center justify-between border-b border-slate-100 px-4 py-3 sm:px-5">
          <div className="flex items-center gap-2.5">
            <span className="grid h-8 w-8 place-items-center rounded-xl bg-primary text-sm font-bold text-white shadow-sm">श</span>
            <div>
              <p className="text-[13px] font-bold tracking-tight text-text-dark">Lipi assistant</p>
              <p className="text-[10.5px] font-semibold text-slate-400">Personal OPD desk for every consult</p>
            </div>
          </div>
          <div className="hidden items-center gap-2 sm:flex">
            <span className="rounded-full border border-primary/15 bg-primary/[0.055] px-2.5 py-1 text-[10.5px] font-bold uppercase tracking-[0.12em] text-primary">
              Hinglish
            </span>
            <span className="flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[10.5px] font-semibold text-slate-500">
              <ShieldCheck className="h-3.5 w-3.5 text-primary" strokeWidth={1.9} />
              Doctor review
            </span>
          </div>
        </div>

        <div className="relative grid gap-3 p-3.5 sm:p-4 lg:grid-cols-[0.92fr_1.08fr]">
          <div className="rounded-2xl border border-slate-200/80 bg-bg-warm/80 p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]">
            <div className="mb-3 flex items-center justify-between">
              <span className="flex items-center gap-2 text-[10.5px] font-bold uppercase tracking-[0.18em] text-slate-400">
                <Mic2 className="h-3.5 w-3.5" strokeWidth={1.9} />
                Speech
              </span>
              <span className="rounded-md bg-white px-2 py-1 text-[10px] font-bold text-primary shadow-sm">39:42</span>
            </div>

            <div className="mb-3 flex h-8 items-end gap-1">
              {[18, 30, 16, 34, 22, 38, 20, 28, 36, 18, 32, 24, 40, 22, 30, 16, 34, 20].map((height, index) => (
                <span
                  key={`${height}-${index}`}
                  className="flex-1 rounded-full bg-primary/25"
                  style={{ height }}
                />
              ))}
            </div>

            <div className="space-y-2">
              {TRANSCRIPT_LINES.map((line) => (
                <div key={line.text} className="rounded-xl border border-white bg-white/82 px-3 py-2 shadow-sm">
                  <div className="mb-1 flex items-center gap-2">
                    <span className={`rounded-md px-1.5 py-0.5 text-[9.5px] font-black uppercase tracking-[0.14em] ${line.speaker === 'Dr' ? 'bg-primary/8 text-primary' : 'bg-slate-100 text-slate-500'}`}>
                      {line.speaker}
                    </span>
                    <span className="h-px flex-1 bg-slate-100" />
                  </div>
                  <p className="text-[11.5px] font-medium leading-snug text-slate-600">{line.text}</p>
                </div>
              ))}
            </div>

            <AssistantMemoryDemo reduce={shouldReduceMotion} />
          </div>

          <div className="grid gap-3">
            <div className="rounded-2xl border border-primary/14 bg-white p-3.5 shadow-[0_16px_44px_-34px_rgba(18,63,39,0.68)]">
              <div className="mb-3 flex items-center justify-between">
                <span className="flex items-center gap-2 text-[10.5px] font-bold uppercase tracking-[0.18em] text-primary">
                  <ClipboardCheck className="h-3.5 w-3.5" strokeWidth={1.9} />
                  Assistant-ready facts
                </span>
                <span className="text-[10.5px] font-bold text-slate-400 tabular-nums">4 / 4 traced</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {FACTS.map((fact) => (
                  <FactPill key={fact.value} fact={fact} reduce={shouldReduceMotion} />
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200/90 bg-[#FCFDFC] p-3.5">
              <div className="mb-2.5 flex items-center gap-2 text-[10.5px] font-bold uppercase tracking-[0.18em] text-slate-400">
                <BadgeCheck className="h-3.5 w-3.5 text-primary" strokeWidth={1.9} />
                Review note
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                <div className="rounded-xl border border-slate-100 bg-white p-3">
                  <span className="text-[9px] font-bold uppercase tracking-[0.15em] text-slate-400">Assessment</span>
                  <p className="mt-1 text-[12px] font-bold leading-snug text-text-dark">Acute febrile illness</p>
                </div>
                <div className="rounded-xl border border-primary/14 bg-primary/[0.045] p-3">
                  <span className="text-[9px] font-bold uppercase tracking-[0.15em] text-primary/60">Assistant task</span>
                  <p className="mt-1 text-[12px] font-bold leading-snug text-primary-dark">Rx + follow-up queued</p>
                </div>
              </div>
              <div className="mt-2.5 flex items-center justify-between rounded-xl border border-primary/14 bg-white px-3 py-2">
                <span className="flex items-center gap-2 text-[12px] font-bold text-primary">
                  <ShieldCheck className="h-4 w-4" strokeWidth={2} />
                  doctor review required
                </span>
                <ArrowRight className="h-4 w-4 text-primary/55" strokeWidth={2} />
              </div>
            </div>
          </div>
        </div>

        <div className="relative border-t border-slate-100 bg-bg-warm/60 px-4 py-2.5 sm:px-5">
          <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
            {OUTPUTS.map((output) => {
              const Icon = output.icon;
              return (
                <motion.div
                  key={output.label}
                  whileHover={shouldReduceMotion ? undefined : { y: -2, transition: { duration: 0.18 } }}
                  className="rounded-xl border border-slate-200/80 bg-white px-2.5 py-2 shadow-[0_10px_28px_-24px_rgba(18,63,39,0.62)]"
                >
                  <div className="mb-1.5 flex items-center gap-2">
                    <Icon className="h-3.5 w-3.5 text-primary" strokeWidth={1.9} />
                    <span className="text-[10.5px] font-bold leading-none text-text-dark">{output.label}</span>
                  </div>
                  <p className="text-[9.5px] font-semibold leading-tight text-slate-400">{output.detail}</p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </motion.div>

      <motion.div
        style={shouldReduceMotion ? undefined : { y: frontLayerY }}
        className="pointer-events-none absolute -bottom-3 left-2 hidden w-[41%] rounded-2xl border border-slate-200/90 bg-white/86 p-3 shadow-[0_26px_72px_-44px_rgba(18,63,39,0.65)] backdrop-blur-sm xl:block"
        aria-hidden
      >
        <div className="mb-2 flex items-center justify-between">
          <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">Assistant queue</span>
          <BellPlus className="h-4 w-4 text-primary/65" strokeWidth={1.9} />
        </div>
        <div className="space-y-1.5">
          {ASSISTANT_TASKS.map((item) => (
            <div key={item} className="flex items-center gap-2 text-[10.5px] font-semibold text-slate-600">
              <BadgeCheck className="h-3.5 w-3.5 text-primary/70" strokeWidth={2} />
              {item}
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
