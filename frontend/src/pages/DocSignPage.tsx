import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { motion } from 'framer-motion';
import {
  AlertTriangle,
  CheckCircle2,
  PenLine,
  Loader2,
  Activity,
  Pill,
  Stethoscope,
  FlaskConical,
  CalendarClock,
  ShieldAlert,
  TriangleAlert,
} from 'lucide-react';

const api = axios.create({ baseURL: '/api' });

interface DiagnosisAnnotated {
  name: string;
  icd10: string | null;
}

interface VitalFlag {
  label: string;
  value: string;
  severity: 'warning' | 'critical';
}

interface CdsAlert {
  suggestion: string;
  rationale: string;
  urgency: string;
  alert_type: string;
  safety_label?: string;
}

interface SessionData {
  session_id: string;
  patient_name: string;
  doctor_name: string;
  patient_age: string | null;
  patient_sex: string | null;
  patient_phone: string | null;
  soap: Record<string, string>;
  cds_alerts: CdsAlert[];
  diagnoses: string[];
  diagnoses_annotated: DiagnosisAnnotated[];
  medications: string[];
  investigations: string[];
  vitals: string[];
  follow_up: string | string[] | null;
  already_signed: boolean;
  signed_at: string | null;
}

const stagger = {
  animate: { transition: { staggerChildren: 0.07 } },
};

const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] as const } },
};

function parseVitalFlags(vitals: string[]): VitalFlag[] {
  const flags: VitalFlag[] = [];
  for (const v of vitals) {
    const bp = v.match(/BP\s+(\d+)\/(\d+)/i);
    if (bp) {
      const sys = parseInt(bp[1]), dia = parseInt(bp[2]);
      if (sys >= 180 || dia >= 110) flags.push({ label: 'BP', value: `${sys}/${dia} mmHg`, severity: 'critical' });
      else if (sys >= 140 || dia >= 90) flags.push({ label: 'BP', value: `${sys}/${dia} mmHg`, severity: 'warning' });
    }
    const spo2 = v.match(/SpO2\s+(\d+)/i);
    if (spo2) {
      const val = parseInt(spo2[1]);
      if (val < 90) flags.push({ label: 'SpO2', value: `${val}%`, severity: 'critical' });
      else if (val < 94) flags.push({ label: 'SpO2', value: `${val}%`, severity: 'warning' });
    }
    const gluc = v.match(/(?:Blood Glucose|Glucose)\s+(\d+)/i);
    if (gluc) {
      const val = parseInt(gluc[1]);
      if (val > 400 || val < 70) flags.push({ label: 'Glucose', value: `${val} mg/dL`, severity: 'critical' });
      else if (val > 200) flags.push({ label: 'Glucose', value: `${val} mg/dL`, severity: 'warning' });
    }
    const hr = v.match(/(?:HR|Heart Rate|Pulse)\s+(\d+)/i);
    if (hr) {
      const val = parseInt(hr[1]);
      if (val > 120 || val < 50) flags.push({ label: 'HR', value: `${val} bpm`, severity: 'critical' });
      else if (val > 100) flags.push({ label: 'HR', value: `${val} bpm`, severity: 'warning' });
    }
    const ef = v.match(/EF\s+(\d+)/i);
    if (ef) {
      const val = parseInt(ef[1]);
      if (val < 30) flags.push({ label: 'EF', value: `${val}%`, severity: 'critical' });
      else if (val < 40) flags.push({ label: 'EF', value: `${val}%`, severity: 'warning' });
    }
    const temp = v.match(/(?:Temp|Temperature)\s+([\d.]+)/i);
    if (temp) {
      const val = parseFloat(temp[1]);
      const isC = val < 50;
      if (isC && val >= 39.5) flags.push({ label: 'Temp', value: `${val}°C`, severity: 'critical' });
      else if (isC && val >= 38.5) flags.push({ label: 'Temp', value: `${val}°C`, severity: 'warning' });
      else if (!isC && val >= 103) flags.push({ label: 'Temp', value: `${val}°F`, severity: 'critical' });
      else if (!isC && val >= 101) flags.push({ label: 'Temp', value: `${val}°F`, severity: 'warning' });
    }
  }
  return flags;
}

function parseMedLine(m: string): string {
  try {
    const obj = JSON.parse(m);
    if (obj && typeof obj === 'object' && obj.name) {
      return [obj.name, obj.dosage, obj.frequency, obj.duration]
        .filter(Boolean)
        .join(' ');
    }
  } catch {}
  return m;
}

