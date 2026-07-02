import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createIntakeSession, voiceExtractIntake } from '../lib/api';
import { motion, AnimatePresence } from 'framer-motion';
import { UserPlus, Phone, ChevronLeft, CheckCircle2, Mic, MicOff, Loader2, Wand2, AlertCircle } from 'lucide-react';

const inputCls = 'w-full px-4 py-2.5 border border-slate-200 rounded-xl text-[14px] outline-none focus:border-primary focus:ring-2 focus:ring-primary/15 bg-slate-50 focus:bg-white transition-all placeholder:text-slate-300';

export default function AssistantIntake() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    patient_name: '',
    patient_phone: '',
    patient_age: '',
    patient_sex: '',
    chief_complaint: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);

  // ── Voice mode ──────────────────────────────────────────────────────────
  const [isRecording, setIsRecording] = useState(false);
  const [voiceLoading, setVoiceLoading] = useState(false);
  const [voiceTranscript, setVoiceTranscript] = useState('');
  const [voiceError, setVoiceError] = useState('');
  const [recordingTime, setRecordingTime] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  function set(key: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
      setForm(f => ({ ...f, [key]: e.target.value }));
  }

  async function startVoiceRecord() {
    setVoiceError('');
    setVoiceTranscript('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data); };

      recorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        if (timerRef.current) clearInterval(timerRef.current);
        setRecordingTime(0);

        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setVoiceLoading(true);
        try {
          const result = await voiceExtractIntake(blob);
          setVoiceTranscript(result.transcript);
          // Auto-fill fields — only override empty fields
          setForm(prev => ({
            patient_name: prev.patient_name || result.patient_name || '',
            patient_phone: prev.patient_phone,
            patient_age: prev.patient_age || result.patient_age || '',
            patient_sex: prev.patient_sex || result.patient_sex || '',
            chief_complaint: prev.chief_complaint || result.chief_complaint || '',
          }));
        } catch {
          setVoiceError('Voice extraction failed. Please fill the form manually.');
        } finally {
          setVoiceLoading(false);
        }
      };

      recorder.start(500);
      setIsRecording(true);
      setRecordingTime(0);
      timerRef.current = window.setInterval(() => setRecordingTime(t => t + 1), 1000);
    } catch (e: any) {
      const name = e?.name;
      if (name === 'NotAllowedError') setVoiceError('Microphone access denied. Allow it in browser settings.');
      else if (name === 'NotFoundError') setVoiceError('No microphone found on this device.');
      else setVoiceError('Could not start recording. Check microphone permissions.');
    }
  }

  function stopVoiceRecord() {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  }

  function formatTime(s: number) {
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
  }

  // ── Submit ──────────────────────────────────────────────────────────────
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.patient_name.trim() || !form.patient_phone.trim()) {
      setError('Patient name and WhatsApp number are required.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await createIntakeSession({
        patient_name: form.patient_name.trim(),
        patient_phone: form.patient_phone.trim(),
        patient_age: form.patient_age.trim() || undefined,
        patient_sex: form.patient_sex || undefined,
        chief_complaint: form.chief_complaint.trim() || undefined,
      });
      setDone(true);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to register patient. Try again.');
    } finally {
      setLoading(false);
    }
  }

  function registerAnother() {
    setForm({ patient_name: '', patient_phone: '', patient_age: '', patient_sex: '', chief_complaint: '' });
    setDone(false);
    setError('');
    setVoiceTranscript('');
    setVoiceError('');
  }

  // ── Success screen ──────────────────────────────────────────────────────
  if (done) {
    return (
      <div className="min-h-screen bg-[#FAFAF7] flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-sm text-center space-y-5"
        >
          <div className="flex justify-center">
            <div className="w-16 h-16 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center">
              <CheckCircle2 className="w-8 h-8 text-emerald-500" />
            </div>
          </div>
          <div>
            <h2 className="text-[18px] font-bold text-text-dark">{form.patient_name} registered</h2>
            <p className="text-[13px] text-slate-500 mt-1 leading-relaxed">
              The doctor will see this patient in their waiting room. WhatsApp number is saved — prescription will be sent in one tap.
            </p>
          </div>
          <div className="flex gap-3">
            <button onClick={registerAnother}
              className="flex-1 border border-slate-200 hover:border-primary/30 text-slate-600 hover:text-primary text-[13px] font-semibold py-2.5 rounded-xl transition-all cursor-pointer">
              Register another
            </button>
            <button onClick={() => navigate('/assistant')}
              className="flex-1 bg-primary hover:bg-primary-dark text-white text-[13px] font-semibold py-2.5 rounded-xl transition-all active:scale-[0.98] cursor-pointer">
              Back to queue
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FAFAF7] font-sans">
      {/* Header */}
      <header className="sticky top-0 bg-white/90 backdrop-blur-md border-b border-slate-200/80 z-10">
        <div className="max-w-lg mx-auto px-5 h-14 flex items-center gap-3">
          <button onClick={() => navigate('/assistant')}
            className="p-1.5 rounded-lg text-slate-400 hover:text-primary hover:bg-primary/5 transition-all cursor-pointer">
            <ChevronLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <UserPlus className="w-4 h-4 text-primary" />
            <span className="text-[15px] font-bold text-text-dark">Register patient</span>
          </div>
        </div>
      </header>

      <div className="max-w-lg mx-auto px-5 py-6">

        {/* ── Voice intake strip ───────────────────────────────── */}
        <div className="mb-5 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-5 py-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-[13px] font-bold text-text-dark">Dictate patient details</p>
                <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
                  Say name, age, sex, complaint in Hindi or English — fields fill automatically.
                </p>
                <p className="text-[10px] text-slate-400 mt-0.5 italic">
                  Example: "Priya Sharma, 35 saal, female, bukhaar se aayi hai teen din se"
                </p>
              </div>

              {/* Record button */}
              <button
                type="button"
                onClick={isRecording ? stopVoiceRecord : startVoiceRecord}
                disabled={voiceLoading}
                className={`shrink-0 flex flex-col items-center gap-1 px-4 py-3 rounded-xl border-2 transition-all cursor-pointer disabled:opacity-50 ${
                  isRecording
                    ? 'bg-red-50 border-red-300 text-red-600 hover:bg-red-100'
                    : 'bg-primary/5 border-primary/30 text-primary hover:bg-primary/10 hover:border-primary/50'
                }`}
              >
                {voiceLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : isRecording ? (
                  <MicOff className="w-5 h-5" />
                ) : (
                  <Mic className="w-5 h-5" />
                )}
                <span className="text-[10px] font-bold uppercase tracking-wider">
                  {voiceLoading ? 'Processing…' : isRecording ? 'Stop' : 'Record'}
                </span>
              </button>
            </div>

            {/* Recording waveform bars + timer */}
            <AnimatePresence>
              {isRecording && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-3 flex items-center gap-3 bg-red-50 border border-red-200/70 rounded-xl px-4 py-3"
                >
                  <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse shrink-0" />
                  <div className="flex items-end gap-0.5 h-7">
                    {[...Array(14)].map((_, i) => (
                      <motion.div
                        key={i}
                        className="w-1 bg-red-400 rounded-full"
                        animate={{ height: ['6px', `${8 + Math.sin(i * 1.3) * 8 + 8}px`, '6px'] }}
                        transition={{ duration: 0.6 + i * 0.07, repeat: Infinity, ease: 'easeInOut' }}
                      />
                    ))}
                  </div>
                  <span className="text-[12px] font-mono font-bold text-red-600 ml-1 tabular-nums">
                    {formatTime(recordingTime)}
                  </span>
                  <span className="text-[11px] text-red-500 ml-auto">Recording…</span>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Voice transcript preview */}
            <AnimatePresence>
              {voiceTranscript && !isRecording && (
                <motion.div
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-3 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3"
                >
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <Wand2 className="w-3 h-3 text-primary" />
                    <span className="text-[10px] font-bold text-primary uppercase tracking-wider">Transcript — fields auto-filled below</span>
                  </div>
                  <p className="text-[12px] text-slate-600 leading-relaxed">{voiceTranscript}</p>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Voice error */}
            {voiceError && (
              <div className="mt-3 flex items-center gap-2 text-[12px] text-red-600 bg-red-50 border border-red-100 rounded-xl px-3 py-2.5">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                {voiceError}
              </div>
            )}
          </div>
        </div>

        {/* ── Form ─────────────────────────────────────────────── */}
        <div className="mb-5">
          <h1 className="text-[15px] font-bold text-text-dark">Patient details</h1>
          <p className="text-[12px] text-slate-400 mt-0.5">Verify auto-filled fields or type manually.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Required */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4">
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Required</p>
            <div>
              <label className="block text-[12px] font-semibold text-slate-600 mb-1.5">Patient full name</label>
              <input type="text" required value={form.patient_name} onChange={set('patient_name')}
                placeholder="e.g. Priya Sharma"
                className={`${inputCls}${voiceTranscript && form.patient_name ? ' border-primary/40 bg-primary/[0.02]' : ''}`} autoFocus />
            </div>
            <div>
              <label className="block text-[12px] font-semibold text-slate-600 mb-1.5 flex items-center gap-1.5">
                <Phone className="w-3.5 h-3.5 text-emerald-500" />
                WhatsApp number
              </label>
              <input type="tel" required value={form.patient_phone} onChange={set('patient_phone')}
                placeholder="e.g. 9876543210 or +91…"
                className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-[14px] outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 bg-slate-50 focus:bg-white transition-all placeholder:text-slate-300" />
              <p className="text-[11px] text-slate-400 mt-1">Saved once — used for prescription dispatch. Never shared.</p>
            </div>
          </div>

          {/* Optional */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4">
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Optional — auto-filled from voice</p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[12px] font-semibold text-slate-600 mb-1.5">Age</label>
                <input type="text" value={form.patient_age} onChange={set('patient_age')}
                  placeholder="e.g. 42"
                  className={`${inputCls}${voiceTranscript && form.patient_age ? ' border-primary/40 bg-primary/[0.02]' : ''}`} />
              </div>
              <div>
                <label className="block text-[12px] font-semibold text-slate-600 mb-1.5">Sex</label>
                <select value={form.patient_sex} onChange={set('patient_sex')}
                  className={`w-full px-4 py-2.5 border border-slate-200 rounded-xl text-[14px] outline-none focus:border-primary focus:ring-2 focus:ring-primary/15 bg-slate-50 focus:bg-white transition-all text-slate-700 cursor-pointer${voiceTranscript && form.patient_sex ? ' border-primary/40 bg-primary/[0.02]' : ''}`}>
                  <option value="">Select</option>
                  <option value="M">Male</option>
                  <option value="F">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-[12px] font-semibold text-slate-600 mb-1.5">Chief complaint</label>
              <textarea value={form.chief_complaint} onChange={set('chief_complaint')} rows={2}
                placeholder="e.g. Fever for 3 days, headache…"
                className={`w-full px-4 py-2.5 border border-slate-200 rounded-xl text-[13px] outline-none focus:border-primary focus:ring-2 focus:ring-primary/15 bg-slate-50 focus:bg-white transition-all placeholder:text-slate-300 resize-none${voiceTranscript && form.chief_complaint ? ' border-primary/40 bg-primary/[0.02]' : ''}`} />
              <p className="text-[11px] text-slate-400 mt-1">Shown to the doctor before consultation starts.</p>
            </div>
          </div>

          {error && (
            <p className="text-[12.5px] text-red-600 bg-red-50 border border-red-100 rounded-xl px-4 py-2.5">
              {error}
            </p>
          )}

          <button type="submit" disabled={loading || !form.patient_name.trim() || !form.patient_phone.trim()}
            className="w-full bg-primary hover:bg-primary-dark disabled:opacity-50 text-white text-[14px] font-semibold py-3 rounded-xl transition-all active:scale-[0.98] flex items-center justify-center gap-2 cursor-pointer shadow-sm">
            <UserPlus className="w-4 h-4" />
            {loading ? 'Registering…' : 'Register patient'}
          </button>
        </form>
      </div>
    </div>
  );
}
