import { useState } from 'react';
import type { ProcessClinicalResponse } from '../types/clinical';

interface Props {
  results: ProcessClinicalResponse;
  patientName?: string;
  doctorName?: string;
}

// Indian medical frequency abbreviations + Hindi translations
const FREQ_TABLE: Array<[string, string, string]> = [
  ['once daily', 'OD', 'दिन में एक बार'],
  ['once a day', 'OD', 'दिन में एक बार'],
  ['od ', 'OD', 'दिन में एक बार'],
  ['twice daily', 'BD', 'दिन में दो बार'],
  ['twice a day', 'BD', 'दिन में दो बार'],
  ['two times', 'BD', 'दिन में दो बार'],
  ['bd ', 'BD', 'दिन में दो बार'],
  ['three times', 'TDS', 'दिन में तीन बार'],
  ['thrice', 'TDS', 'दिन में तीन बार'],
  ['tds', 'TDS', 'दिन में तीन बार'],
  ['four times', 'QID', 'दिन में चार बार'],
  ['qid', 'QID', 'दिन में चार बार'],
  ['as needed', 'SOS', 'ज़रूरत पड़ने पर'],
  ['when required', 'SOS', 'ज़रूरत पड़ने पर'],
  ['sos', 'SOS', 'ज़रूरत पड़ने पर'],
  ['before meals', 'AC', 'खाने से पहले'],
  ['after meals', 'PC', 'खाने के बाद'],
  ['at bedtime', 'HS', 'सोने से पहले'],
  ['morning', 'AM', 'सुबह'],
  ['night', 'HS', 'रात को सोने से पहले'],
];

function mapFreq(freq: string): { abbr: string; hindi: string } {
  const lower = (freq || '').toLowerCase();
  for (const [pattern, abbr, hindi] of FREQ_TABLE) {
    if (lower.includes(pattern)) return { abbr, hindi };
  }
  return { abbr: freq?.toUpperCase() || '—', hindi: freq || '—' };
}

const RED_FLAGS = [
  'तेज़ बुखार हो (103°F / 39.4°C से ऊपर)',
  'सांस लेने में तकलीफ हो',
  'बेहोशी या तेज़ चक्कर आए',
  'उल्टी बंद न हो या खून आए',
  'दर्द अचानक बहुत ज़्यादा बढ़ जाए',
];

const GENERAL_TIPS = [
  'दवाई डॉक्टर के कहे अनुसार ही लें — खुद बंद न करें',
  'पर्याप्त पानी पिएं — दिन में कम से कम 8-10 गिलास',
  'खाने के बाद दवाई लें (जब तक अलग न कहा हो)',
  'आराम करें, भारी काम से बचें',
];

