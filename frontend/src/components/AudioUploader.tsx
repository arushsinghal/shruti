import { useRef, useState, useEffect } from 'react';
import { getWebSocketBase, transcribeAudio, uploadAudio, submitTranscriptText } from '../lib/api';
import type { TranscribeResponse } from '../types/clinical';

interface Props {
  sessionId: string;
  onTranscript: (result: TranscribeResponse, asrMs?: number) => void;
  onAutoProcess?: () => void;
}

type UploadStatus = 'idle' | 'uploading' | 'transcribing' | 'done' | 'error';
type InputMode = 'file' | 'record' | 'text';

const ACCEPTED = '.mp3,.wav,.m4a,.webm';
const ACCEPTED_SET = new Set(['audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/mp4', 'audio/m4a', 'audio/webm', 'video/webm']);

function isAccepted(file: File) {
  const ext = file.name.split('.').pop()?.toLowerCase() ?? '';
  return ACCEPTED_SET.has(file.type) || ['mp3', 'wav', 'm4a', 'webm'].includes(ext);
}

export default function AudioUploader({ sessionId, onTranscript, onAutoProcess }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const [mode, setMode] = useState<InputMode>('record');
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
    } catch (err) {
      console.error(err);
      setError('Microphone access denied or unavailable.');
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
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
    <div className="space-y-4">
      {/* Mode Toggle */}
      {!isWorking && status !== 'done' && (
        <div className="flex bg-slate-100 p-1 rounded-lg">
          <button
            onClick={() => setMode('record')}
            className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-colors ${mode === 'record' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
          >
            Live Dictation
          </button>
          <button
            onClick={() => setMode('file')}
            className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-colors ${mode === 'file' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
          >
            Upload Audio
          </button>
          <button
            onClick={() => setMode('text')}
            className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-colors ${mode === 'text' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
          >
            Direct Text Input
          </button>
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
            'border-2 border-dashed rounded-xl px-6 py-10 text-center transition-colors',
            isWorking ? 'cursor-not-allowed opacity-60' : 'cursor-pointer',
            dragOver ? 'border-blue-400 bg-blue-50' : file ? 'border-green-400 bg-green-50' : 'border-slate-300 bg-slate-50 hover:border-blue-300 hover:bg-blue-50',
          ].join(' ')}
        >
          <input ref={inputRef} type="file" accept={ACCEPTED} className="hidden" onChange={(e) => handleFiles(e.target.files)} />
          <div className="text-3xl mb-2">{file ? '🎵' : '📁'}</div>
          {file ? (
            <p className="text-sm font-medium text-green-700">{file.name}</p>
          ) : (
            <>
              <p className="text-sm font-medium text-slate-700">Drop an audio file here, or click to browse</p>
              <p className="text-xs text-slate-400 mt-1">mp3 · wav · m4a · webm</p>
            </>
          )}
        </div>
      ) : mode === 'text' ? (
        <div className="border border-slate-200 rounded-xl p-4 bg-slate-50">
          <textarea
            value={transcriptText}
            onChange={(e) => setTranscriptText(e.target.value)}
            disabled={isWorking}
            placeholder="Paste or write the doctor's transcript here..."
            className="w-full h-32 p-3 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
          />
        </div>
      ) : (
        <div className="border border-slate-200 rounded-xl p-8 flex flex-col items-center justify-center bg-slate-50">
          {!isRecording && !file && !isWorking && (
            <button onClick={startRecording} className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center hover:bg-red-200 transition-colors cursor-pointer">
              <div className="w-6 h-6 rounded-full bg-red-500"></div>
            </button>
          )}
          {isRecording && (
            <button onClick={stopRecording} className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center border-2 border-red-500 animate-pulse cursor-pointer">
              <div className="w-6 h-6 rounded bg-red-500"></div>
            </button>
          )}
          {/* Auto-flow: recording stopped, processing in progress */}
          {!isRecording && isAutoFlow && (
            <div className="flex flex-col items-center gap-3">
              <div className="w-14 h-14 rounded-full border-2 border-primary/30 flex items-center justify-center">
                <svg className="w-6 h-6 text-primary animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
              </div>
            </div>
          )}
          {file && !isRecording && !isAutoFlow && (
            <div className="text-center">
              <div className="text-3xl mb-2">🎤</div>
              <p className="text-sm font-medium text-green-700">Recording Captured</p>
              <button onClick={() => { setFile(null); setFromRecording(false); }} className="text-xs text-slate-500 hover:text-red-500 mt-2 underline">Discard & Re-record</button>
            </div>
          )}
          <div className="mt-4 text-sm font-medium text-slate-600">
            {isRecording
              ? `Recording... ${formatTime(recordingTime)}`
              : isAutoFlow
                ? status === 'uploading' ? `Uploading… ${uploadPct}%` : 'Transcribing via Sarvam AI…'
                : file ? 'Ready to process'
                : 'Click to start dictation'}
          </div>
          {isAutoFlow && (
            <p className="text-xs text-slate-400 mt-1">Generating documentation automatically</p>
          )}
        </div>
      )}

      {/* Progress / status (file/upload mode) */}
      {status === 'uploading' && !isAutoFlow && (
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-slate-500">
            <span>Uploading…</span>
            <span>{uploadPct}%</span>
          </div>
          <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
            <div className="h-full bg-blue-500 transition-all duration-200" style={{ width: `${uploadPct}%` }} />
          </div>
        </div>
      )}

      {status === 'transcribing' && !isAutoFlow && (
        <div className="flex items-center gap-2 text-sm text-indigo-600">
          <span className="animate-spin">⟳</span>
          <span>{mode === 'text' ? 'Processing transcript...' : 'Transcribing audio via Sarvam AI…'}</span>
        </div>
      )}

      {status === 'done' && (
        <div className="space-y-1">
          <p className="text-sm text-green-600 font-medium">Transcription complete.</p>
          <p className="text-xs text-slate-400">Transcript identifiers scrubbed before storage.</p>
        </div>
      )}

      {/* Sarvam trust disclosure */}
      {mode !== 'text' && status !== 'done' && !isAutoFlow && (
        <p className="text-[11px] text-slate-400 leading-relaxed border-t border-slate-100 pt-3">
          Audio is processed through{' '}
          <a href="https://sarvam.ai" target="_blank" rel="noopener noreferrer" className="underline hover:text-slate-600">
            Sarvam AI
          </a>{' '}
          for speech-to-text. Transcript identifiers are scrubbed before storage. Raw audio is deleted
          after note generation.{' '}
          <a href="/privacy" className="underline hover:text-slate-600">
            Privacy policy
          </a>
        </p>
      )}

      {error && (
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          {error}
        </p>
      )}

      {/* Action button — only shown for non-auto file/text modes */}
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
