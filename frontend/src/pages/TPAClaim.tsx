import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../lib/api';

interface DiagnosisAnnotated {
  name: string;
  icd10: string | null;
}

interface TPAData {
  session_id: string;
  generated_at: string;
  patient: { name: string; age: string; sex: string; phone: string };
  doctor: {
    name: string;
    nmc_number: string;
    specialization: string;
    clinic_name: string;
    clinic_address: string;
    clinic_phone: string;
  };
  consultation: { date: string; signed: boolean };
  clinical: {
    diagnoses: DiagnosisAnnotated[];
    primary_icd10: string | null;
    primary_diagnosis: string;
    assessment: string;
    medications: string[];
    vitals: string[];
    investigations: string[];
  };
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="mb-3">
      <p className="text-[10px] uppercase tracking-wider text-slate-400 mb-0.5">{label}</p>
      <p className="text-sm font-medium text-slate-800">{value || '—'}</p>
    </div>
  );
}

export default function TPAClaim() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [data, setData] = useState<TPAData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!sessionId) return;
    api.get(`/internal/tpa-claim/${sessionId}`)
      .then(r => setData(r.data))
      .catch(e => setError(e.response?.data?.detail || 'Failed to load claim'))
      .finally(() => setLoading(false));
  }, [sessionId]);

  function openPrint() {
    window.open(`/api/internal/tpa-claim/${sessionId}/print`, '_blank');
  }

  if (loading) return <div className="flex items-center justify-center h-64 text-slate-400 text-sm">Loading claim...</div>;
  if (error) return <div className="p-6 text-red-600 text-sm">{error}</div>;
  if (!data) return null;

  const { patient, doctor, consultation, clinical } = data;

  return (
    <div className="max-w-3xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-800">TPA Claim Packet</h1>
          <p className="text-sm text-slate-500 mt-0.5">{consultation.date}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-xs font-semibold rounded-full px-3 py-1 border ${consultation.signed ? 'bg-emerald-50 border-emerald-200 text-emerald-700' : 'bg-amber-50 border-amber-200 text-amber-700'}`}>
            {consultation.signed ? '✓ Doctor Signed' : '⚠ Awaiting Signature'}
          </span>
          <button
            onClick={openPrint}
            className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-4 py-2 rounded-lg"
          >
            Print / Save PDF
          </button>
        </div>
      </div>

      {/* Patient + Doctor */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Patient</p>
          <Field label="Name" value={patient.name} />
          <Field label="Age / Sex" value={[patient.age, patient.sex].filter(Boolean).join(' / ')} />
          <Field label="Phone" value={patient.phone} />
          <Field label="Date of Consultation" value={consultation.date} />
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Treating Doctor</p>
          <Field label="Name" value={doctor.name} />
          <Field label="NMC Reg. No." value={doctor.nmc_number} />
          <Field label="Specialization" value={doctor.specialization} />
          <Field label="Clinic" value={doctor.clinic_name} />
          <Field label="Address" value={doctor.clinic_address} />
        </div>
      </div>

      {/* Diagnoses with ICD-10 */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 mb-4">
        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Diagnosis (ICD-10)</p>
        {clinical.diagnoses.length === 0 ? (
          <p className="text-sm text-slate-400 italic">No diagnoses extracted</p>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-100">
                <th className="text-left text-xs text-slate-400 uppercase pb-2 font-medium">Diagnosis</th>
                <th className="text-left text-xs text-slate-400 uppercase pb-2 font-medium">ICD-10 Code</th>
                <th className="text-left text-xs text-slate-400 uppercase pb-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {clinical.diagnoses.map((dx, i) => (
                <tr key={i} className="border-b border-slate-50 last:border-0">
                  <td className="py-2.5 text-sm text-slate-800">{dx.name}</td>
                  <td className="py-2.5">
                    {dx.icd10
                      ? <span className="font-mono text-sm text-blue-700 font-bold">{dx.icd10}</span>
                      : <span className="text-xs text-slate-300">not mapped</span>}
                  </td>
                  <td className="py-2.5">
                    <span className="text-xs text-slate-500 bg-slate-100 rounded px-2 py-0.5">
                      {i === 0 ? 'Primary' : 'Secondary'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Assessment */}
      {clinical.assessment && (
        <div className="bg-white rounded-xl border border-slate-200 p-4 mb-4">
          <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Clinical Assessment</p>
          <p className="text-sm text-slate-800 leading-relaxed whitespace-pre-wrap">{clinical.assessment}</p>
        </div>
      )}

      {/* Medications + Vitals */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        {clinical.medications.length > 0 && (
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Medications Prescribed</p>
            <ul className="space-y-1.5">
              {clinical.medications.map((m, i) => (
                <li key={i} className="text-sm text-slate-800 flex gap-2">
                  <span className="text-slate-300">•</span>{m}
                </li>
              ))}
            </ul>
          </div>
        )}
        {clinical.vitals.length > 0 && (
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Vitals Recorded</p>
            <ul className="space-y-1.5">
              {clinical.vitals.map((v, i) => (
                <li key={i} className="text-sm text-slate-800 flex gap-2">
                  <span className="text-slate-300">•</span>{v}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Investigations */}
      {clinical.investigations.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-4 mb-4">
          <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Investigations Advised</p>
          <div className="flex flex-wrap gap-2">
            {clinical.investigations.map((inv, i) => (
              <span key={i} className="text-xs bg-slate-100 text-slate-700 rounded-lg px-2.5 py-1">{inv}</span>
            ))}
          </div>
        </div>
      )}

      {/* Signature block */}
      <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 mt-2">
        <div className="grid grid-cols-2 gap-8">
          <div>
            <p className="text-xs text-slate-400 uppercase tracking-wider mb-2">Doctor Signature</p>
            <div className="h-12 border-b border-slate-300 mb-2" />
            <p className="text-xs text-slate-500">{doctor.name}{doctor.nmc_number ? ` · NMC ${doctor.nmc_number}` : ''}</p>
          </div>
          <div>
            <p className="text-xs text-slate-400 uppercase tracking-wider mb-2">Hospital / Clinic Stamp</p>
            <div className="h-12 border border-dashed border-slate-300 rounded-lg mb-2" />
            <p className="text-xs text-slate-500">{doctor.clinic_name}</p>
          </div>
        </div>
      </div>

      <p className="text-center text-[10px] text-slate-300 mt-6">
        Generated by Lipi Clinical AI · For insurance / TPA use only · Session {data.session_id.slice(0, 8).toUpperCase()}
      </p>
    </div>
  );
}