export default function PatientInstructionsHindi({ results, patientName, doctorName }: Props) {
  const [open, setOpen] = useState(false);
  const meds = results.facts?.medications ?? [];
  const today = new Date().toLocaleDateString('hi-IN', { day: 'numeric', month: 'long', year: 'numeric' });

  function buildWhatsAppText() {
    const lines = [
      `*मरीज़ की पर्ची — ${patientName ?? 'मरीज़'}*`,
      `_${today}_`,
      '',
      '*💊 दवाइयाँ:*',
      ...(meds.length > 0
        ? meds.map(m => {
            const { abbr, hindi } = mapFreq(m.frequency || '');
            return `• ${m.name.charAt(0).toUpperCase() + m.name.slice(1)}${m.dosage ? ' ' + m.dosage : ''} — ${hindi} (${abbr})`;
          })
        : ['• डॉक्टर द्वारा दवाई बताई जाएगी']),
      '',
      '*⚠️ तुरंत अस्पताल जाएं अगर:*',
      ...RED_FLAGS.map(f => `• ${f}`),
      '',
      `_${doctorName ? `Dr. ${doctorName}` : 'आपके डॉक्टर'} द्वारा समीक्षित · Lipi Health_`,
    ];
    return encodeURIComponent(lines.join('\n'));
  }

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-1.5 text-xs font-medium text-orange-700 hover:text-orange-900 border border-orange-200 hover:border-orange-400 bg-orange-50 hover:bg-orange-100 rounded px-3 py-1.5 transition-all"
        title="मरीज़ को हिंदी में पर्ची दें"
      >
        <span className="font-bold text-sm leading-none">अ</span>
        मरीज़ पर्ची
      </button>

      {open && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm border border-slate-200 flex flex-col max-h-[90vh]">

            {/* Header */}
            <div className="p-5 border-b border-slate-100 flex items-center justify-between shrink-0">
              <div>
                <h2 className="font-bold text-slate-800 text-base">मरीज़ की पर्ची</h2>
                <p className="text-[11px] text-slate-400 mt-0.5">Patient copy in Hindi · share via WhatsApp</p>
              </div>
              <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-slate-600 transition-colors">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Body */}
            <div className="p-5 overflow-y-auto flex-grow space-y-4">

              {/* Patient + date */}
              <div className="flex justify-between text-xs text-slate-500 pb-2 border-b border-slate-100">
                <span>मरीज़: <strong className="text-slate-800">{patientName ?? 'अज्ञात'}</strong></span>
                <span>{today}</span>
              </div>

              {/* Medicines */}
              <div>
                <h3 className="text-xs font-bold text-slate-600 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  💊 दवाइयाँ
                </h3>
                {meds.length > 0 ? (
                  <div className="space-y-2">
                    {meds.map((m, i) => {
                      const { abbr, hindi } = mapFreq(m.frequency || '');
                      return (
                        <div key={i} className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                          <div className="flex items-start justify-between">
                            <span className="font-bold text-slate-800 text-sm capitalize">{m.name}</span>
                            {m.dosage && <span className="text-xs text-slate-500 font-medium">{m.dosage}</span>}
                          </div>
                          <div className="mt-1 text-xs text-slate-600">
                            {hindi}{' '}
                            <span className="font-bold text-primary bg-primary/10 px-1.5 py-0.5 rounded text-[10px]">{abbr}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">डॉक्टर द्वारा बताई जाएगी</p>
                )}
              </div>

              {/* General tips */}
              <div>
                <h3 className="text-xs font-bold text-slate-600 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  ✅ सामान्य सलाह
                </h3>
                <div className="space-y-1.5">
                  {GENERAL_TIPS.map((tip, i) => (
                    <p key={i} className="text-xs text-slate-600 flex items-start gap-1.5">
                      <span className="text-primary font-bold mt-0.5 shrink-0">•</span>
                      {tip}
                    </p>
                  ))}
                </div>
              </div>

              {/* Red flags */}
              <div>
                <h3 className="text-xs font-bold text-red-600 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  ⚠️ तुरंत अस्पताल जाएं अगर
                </h3>
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 space-y-1.5">
                  {RED_FLAGS.map((flag, i) => (
                    <p key={i} className="text-xs text-red-700 flex items-start gap-1.5">
                      <span className="mt-0.5 shrink-0">•</span>
                      {flag}
                    </p>
                  ))}
                </div>
              </div>

              <p className="text-[10px] text-slate-400 pt-2 border-t border-slate-100">
                {doctorName ? `Dr. ${doctorName}` : 'आपके डॉक्टर'} द्वारा समीक्षित · Lipi Health · यह पर्ची डॉक्टर की सलाह का विकल्प नहीं है
              </p>
            </div>

            {/* Footer actions */}
            <div className="p-4 border-t border-slate-100 flex gap-2 shrink-0">
              <a
                href={`https://wa.me/?text=${buildWhatsAppText()}`}
                target="_blank"
                rel="noreferrer"
                className="flex-1 flex items-center justify-center gap-2 bg-[#25D366] hover:bg-[#1ebe5d] text-white text-sm font-bold rounded-lg py-2.5 transition-colors"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/>
                  <path d="M12 0C5.373 0 0 5.373 0 12c0 2.123.554 4.112 1.528 5.834L0 24l6.336-1.503A11.956 11.956 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.818a9.818 9.818 0 01-5.002-1.371l-.36-.213-3.732.885.937-3.632-.234-.373A9.818 9.818 0 1112 21.818z"/>
                </svg>
                WhatsApp करें
              </a>
              <button
                onClick={() => setOpen(false)}
                className="px-4 text-sm text-slate-500 hover:text-slate-700 font-medium border border-slate-200 rounded-lg transition-colors"
              >
                बंद करें
              </button>
            </div>

          </div>
        </div>
      )}
    </>
  );
}
