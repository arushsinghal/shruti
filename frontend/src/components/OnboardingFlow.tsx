import { useState, useEffect } from 'react';
import { getClinicInviteCode } from '../lib/api';
import { useAuth } from '../context/AuthContext';

interface StepDef {
  icon: React.ReactNode;
  title: string;
  desc: string;
  isInviteStep?: boolean;
}

const BASE_STEPS: StepDef[] = [
  {
    icon: (
      <svg className="w-8 h-8 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
      </svg>
    ),
    title: 'Create a Session',
    desc: 'Click "+ New Session" and select Health mode for a doctor-patient consultation.',
  },
  {
    icon: (
      <svg className="w-8 h-8 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
      </svg>
    ),
    title: 'Record the Consultation',
    desc: 'Talk naturally with your patient — Hindi, English, or Hinglish. Stop when done.',
  },
  {
    icon: (
      <svg className="w-8 h-8 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    title: 'Review & Sign',
    desc: 'Lipi writes the full SOAP note in 3 seconds. Review, sign, and print the prescription.',
  },
  {
    icon: (
      <svg className="w-8 h-8 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
      </svg>
    ),
    title: 'Invite Your Assistant',
    desc: 'Share this code with your clinic assistant. They join once and see your queue automatically.',
    isInviteStep: true,
  },
];

const STORAGE_KEY = 'lipi_onboarding_done';

export default function OnboardingFlow() {
  const { user } = useAuth();
  const isDoctor = user?.role !== 'assistant';

  const [visible, setVisible] = useState(false);
  const [step, setStep] = useState(0);
  const [inviteCode, setInviteCode] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const STEPS = isDoctor ? BASE_STEPS : [];

  useEffect(() => {
    if (!localStorage.getItem(STORAGE_KEY) && isDoctor) {
      setVisible(true);
      getClinicInviteCode().then(r => setInviteCode(r.code)).catch(() => {});
    }
  }, [isDoctor]);

  function dismiss() {
    localStorage.setItem(STORAGE_KEY, '1');
    setVisible(false);
  }

  function handleCopy() {
    if (!inviteCode) return;
    navigator.clipboard.writeText(inviteCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (!visible || STEPS.length === 0) return null;

  const currentStep = STEPS[step];
  const isLastStep = step === STEPS.length - 1;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md border border-slate-100">
        {/* Header */}
        <div className="p-6 border-b border-slate-100 text-center">
          <div className="flex items-center justify-center gap-2 mb-1">
            <span className="font-bold text-primary text-2xl">श</span>
            <span className="text-lg font-bold text-text-dark tracking-tight">Lipi</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">AI Clinical Scribe — welcome to Lipi</p>
        </div>

        {/* Steps */}
        <div className="p-6">
          {/* Step indicators */}
          <div className="flex items-center justify-center gap-2 mb-6">
            {STEPS.map((_, i) => (
              <button
                key={i}
                onClick={() => setStep(i)}
                className={`h-1.5 rounded-full transition-all cursor-pointer ${
                  i === step ? 'w-6 bg-primary' : 'w-1.5 bg-slate-200'
                }`}
              />
            ))}
          </div>

          {/* Current step */}
          <div className="text-center space-y-3 min-h-[140px] flex flex-col items-center justify-center">
            <div className="w-14 h-14 bg-primary/10 rounded-2xl flex items-center justify-center">
              {currentStep.icon}
            </div>
            <div>
              <p className="font-bold text-slate-800 text-base">
                Step {step + 1}: {currentStep.title}
              </p>
              <p className="text-sm text-slate-500 mt-1 leading-relaxed">{currentStep.desc}</p>
            </div>

            {/* Invite code widget on step 4 */}
            {currentStep.isInviteStep && (
              <div className="w-full mt-1">
                {inviteCode ? (
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-4 py-2.5 font-mono text-[22px] font-bold tracking-[0.15em] text-text-dark text-center">
                      {inviteCode}
                    </div>
                    <button
                      onClick={handleCopy}
                      className="shrink-0 text-[12px] font-semibold text-white bg-primary hover:bg-primary-dark px-3 py-3 rounded-lg transition-all cursor-pointer"
                    >
                      {copied ? '✓' : 'Copy'}
                    </button>
                  </div>
                ) : (
                  <div className="h-12 bg-slate-100 rounded-lg animate-pulse" />
                )}
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="p-4 border-t border-slate-100 flex gap-3">
          <button
            onClick={dismiss}
            className="flex-1 px-4 py-2 text-sm text-slate-400 hover:text-slate-600 font-medium transition-colors cursor-pointer"
          >
            Skip
          </button>
          {!isLastStep ? (
            <button
              onClick={() => setStep(step + 1)}
              className="flex-1 px-4 py-2 bg-primary hover:bg-primary-dark text-white text-sm font-semibold rounded-lg transition-all shadow-sm cursor-pointer"
            >
              Next →
            </button>
          ) : (
            <button
              onClick={dismiss}
              className="flex-1 px-4 py-2 bg-primary hover:bg-primary-dark text-white text-sm font-semibold rounded-lg transition-all shadow-sm cursor-pointer"
            >
              Let's go →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