function SoapRow({ label, keys, soap }: { label: string; keys: string[]; soap: Record<string, string> }) {
  const text = keys.map(k => soap[k]).find(Boolean);
  if (!text) return null;
  return (
    <div className="py-3.5 border-b border-slate-100 last:border-0">
      <p className="text-[10.5px] font-bold uppercase tracking-[0.18em] text-slate-400 mb-1.5">{label}</p>
      <p className="text-[14px] text-slate-700 leading-relaxed whitespace-pre-wrap">{text}</p>
    </div>
  );
}

function SkeletonLoader() {
  return (
    <div className="min-h-[100dvh] bg-bg-warm">
      <div className="h-[60px] bg-white border-b border-slate-200/60" />
      <div className="px-4 pt-6 max-w-lg mx-auto space-y-4">
        {[88, 56, 200, 160, 120].map((h, i) => (
          <div
            key={i}
            className="rounded-3xl bg-slate-100 animate-pulse"
            style={{ height: h }}
          />
        ))}
      </div>
    </div>
  );
}

export default function DocSignPage() {
  const { token } = useParams<{ token: string }>();
  const [data, setData] = useState<SessionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [signing, setSigning] = useState(false);
  const [signed, setSigned] = useState(false);
  const [prescriptionSent, setPrescriptionSent] = useState(false);

  useEffect(() => {
    if (!token) return;
    api.get(`/public/sign/${token}`)
      .then(r => {
        setData(r.data);
        if (r.data.already_signed) setSigned(true);
      })
      .catch(e => setError(e.response?.data?.detail || 'This link is invalid or has expired.'))
      .finally(() => setLoading(false));
  }, [token]);

  async function handleSign() {
    if (!token || signing || signed) return;
    setSigning(true);
    try {
      const r = await api.post(`/public/sign/${token}`);
      setSigned(true);
      setPrescriptionSent(!!r.data.prescription_dispatched);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to sign. Please try again.');
    } finally {
      setSigning(false);
    }
  }

  if (loading) return <SkeletonLoader />;

  if (error) {
    return (
      <div className="min-h-[100dvh] bg-bg-warm flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
          className="bg-white border border-slate-200/80 rounded-3xl p-8 max-w-sm w-full text-center shadow-sm"
        >
          <div className="w-12 h-12 rounded-2xl bg-red-50 border border-red-100 flex items-center justify-center mx-auto mb-4">
            <TriangleAlert className="w-5 h-5 text-red-500" />
          </div>
          <p className="text-text-dark font-bold text-lg mb-2">Link unavailable</p>
          <p className="text-[14px] text-slate-500 leading-relaxed">{error}</p>
        </motion.div>
      </div>
    );
  }

  if (!data) return null;

  const followUpText = Array.isArray(data.follow_up) ? data.follow_up[0] : data.follow_up;
  const vitalFlags = parseVitalFlags(data.vitals || []);
  const hasCritical = vitalFlags.some(f => f.severity === 'critical');
  const cdsAlerts = data.cds_alerts || [];
  const criticalAlerts = cdsAlerts.filter(a =>
    a.urgency === 'critical' || a.urgency === 'high' || a.alert_type === 'drug_drug_interaction' || a.alert_type === 'allergy_contraindication'
  );
  const otherAlerts = cdsAlerts.filter(a => !criticalAlerts.includes(a));
  const diagnoses = data.diagnoses_annotated?.length
    ? data.diagnoses_annotated
    : data.diagnoses.map(d => ({ name: d, icd10: null }));

  return (
    <div className="min-h-[100dvh] bg-bg-warm antialiased">

      {/* Top bar — matches Landing nav exactly */}
      <div className="bg-bg-warm/90 backdrop-blur-md border-b border-slate-200/60 px-4 h-[60px] flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-2.5">
          <span className="grid place-items-center w-8 h-8 rounded-xl bg-primary text-white font-bold text-sm shadow-sm">
            श
          </span>
          <span className="text-[17px] font-bold tracking-tight text-text-dark">Lipi</span>
          <span className="text-slate-400 text-[13px] font-medium">Clinical Note</span>
        </div>
        {hasCritical && (
          <span className="flex items-center gap-1.5 text-[11.5px] font-semibold text-red-600 bg-red-50 border border-red-100 rounded-full px-3 py-1">
            <Activity className="w-3 h-3" />
            Abnormal values
          </span>
        )}
      </div>

      {/* Subtle dot backdrop — same as Landing hero */}
      <div className="absolute inset-0 top-[60px] bg-dot-fade pointer-events-none opacity-40" aria-hidden />

      <div className="relative px-4 py-6 max-w-lg mx-auto pb-36">
        <motion.div variants={stagger} initial="initial" animate="animate" className="space-y-4">

          {/* Patient card */}
          <motion.div variants={fadeUp} className="bg-white border border-slate-200/80 rounded-3xl p-6 shadow-sm">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[1.75rem] font-extrabold tracking-tight leading-tight text-text-dark">
                  {data.patient_name || 'Patient'}
                </p>
                <p className="text-[13.5px] text-slate-400 font-medium mt-1">
                  {[data.patient_age, data.patient_sex].filter(Boolean).join(' · ')}
                  {(data.patient_age || data.patient_sex) && data.doctor_name ? (
                    <span className="mx-2 text-slate-200">|</span>
                  ) : null}
                  {data.doctor_name}
                </p>
              </div>
              {signed && (
                <span className="flex-shrink-0 flex items-center gap-1.5 text-[11.5px] font-semibold text-primary bg-primary/[0.07] border border-primary/20 rounded-full px-3 py-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Signed
                </span>
              )}
            </div>
          </motion.div>

          {/* Vital flags */}
          {vitalFlags.length > 0 && (
            <motion.div
              variants={fadeUp}
              className={`rounded-3xl border p-5 ${
                hasCritical
                  ? 'bg-red-50 border-red-100'
                  : 'bg-amber-50 border-amber-100'
              }`}
            >
              <div className="flex items-center gap-2 mb-3">
                <Activity className={`w-4 h-4 ${hasCritical ? 'text-red-500' : 'text-amber-500'}`} />
                <p className={`text-[10.5px] font-bold uppercase tracking-[0.18em] ${hasCritical ? 'text-red-500' : 'text-amber-600'}`}>
                  {hasCritical ? 'Critical vitals' : 'Abnormal vitals'}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {vitalFlags.map((f, i) => (
                  <span
                    key={i}
                    className={`text-[12.5px] font-semibold rounded-full px-3.5 py-1.5 border ${
                      f.severity === 'critical'
                        ? 'bg-white text-red-600 border-red-200'
                        : 'bg-white text-amber-700 border-amber-200'
                    }`}
                  >
                    {f.label}: {f.value}
                  </span>
                ))}
              </div>
            </motion.div>
          )}

          {/* CDS alerts - critical/high */}
          {criticalAlerts.length > 0 && (
            <motion.div variants={fadeUp} className="space-y-2.5">
              <p className="text-[10.5px] font-bold uppercase tracking-[0.18em] text-slate-400 px-1">
                Safety alerts - {criticalAlerts.length} {criticalAlerts.length === 1 ? 'flag' : 'flags'}
              </p>
              {criticalAlerts.map((alert, i) => (
                <div
                  key={i}
                  className="border-l-[3px] border-red-500 bg-white rounded-r-2xl px-4 py-4 border border-slate-200/60 border-l-0"
                  style={{ borderLeft: '3px solid #ef4444' }}
                >
                  <div className="flex items-start gap-3">
                    <ShieldAlert className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-[13.5px] font-semibold text-slate-800 leading-snug">{alert.suggestion}</p>
                      {alert.rationale && (
                        <p className="text-[12px] text-slate-500 mt-1 leading-relaxed">{alert.rationale}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </motion.div>
          )}

          {/* CDS alerts - medium/low */}
          {otherAlerts.length > 0 && (
            <motion.div variants={fadeUp} className="space-y-2">
              {criticalAlerts.length === 0 && (
                <p className="text-[10.5px] font-bold uppercase tracking-[0.18em] text-slate-400 px-1">
                  Clinical notices
                </p>
              )}
              {otherAlerts.map((alert, i) => (
                <div
                  key={i}
                  className="bg-white rounded-r-2xl px-4 py-3.5 border border-slate-200/60"
                  style={{ borderLeft: '3px solid #f59e0b' }}
                >
                  <div className="flex items-start gap-2.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-500 mt-0.5 flex-shrink-0" />
                    <p className="text-[12.5px] font-medium text-slate-700 leading-snug">{alert.suggestion}</p>
                  </div>
                </div>
              ))}
            </motion.div>
          )}

          {/* SOAP note */}
          <motion.div variants={fadeUp} className="bg-white border border-slate-200/80 rounded-3xl p-6 shadow-sm">
            <p className="text-[10.5px] font-bold uppercase tracking-[0.18em] text-slate-400 mb-1">SOAP Note</p>
            <SoapRow label="Subjective" keys={['S', 'subjective', 'Subjective', 's']} soap={data.soap} />
            <SoapRow label="Objective" keys={['O', 'objective', 'Objective', 'o']} soap={data.soap} />
            <SoapRow label="Assessment" keys={['A', 'assessment', 'Assessment', 'a']} soap={data.soap} />
            <SoapRow label="Plan" keys={['P', 'plan', 'Plan', 'p']} soap={data.soap} />
          </motion.div>

          {/* Clinical facts */}
          {(diagnoses.length > 0 || data.medications.length > 0 || data.investigations.length > 0 || followUpText) && (
            <motion.div variants={fadeUp} className="bg-white border border-slate-200/80 rounded-3xl p-6 shadow-sm space-y-5">

              {diagnoses.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 mb-3">
                    <Stethoscope className="w-3.5 h-3.5 text-slate-400" strokeWidth={2} />
                    <p className="text-[10.5px] font-bold uppercase tracking-[0.18em] text-slate-400">Diagnoses</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {diagnoses.map((dx, i) => (
                      <span
                        key={i}
                        className="flex items-center gap-1.5 text-[12.5px] font-medium text-slate-700 bg-slate-50 border border-slate-200 rounded-full px-3.5 py-1.5"
                      >
                        {dx.name}
                        {dx.icd10 && (
                          <span className="font-mono text-[10px] text-primary bg-primary/[0.07] rounded-full px-2 py-0.5">
                            {dx.icd10}
                          </span>
                        )}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {data.medications.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 mb-3">
                    <Pill className="w-3.5 h-3.5 text-slate-400" strokeWidth={2} />
                    <p className="text-[10.5px] font-bold uppercase tracking-[0.18em] text-slate-400">Medications</p>
                  </div>
                  <ul className="space-y-2">
                    {data.medications.map((m, i) => (
                      <li key={i} className="text-[13.5px] text-slate-700 flex items-baseline gap-2.5">
                        <span className="w-1 h-1 rounded-full bg-primary/50 mt-2 flex-shrink-0" />
                        {parseMedLine(typeof m === 'string' ? m : JSON.stringify(m))}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {data.investigations.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 mb-3">
                    <FlaskConical className="w-3.5 h-3.5 text-slate-400" strokeWidth={2} />
                    <p className="text-[10.5px] font-bold uppercase tracking-[0.18em] text-slate-400">Investigations</p>
                  </div>
                  <ul className="space-y-2">
                    {data.investigations.map((inv, i) => (
                      <li key={i} className="text-[13.5px] text-slate-700 flex items-baseline gap-2.5">
                        <span className="w-1 h-1 rounded-full bg-primary/50 mt-2 flex-shrink-0" />
                        {typeof inv === 'string' ? inv : JSON.stringify(inv)}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {followUpText && (
                <div>
                  <div className="flex items-center gap-1.5 mb-2">
                    <CalendarClock className="w-3.5 h-3.5 text-slate-400" strokeWidth={2} />
                    <p className="text-[10.5px] font-bold uppercase tracking-[0.18em] text-slate-400">Follow-up</p>
                  </div>
                  <p className="text-[13.5px] text-slate-700">{followUpText}</p>
                </div>
              )}
            </motion.div>
          )}

        </motion.div>
      </div>

      {/* Sign footer - fixed to bottom */}
      <div className="fixed bottom-0 left-0 right-0 bg-bg-warm/95 backdrop-blur-md border-t border-slate-200 px-4 pt-4 pb-safe">
        <div className="max-w-lg mx-auto pb-5">
          {signed ? (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white border border-slate-200/80 rounded-3xl p-5 flex flex-col items-center gap-3 shadow-sm"
            >
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary" />
                <p className="font-bold text-text-dark">Note signed</p>
              </div>
              <p className="text-[12.5px] text-slate-500 text-center leading-relaxed">
                {prescriptionSent && data.patient_phone
                  ? `Prescription sent to patient's WhatsApp`
                  : data.patient_phone
                  ? 'Prescription dispatch is being processed.'
                  : 'No patient phone on file.'}
              </p>
              <a
                href={`/internal/tpa/${data.session_id}`}
                className="text-[13.5px] font-semibold text-primary bg-primary/[0.07] hover:bg-primary/[0.12] border border-primary/20 rounded-full px-5 py-2 transition-colors"
              >
                View Insurance Claim
              </a>
            </motion.div>
          ) : (
            <div>
              <motion.button
                onClick={handleSign}
                disabled={signing}
                whileTap={{ scale: 0.98 }}
                className="w-full bg-primary hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed
                           text-white font-bold py-4 rounded-full text-[15px]
                           transition-colors duration-150 shadow-sm
                           flex items-center justify-center gap-2.5"
              >
                {signing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Signing...
                  </>
                ) : (
                  <>
                    <PenLine className="w-4 h-4" />
                    {data.patient_phone ? 'Sign & Send to Patient' : 'Sign Note'}
                  </>
                )}
              </motion.button>
              <p className="text-center text-[11.5px] text-slate-400 font-medium mt-2.5">
                {data.patient_phone
                  ? 'Signs and WhatsApps the prescription to the patient.'
                  : 'Signs and locks this clinical note.'}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
