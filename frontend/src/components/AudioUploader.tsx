import { useRef, useState, useEffect } from 'react';
import { getWebSocketBase, transcribeAudio, uploadAudio, submitTranscriptText } from '../lib/api';
import type { TranscribeResponse } from '../types/clinical';

interface Props {
  sessionId: string;
  onTranscript: (result: TranscribeResponse) => void;
}

type UploadStatus = 'idle' | 'uploading' | 'transcribing' | 'done' | 'error';
type InputMode = 'file' | 'record' | 'text';

const ACCEPTED = '.mp3,.wav,.m4a,.webm';
const ACCEPTED_SET = new Set(['audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/mp4', 'audio/m4a', 'audio/webm', 'video/webm']);

function isAccepted(file: File) {
  const ext = file.name.split('.').pop()?.toLowerCase() ?? '';
  return ACCEPTED_SET.has(file.type) || ['mp3', 'wav', 'm4a', 'webm'].includes(ext);
}

export default function AudioUploader({ sessionId, onTranscript }: Props) {
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
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      // Open WebSocket connection for real-time streaming
      const ws = new WebSocket(`${getWebSocketBase()}/ws/audio/${sessionId}`);
      
      ws.onopen = () => {
        console.log('WS: Audio stream connected');
      };

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
          // Stream chunk to backend in real-time if WS is open
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(e.data);
          }
        }
      };

      mediaRecorder.onstop = () => {
        // Signal end of stream to backend
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('END');
        }
        ws.close();
        
        // Also create a local File blob for the normal upload/transcribe flow
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const recordedFile = new File([blob], 'live_recording.webm', { type: 'audio/webm' });
        setFile(recordedFile);
        stream.getTracks().forEach(track => track.stop()); // release mic
      };

      // timeslice: emit a chunk every 1 second so WS streams in near-real-time
      mediaRecorder.start(1000);
      setIsRecording(true);
      setError(null);
      setFile(null); // clear old file
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

    try {
      setStatus('uploading');
      setUploadPct(0);
      await uploadAudio(sessionId, file, setUploadPct);

      setStatus('transcribing');
      const result = await transcribeAudio(sessionId);

      setStatus('done');
      onTranscript(result);
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
          {!isRecording && !file && (
            <button onClick={startRecording} className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center hover:bg-red-200 transition-colors">
              <div className="w-6 h-6 rounded-full bg-red-500"></div>
            </button>
          )}
          {isRecording && (
            <button onClick={stopRecording} className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center border-2 border-red-500 animate-pulse">
              <div className="w-6 h-6 rounded bg-red-500"></div>
            </button>
          )}
          {file && !isRecording && (
            <div className="text-center">
              <div className="text-3xl mb-2">🎤</div>
              <p className="text-sm font-medium text-green-700">Recording Captured</p>
              <button onClick={() => setFile(null)} className="text-xs text-slate-500 hover:text-red-500 mt-2 underline">Discard & Rerecord</button>
            </div>
          )}
          <div className="mt-4 text-sm font-medium text-slate-600">
            {isRecording ? `Recording... ${formatTime(recordingTime)}` : file ? 'Ready to process' : 'Click to start dictation'}
          </div>
        </div>
      )}

      {/* Progress / status */}
      {status === 'uploading' && (
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

      {status === 'transcribing' && (
        <div className="flex items-center gap-2 text-sm text-indigo-600">
          <span className="animate-spin">⟳</span>
          <span>{mode === 'text' ? 'Processing transcript...' : 'Transcribing audio via Sarvam ASR…'}</span>
        </div>
      )}

      {status === 'done' && (
        <p className="text-sm text-green-600 font-medium">Transcription complete.</p>
      )}

      {error && (
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          {error}
        </p>
      )}

      {/* Action button */}
      {status !== 'done' && (
        mode === 'text' ? (
          <button
            onClick={handleSubmitText}
            disabled={!transcriptText.trim() || isWorking}
            className="w-full py-2.5 rounded-lg text-sm font-medium transition-colors bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isWorking ? 'Saving…' : 'Submit Transcript'}
          </button>
        ) : (
          <button
            onClick={handleUpload}
            disabled={!file || isWorking || isRecording}
            className="w-full py-2.5 rounded-lg text-sm font-medium transition-colors bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isWorking ? 'Processing…' : 'Upload & Transcribe'}
          </button>
        )
      )}
    </div>
  );
}
