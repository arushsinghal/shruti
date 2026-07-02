import { useRef, useState, useEffect } from 'react';
import { getWebSocketBase, transcribeAudio, uploadAudio, submitTranscriptText } from '../lib/api';
import type { TranscribeResponse } from '../types/clinical';

interface Props {
  sessionId: string;
  onTranscript: (result: TranscribeResponse, asrMs?: number) => void;
  onAutoProcess?: () => void;
  externalMode?: InputMode;
  onModeChange?: (mode: InputMode) => void;
  hideTabs?: boolean;
  dark?: boolean;
}

type UploadStatus = 'idle' | 'uploading' | 'transcribing' | 'done' | 'error';
export type InputMode = 'file' | 'record' | 'text';

const ACCEPTED = '.mp3,.wav,.m4a,.webm';
const ACCEPTED_SET = new Set(['audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/mp4', 'audio/m4a', 'audio/webm', 'video/webm']);

function isAccepted(file: File) {
  const ext = file.name.split('.').pop()?.toLowerCase() ?? '';
  return ACCEPTED_SET.has(file.type) || ['mp3', 'wav', 'm4a', 'webm'].includes(ext);
}

export default function AudioUploader({ sessionId, onTranscript, onAutoProcess, externalMode, onModeChange, hideTabs, dark }: Props) {
  // d(darkClass, lightClass) — picks based on dark prop
  const d = (dk: string, lt: string) => dark ? dk : lt;
  const inputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const [internalMode, setInternalMode] = useState<InputMode>('record');
  const mode = externalMode ?? internalMode;
  function setMode(m: InputMode) { setInternalMode(m); onModeChange?.(m); }
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<UploadStatus>('idle');
  const [uploadPct, setUploadPct] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [transcriptText, setTranscriptText] = useState('');
  const [fromRecording, setFromRecording] = useState(false);

  // Recording State
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);

  // Waveform visualiser
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const [barHeights, setBarHeights] = useState<number[]>(Array(20).fill(4));

  function startWaveform(stream: MediaStream) {
    try {
      const ctx = new AudioContext();
      const src = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 64;
      src.connect(analyser);
      analyserRef.current = analyser;
      const buf = new Uint8Array(analyser.frequencyBinCount);
      const NUM_BARS = 20;
      function tick() {
        analyser.getByteFrequencyData(buf);
        const step = Math.floor(buf.length / NUM_BARS);
        const heights = Array.from({ length: NUM_BARS }, (_, i) => {
          const val = buf[i * step] ?? 0;
          return Math.max(4, (val / 255) * 48);
        });
        setBarHeights(heights);
        animFrameRef.current = requestAnimationFrame(tick);
      }
      tick();
    } catch {
      // Web Audio not available — use CSS fallback (existing animation)
    }
  }

  function stopWaveform() {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    analyserRef.current = null;
    setBarHeights(Array(20).fill(4));
  }

  // Timer for recording duration
  useEffect(() => {
    let interval: number;
    if (isRecording) {
      interval = window.setInterval(() => setRecordingTime((t) => t + 1), 1000);
    } else {
      setRecordingTime(0);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  // Auto-trigger upload when recording file is ready
  useEffect(() => {
    if (file && fromRecording && status === 'idle') {
      handleUpload();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [file, fromRecording]);

  function formatTime(seconds: number) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  }

  // File Drop Logic
  function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    const f = files[0];
    if (!isAccepted(f)) {
      setError('Unsupported file type. Please upload an mp3, wav, m4a, or webm file.');
      return;
    }
    setFromRecording(false);
    setFile(f);
    setError(null);
  }

  function onDragOver(e: React.DragEvent) { e.preventDefault(); setDragOver(true); }
  function onDragLeave() { setDragOver(false); }
  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    handleFiles(e.dataTransfer.files);
  }

  // Recording Logic
  async function startRecording() {
    try {
      setFromRecording(false);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      const token = localStorage.getItem('token');
      const tokenQuery = token ? `?token=${encodeURIComponent(token)}` : '';
      const ws = new WebSocket(`${getWebSocketBase()}/ws/audio/${sessionId}${tokenQuery}`);
      ws.onopen = () => { console.log('WS: Audio stream connected'); };

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
          if (ws.readyState === WebSocket.OPEN) ws.send(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        if (ws.readyState === WebSocket.OPEN) ws.send('END');
        ws.close();
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const recordedFile = new File([blob], 'live_recording.webm', { type: 'audio/webm' });
        setFromRecording(true);
        setFile(recordedFile);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start(1000);
      setIsRecording(true);
      setError(null);
      setFile(null);
      startWaveform(stream);
    } catch (err: unknown) {
      console.error(err);
      const name = err instanceof Error ? (err as any).name : '';
      if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
        setError('mic_denied');
      } else if (name === 'NotFoundError' || name === 'DevicesNotFoundError') {
        setError('mic_missing');
      } else {
        setError('Microphone unavailable. Please check your device settings.');
      }
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      stopWaveform();
    }
  }

  // Upload Logic
  async function handleUpload() {
    if (!file) return;
    setError(null);
    const asrStart = Date.now();

    try {
      setStatus('uploading');
      setUploadPct(0);
      await uploadAudio(sessionId, file, setUploadPct);

      setStatus('transcribing');
      const result = await transcribeAudio(sessionId);
      const asrMs = Date.now() - asrStart;

      setStatus('done');
      onTranscript(result, asrMs);
      // Auto-trigger clinical processing for recordings
      if (fromRecording && onAutoProcess) {
        onAutoProcess();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed';
      setError(msg);
      setStatus('error');
    }
  }

  // Text Transcript Submit Logic
  async function handleSubmitText() {
    if (!transcriptText.trim()) return;
    setError(null);

    try {
      setStatus('transcribing');
      const result = await submitTranscriptText(sessionId, transcriptText);
      setStatus('done');
      onTranscript(result);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Submission failed';
      setError(msg);
      setStatus('error');
    }
  }

  const isWorking = status === 'uploading' || status === 'transcribing';
  const isAutoFlow = fromRecording && isWorking;

  return (
    <div className="space-y-3">
      {/* Mode Toggle */}
      {!isWorking && status !== 'done' && !hideTabs && (
        <div className={`flex p-1 rounded-lg ${d('bg-slate-800', 'bg-slate-100')}`}>
          {(['record', 'file', 'text'] as const).map((m, i) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-colors ${
                mode === m
                  ? d('bg-slate-700 text-white shadow-sm', 'bg-white text-slate-900 shadow-sm')
                  : d('text-slate-400 hover:text-slate-200', 'text-slate-500 hover:text-slate-700')
              }`}
            >
              {['Live Dictation', 'Upload Audio', 'Direct Text'][i]}
            </button>
          ))}
        </div>
      )}

      {/* Input Area */}
      {mode === 'file' ? (
        <div
          onClick={() => !isWorking && inputRef.current?.click()}
          onDragOver={onDragOver}
          onDragEnter={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          className={[
            'border-2 border-dashed rounded-xl px-6 py-8 text-center transition-colors',
            isWorking ? 'cursor-not-allowed opacity-60' : 'cursor-pointer',
            dragOver
              ? d('border-blue-500 bg-blue-900/30', 'border-blue-400 bg-blue-50')
              : file
                ? d('border-green-600 bg-green-900/20', 'border-green-400 bg-green-50')
                : d('border-slate-600 bg-slate-800/60 hover:border-blue-500 hover:bg-blue-900/20',
                    'border-slate-300 bg-slate-50 hover:border-blue-300 hover:bg-blue-50'),
          ].join(' ')}
        >
          <input ref={inputRef} type="file" accept={ACCEPTED} className="hidden" onChange={(e) => handleFiles(e.target.files)} />
          <div className="text-3xl mb-2">{file ? '🎵' : '📁'}</div>
          {file ? (
            <p className={`text-sm font-medium ${d('text-emerald-400', 'text-green-700')}`}>{file.name}</p>
          ) : (
            <>
              <p className={`text-sm font-medium ${d('text-slate-300', 'text-slate-700')}`}>Drop audio here, or click to browse</p>
              <p className={`text-xs mt-1 ${d('text-slate-500', 'text-slate-400')}`}>mp3 · wav · m4a · webm</p>
            </>
          )}
        </div>
      ) : mode === 'text' ? (
        <div className={`border rounded-xl p-3 ${d('border-slate-700 bg-slate-800/60', 'border-slate-200 bg-slate-50')}`}>
          <textarea
            value={transcriptText}
            onChange={(e) => setTranscriptText(e.target.value)}
            disabled={isWorking}
            placeholder="Paste or write the doctor's transcript here..."
            className={`w-full h-32 p-3 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none ${
              d('bg-slate-900 border-slate-700 text-slate-200 placeholder:text-slate-500',
                'bg-white border-slate-200 text-slate-800')
            }`}
          />
        </div>
      ) : (
        /* Record mode */
        <div className={`border rounded-xl p-6 flex flex-col items-center justify-center min-h-[200px] ${
          d('border-slate-700 bg-slate-800/40', 'border-slate-200 bg-slate-50')
        }`}>
          {!isRecording && !file && !isWorking && (
            <button
              onClick={startRecording}
              className={`w-16 h-16 rounded-full flex items-center justify-center active:scale-95 transition-all cursor-pointer touch-manipulation ${
                d('bg-red-900/50 hover:bg-red-900/70 border border-red-800/60', 'bg-red-100 hover:bg-red-200')
              }`}
            >
              <div className="w-6 h-6 rounded-full bg-red-500"></div>
            </button>
          )}
          {isRecording && (
            <div className="flex flex-col items-center gap-4 w-full">
              {/* Live waveform visualiser */}
              <div className="flex items-end gap-0.5 h-12 px-4 py-1">
                {barHeights.map((h, i) => (
                  <div
                    key={i}
                    className="w-[5px] bg-red-500 rounded-full transition-all duration-75"
                    style={{ height: `${h}px`, opacity: 0.6 + (h / 48) * 0.4 }}
                  />
                ))}
              </div>
              <button
                onClick={stopRecording}
                className="relative flex items-center gap-3 px-6 py-3 rounded-full bg-red-100 border-2 border-red-400 text-red-700 font-bold text-sm cursor-pointer hover:bg-red-200 transition-colors active:scale-[0.97]"
              >
                <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                {formatTime(recordingTime)} — Tap to stop
                <div className="absolute inset-0 rounded-full border-2 border-red-400 opacity-30 animate-ping" />
              </button>
            </div>
          )}
          {!isRecording && isAutoFlow && (
            <div className="w-12 h-12 rounded-full border-2 border-indigo-500/40 flex items-center justify-center">
              <svg className="w-5 h-5 text-indigo-400 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
            </div>
          )}
          {file && !isRecording && !isAutoFlow && (
            <div className="text-center">
              <div className="text-3xl mb-2">🎤</div>
              <p className={`text-sm font-medium ${d('text-emerald-400', 'text-green-700')}`}>Recording Captured</p>
              <button
                onClick={() => { setFile(null); setFromRecording(false); }}
                className={`text-xs mt-2 underline ${d('text-slate-500 hover:text-red-400', 'text-slate-500 hover:text-red-500')}`}
              >
                Discard & Re-record
              </button>
            </div>
          )}
          <div className={`mt-4 text-sm font-medium ${d('text-slate-400', 'text-slate-600')}`}>
            {isRecording
              ? <span className="text-red-400 font-semibold">● {formatTime(recordingTime)}</span>
              : isAutoFlow
                ? status === 'uploading' ? `Uploading… ${uploadPct}%` : 'Transcribing…'
                : file ? 'Ready to process'
                : 'Tap to start recording'}
          </div>
          {isAutoFlow && (
            <p className={`text-xs mt-1 ${d('text-slate-500', 'text-slate-400')}`}>Generating documentation automatically</p>
          )}
        </div>
      )}

      {/* Upload progress */}
      {status === 'uploading' && !isAutoFlow && (
        <div className="space-y-1">
          <div className={`flex justify-between text-xs ${d('text-slate-400', 'text-slate-500')}`}>
            <span>Uploading…</span><span>{uploadPct}%</span>
          </div>
          <div className={`h-1.5 rounded-full overflow-hidden ${d('bg-slate-700', 'bg-slate-200')}`}>
            <div className="h-full bg-blue-500 transition-all duration-200" style={{ width: `${uploadPct}%` }} />
          </div>
        </div>
      )}

      {status === 'transcribing' && !isAutoFlow && (
        <div className={`flex items-center gap-2 text-sm ${d('text-indigo-400', 'text-indigo-600')}`}>
          <svg className="w-4 h-4 animate-spin shrink-0" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          <span className="font-medium">{mode === 'text' ? 'Processing…' : 'Transcribing + diarizing…'}</span>
        </div>
      )}

      {status === 'done' && (
        <p className={`text-sm font-medium ${d('text-emerald-400', 'text-green-600')}`}>Transcription complete.</p>
      )}

      {/* Speech-processing trust disclosure */}
      {mode !== 'text' && status !== 'done' && !isAutoFlow && (
        <p className={`text-[11px] leading-relaxed border-t pt-3 ${
          d('text-slate-500 border-slate-800', 'text-slate-400 border-slate-100')
        }`}>
          Audio processed on-shore via an India-based speech recognition service. Identifiers scrubbed before storage. Audio deleted after transcription.{' '}
          <a href="/privacy" className={`underline ${d('hover:text-slate-300', 'hover:text-slate-600')}`}>Privacy policy</a>
        </p>
      )}

      {/* Mic errors */}
      {error === 'mic_denied' && (
        <div className={`border rounded-xl p-4 space-y-2 ${d('bg-red-900/20 border-red-800/40', 'bg-red-50 border-red-200')}`}>
          <p className={`text-sm font-bold ${d('text-red-400', 'text-red-700')}`}>Microphone access blocked</p>
          <p className={`text-xs ${d('text-red-400', 'text-red-600')}`}>Lipi needs microphone permission to record.</p>
          <button onClick={() => { setError(null); setMode('file'); }} className={`text-xs underline ${d('text-red-400 hover:text-red-300', 'text-red-600 hover:text-red-800')}`}>
            Upload an audio file instead →
          </button>
        </div>
      )}
      {error === 'mic_missing' && (
        <div className={`border rounded-xl p-4 ${d('bg-amber-900/20 border-amber-800/40', 'bg-amber-50 border-amber-200')}`}>
          <p className={`text-sm font-bold ${d('text-amber-400', 'text-amber-700')}`}>No microphone found</p>
          <button onClick={() => { setError(null); setMode('file'); }} className={`text-xs underline mt-2 block ${d('text-amber-400 hover:text-amber-300', 'text-amber-700 hover:text-amber-900')}`}>
            Upload an audio file instead →
          </button>
        </div>
      )}
      {error && error !== 'mic_denied' && error !== 'mic_missing' && (
        <p className={`text-sm border rounded-lg px-3 py-2 ${d('text-red-400 bg-red-900/20 border-red-800/40', 'text-red-600 bg-red-50 border-red-200')}`}>
          {error}
        </p>
      )}

      {/* Action buttons */}
      {status !== 'done' && !isAutoFlow && (
        mode === 'text' ? (
          <button
            onClick={handleSubmitText}
            disabled={!transcriptText.trim() || isWorking}
            className="w-full py-2.5 rounded-lg text-sm font-medium transition-colors bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isWorking ? 'Saving…' : 'Submit Transcript'}
          </button>
        ) : mode === 'file' ? (
          <button
            onClick={handleUpload}
            disabled={!file || isWorking || isRecording}
            className="w-full py-2.5 rounded-lg text-sm font-medium transition-colors bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isWorking ? 'Processing…' : 'Upload & Transcribe'}
          </button>
        ) : null
      )}
    </div>
  );
}
