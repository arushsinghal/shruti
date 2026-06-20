import { useState } from 'react';

interface Props {
  transcript: string;
  languageDetected?: string;
  isStub: boolean;
  diarizedTranscript?: string;
}

export default function TranscriptViewer({ transcript, languageDetected, isStub, diarizedTranscript }: Props) {
  const [showDiarized, setShowDiarized] = useState(!!diarizedTranscript);

  // Parse diarized transcript into labelled lines with color coding
  // Handles both "Doctor: ..." and "[Professional] ..." formats from backend
  function renderDiarized(text: string) {
    return text.split('\n').filter(Boolean).map((line, i) => {
      const lower = line.toLowerCase();
      const isDr =
        lower.startsWith('doctor:') ||
        lower.startsWith('[professional]') ||
        lower.startsWith('[doctor]');
      const isPat =
        lower.startsWith('patient:') ||
        lower.startsWith('[client]') ||
        lower.startsWith('[patient]');
      const isUnknown = lower.startsWith('unknown:') || lower.startsWith('[speaker');

      const speaker = isDr ? 'Doctor' : isPat ? 'Patient' : isUnknown ? 'Speaker' : null;
      // Strip prefix — handles "Doctor: text", "[Professional] text"
      const content = speaker
        ? line.replace(/^(\[[\w\s]+\]|doctor:|patient:|unknown:|speaker[\w\s]*:)/i, '').trim()
        : line;

      if (!speaker) {
        return <p key={i} className="text-slate-600 text-sm italic pl-2">{line}</p>;
      }

      return (
        <div
          key={i}
          className={`flex gap-3 items-start ${isDr ? 'flex-row' : 'flex-row-reverse'}`}
        >
          <span className={`text-[10px] font-bold uppercase tracking-widest mt-1.5 shrink-0 w-14 ${isDr ? 'text-blue-500 text-left' : 'text-emerald-600 text-right'}`}>
            {speaker}
          </span>
          <div className={`rounded-xl px-4 py-2 text-sm max-w-[80%] ${
            isDr
              ? 'bg-blue-50 text-blue-900 rounded-tl-sm'
              : isPat
              ? 'bg-emerald-50 text-emerald-900 rounded-tr-sm'
              : 'bg-slate-100 text-slate-700'
          }`}>
            {content}
          </div>
        </div>
      );
    });
  }

  return (
    <div className="space-y-3">
      {isStub && (
        <div className="flex items-start gap-2 rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800">
          <span className="mt-0.5 shrink-0">⚠</span>
          <span>
            Audio could not be transcribed — using a sample transcript for demonstration. For best results, speak clearly and ensure microphone access is granted.
          </span>
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
            Transcript
          </h3>
          <div className="flex items-center gap-2">
            {languageDetected && (
              <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full font-mono">
                {languageDetected}
              </span>
            )}
            {diarizedTranscript && (
              <button
                onClick={() => setShowDiarized(!showDiarized)}
                className={`text-xs px-2.5 py-0.5 rounded-full font-medium transition-colors ${
                  showDiarized
                    ? 'bg-blue-100 text-blue-700 hover:bg-slate-100 hover:text-slate-600'
                    : 'bg-slate-100 text-slate-600 hover:bg-blue-100 hover:text-blue-700'
                }`}
              >
                {showDiarized ? '💬 Dialogue View' : '📄 Raw View'}
              </button>
            )}
          </div>
        </div>

        {!isStub && (
          <div className="flex items-center gap-1.5 text-[11px] text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-md px-2.5 py-1 w-fit" title="Sensitive identifiers are scrubbed where detected before storage. Doctor review required.">
            <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <span className="font-semibold">PHI scrubbed</span>
          </div>
        )}

        {showDiarized && diarizedTranscript ? (
          <div className="space-y-3">
            {renderDiarized(diarizedTranscript)}
          </div>
        ) : (
          <p className="text-slate-800 leading-relaxed whitespace-pre-wrap text-sm">{transcript}</p>
        )}
      </div>
    </div>
  );
}
