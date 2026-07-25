import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';

interface Medication {
  name?: string;
  dose?: string;
  dosage?: string;
  frequency?: string;
  duration?: string;
}

interface Visit {
  session_id: string;
  doctor_name: string | null;
  created_at: string;
  diagnosis: string | null;
  medications: Medication[];
}

interface PatientRecordsResponse {
  patient_name: string | null;
  phone_last4: string;
  visits: Visit[];
}

const DEMO_DATA: PatientRecordsResponse = {
  patient_name: 'Priya Sharma',
  phone_last4: '4821',
  visits: [
    {
      session_id: 'demo-3',
      doctor_name: 'Anjali Mehra',
      created_at: '2026-06-18T10:30:00Z',
      diagnosis: 'Viral upper respiratory infection',
      medications: [
        { name: 'Paracetamol', dose: '650mg', frequency: 'Twice daily', duration: '3 days' },
        { name: 'Cetirizine', dose: '10mg', frequency: 'Once at night', duration: '5 days' },
      ],
    },
    {
      session_id: 'demo-2',
      doctor_name: 'Anjali Mehra',
      created_at: '2026-03-02T09:15:00Z',
      diagnosis: 'Type 2 diabetes, routine follow-up',
      medications: [
        { name: 'Metformin', dose: '500mg', frequency: 'Twice daily', duration: 'Ongoing' },
      ],
    },
    {
      session_id: 'demo-1',
      doctor_name: 'Rahul Bansal',
      created_at: '2025-11-14T16:00:00Z',
      diagnosis: 'Tension headache',
      medications: [
        { name: 'Ibuprofen', dose: '400mg', frequency: 'As needed', duration: '5 days' },
      ],
    },
  ],
};

function fmt(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' });
  } catch {
    return iso;
  }
}

const fadeUp = {
  hidden: { opacity: 0, y: 14 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.45, ease: [0.16, 1, 0.3, 1] as const } },
};

export default function PatientRecords() {
  const { token } = useParams<{ token: string }>();
  const reduce = useReducedMotion();
  const isDemo = token === 'demo';

  const [data, setData] = useState<PatientRecordsResponse | null>(isDemo ? DEMO_DATA : null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(!isDemo);

  useEffect(() => {
    if (isDemo || !token) return;
    fetch(`/api/public/patient-records/${token}`)
      .then(async r => {
        if (!r.ok) {
          const body = await r.json().catch(() => ({}));
          throw new Error(body.detail || 'This link is no longer valid.');
        }
        return r.json() as Promise<PatientRecordsResponse>;
      })
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [token, isDemo]);

  return (
    <div className="min-h-screen bg-bg-warm font-sans text-text-dark antialiased">
      <div className="max-w-xl mx-auto px-5 py-10">

        {/* Header */}
        <div className="flex items-center gap-2.5 mb-8">
          <span className="grid place-items-center w-9 h-9 rounded-xl bg-primary text-white font-bold text-base shadow-sm">श</span>
          <span className="text-[18px] font-bold tracking-tight text-text-dark">Lipi</span>
          {isDemo && (
            <span className="ml-auto text-[10.5px] font-bold uppercase tracking-wider text-primary bg-primary/10 border border-primary/20 px-2.5 py-1 rounded-full">
              Demo
            </span>
          )}
        </div>

        <motion.div initial={reduce ? false : 'hidden'} animate="visible" variants={fadeUp}>
          <h1 className="text-[1.6rem] font-bold tracking-tight leading-snug mb-1.5">
            Your health record
          </h1>
          {data && (
            <p className="text-[14px] text-slate-500 mb-8">
              {data.patient_name || 'Patient'} · Number ending in •••{data.phone_last4}
            </p>
          )}
        </motion.div>

        {/* Loading */}
        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-32 bg-white border border-slate-200/80 rounded-2xl animate-pulse" />
            ))}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="rounded-2xl bg-red-50 border border-red-100 px-5 py-4 text-[13.5px] text-red-700 leading-relaxed">
            {error}
          </div>
        )}

        {/* Empty */}
        {data && data.visits.length === 0 && (
          <div className="text-center py-16 border border-slate-200 border-dashed rounded-2xl bg-white">
            <p className="text-[13.5px] text-slate-500">No completed visits yet. Once your doctor signs a consultation, it will appear here.</p>
          </div>
        )}

        {/* Visits */}
        {data && data.visits.length > 0 && (
          <div className="space-y-4">
            {data.visits.map((v, i) => (
              <motion.div
                key={v.session_id}
                initial={reduce ? false : { opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.45, delay: reduce ? 0 : i * 0.06, ease: [0.16, 1, 0.3, 1] }}
                className="bg-white rounded-2xl border border-slate-200/80 overflow-hidden"
              >
                <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between gap-3">
                  <p className="font-semibold text-[14px] text-text-dark leading-snug">
                    {v.diagnosis || 'Consultation'}
                  </p>
                  <span className="text-[11.5px] text-slate-400 shrink-0">{fmt(v.created_at)}</span>
                </div>
                <div className="px-5 py-4 space-y-3">
                  {v.doctor_name && (
                    <p className="text-[12.5px] text-slate-500">
                      {/^dr\.?\s/i.test(v.doctor_name) ? v.doctor_name : `Dr. ${v.doctor_name}`}
                    </p>
                  )}
                  {v.medications.length > 0 && (
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Medicines</p>
                      <div className="space-y-1.5">
                        {v.medications.map((m, mi) => (
                          <div key={mi} className="flex items-start gap-2 text-[13px]">
                            <span className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0" />
                            <span className="text-text-dark font-medium">{m.name || 'Medicine'}</span>
                            {(m.dose || m.dosage || m.frequency || m.duration) && (
                              <span className="text-slate-500">
                                {[m.dose || m.dosage, m.frequency, m.duration].filter(Boolean).join(' · ')}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        )}

        <p className="text-[11px] text-slate-400 text-center pt-8 leading-relaxed">
          This record is for your reference only. Always consult your doctor before changing medicines.
        </p>
      </div>
    </div>
  );
}
