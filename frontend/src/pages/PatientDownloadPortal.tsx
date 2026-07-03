import { useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { useParams } from 'react-router-dom';
import { getPublicPrescriptionHtml, verifyPublicAccess } from '../lib/api';

export default function PatientDownloadPortal() {
  const { token } = useParams<{ token: string }>();
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [patientName, setPatientName] = useState('');
  const [initials, setInitials] = useState('');
  const [yearOfBirth, setYearOfBirth] = useState('');
  const [html, setHtml] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleVerify = async (event: FormEvent) => {
    event.preventDefault();
    if (!token) {
      setError('Invalid prescription link.');
      return;
    }
    if (!patientName.trim() && !initials.trim() && !yearOfBirth.trim()) {
      setError('Enter patient initials, full name, or year of birth.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const verified = await verifyPublicAccess(token, {
        patient_name: patientName.trim(),
        initials: initials.trim(),
        year_of_birth: yearOfBirth.trim(),
      });
      const prescriptionHtml = await getPublicPrescriptionHtml(verified.download_token);
      setHtml(prescriptionHtml);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Could not verify this prescription link.');
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    iframeRef.current?.contentWindow?.focus();
    iframeRef.current?.contentWindow?.print();
  };

  if (html) {
    return (
      <div className="min-h-screen bg-slate-100 text-slate-900">
        <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/95 backdrop-blur">
          <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
            <div>
              <p className="text-sm font-bold text-teal-700">Lipi Prescription</p>
              <p className="text-[11px] text-slate-500">Verified patient download</p>
            </div>
            <button
              onClick={handlePrint}
              className="rounded-md bg-teal-700 px-4 py-2 text-xs font-bold text-white hover:bg-teal-600"
            >
              Print / Save PDF
            </button>
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-4 py-5">
          <iframe
            ref={iframeRef}
            title="Prescription"
            srcDoc={html}
            className="h-[calc(100vh-96px)] w-full rounded-lg border border-slate-200 bg-white shadow-sm"
          />
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-5 py-10">
        <div className="mb-7">
          <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-lg bg-teal-500/15 text-xl font-black text-teal-300">
            L
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Verify prescription access</h1>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            This secure link opens only after matching the patient details held by the clinic.
          </p>
        </div>

        <form onSubmit={handleVerify} className="space-y-4 rounded-lg border border-white/10 bg-white/[0.04] p-5 shadow-2xl">
          <div>
            <label className="mb-1.5 block text-xs font-bold uppercase tracking-wide text-slate-300">
              Patient initials
            </label>
            <input
              value={initials}
              onChange={(event) => setInitials(event.target.value)}
              className="w-full rounded-md border border-white/10 bg-slate-900 px-3 py-2.5 text-sm text-white outline-none focus:border-teal-400"
              placeholder="S.V."
              autoCapitalize="characters"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-bold uppercase tracking-wide text-slate-300">
              Full name
            </label>
            <input
              value={patientName}
              onChange={(event) => setPatientName(event.target.value)}
              className="w-full rounded-md border border-white/10 bg-slate-900 px-3 py-2.5 text-sm text-white outline-none focus:border-teal-400"
              placeholder="Sita Verma"
              autoComplete="name"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-bold uppercase tracking-wide text-slate-300">
              Year of birth
            </label>
            <input
              value={yearOfBirth}
              onChange={(event) => setYearOfBirth(event.target.value.replace(/\D/g, '').slice(0, 4))}
              className="w-full rounded-md border border-white/10 bg-slate-900 px-3 py-2.5 text-sm text-white outline-none focus:border-teal-400"
              placeholder="1984"
              inputMode="numeric"
              maxLength={4}
            />
          </div>

          {error && (
            <div className="rounded-md border border-red-400/30 bg-red-500/10 px-3 py-2 text-xs font-semibold text-red-200">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-teal-500 px-4 py-2.5 text-sm font-bold text-slate-950 transition hover:bg-teal-400 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? 'Verifying...' : 'Continue'}
          </button>
        </form>

        <p className="mt-4 text-center text-[11px] leading-5 text-slate-500">
          Link access expires automatically. The doctor remains the final authority on all clinical details.
        </p>
      </main>
    </div>
  );
}
