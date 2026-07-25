import { useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { useParams } from 'react-router-dom';
import { ShieldCheck, AlertCircle, Loader2, Printer } from 'lucide-react';
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

  const inputCls =
    'block w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-[14px] text-text-dark placeholder-slate-400 focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/15 focus:bg-white transition-all';

  if (html) {
    return (
      <div className="min-h-screen bg-bg-warm font-sans text-text-dark antialiased">
        <header className="sticky top-0 z-10 border-b border-slate-200/80 bg-white/95 backdrop-blur">
          <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
            <div className="flex items-center gap-2.5">
              <span className="grid place-items-center w-8 h-8 rounded-xl bg-primary text-white font-bold text-sm shadow-sm">श</span>
              <div>
                <p className="text-[14px] font-bold tracking-tight text-text-dark leading-tight">Lipi prescription</p>
                <p className="text-[11px] text-slate-500 leading-tight">Verified patient download</p>
              </div>
            </div>
            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 rounded-full bg-primary hover:bg-primary-dark px-4 py-2 text-[12.5px] font-semibold text-white transition-colors cursor-pointer"
            >
              <Printer className="w-3.5 h-3.5" />
              Print / save PDF
            </button>
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-4 py-5">
          <iframe
            ref={iframeRef}
            title="Prescription"
            srcDoc={html}
            className="h-[calc(100vh-96px)] w-full rounded-2xl border border-slate-200/80 bg-white"
          />
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-warm font-sans text-text-dark antialiased">
      <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-5 py-10">
        <div className="mb-7">
          <div className="mb-4 flex items-center gap-2.5">
            <span className="grid place-items-center w-10 h-10 rounded-xl bg-primary text-white font-bold text-lg shadow-sm">श</span>
            <span className="text-[18px] font-bold tracking-tight text-text-dark">Lipi</span>
          </div>
          <h1 className="text-[1.6rem] font-bold tracking-tight leading-snug">Verify prescription access</h1>
          <p className="mt-2 text-[14px] leading-relaxed text-slate-500">
            This secure link opens only after matching the patient details held by the clinic.
          </p>
        </div>

        <form onSubmit={handleVerify} className="space-y-4 rounded-2xl bg-white border border-slate-200/80 p-5">
          <div>
            <label className="block text-[12px] font-semibold text-slate-600 mb-1.5">Patient initials</label>
            <input
              value={initials}
              onChange={(event) => setInitials(event.target.value)}
              className={inputCls}
              placeholder="S.V."
              autoCapitalize="characters"
            />
          </div>

          <div>
            <label className="block text-[12px] font-semibold text-slate-600 mb-1.5">Full name</label>
            <input
              value={patientName}
              onChange={(event) => setPatientName(event.target.value)}
              className={inputCls}
              placeholder="Sita Verma"
              autoComplete="name"
            />
          </div>

          <div>
            <label className="block text-[12px] font-semibold text-slate-600 mb-1.5">Year of birth</label>
            <input
              value={yearOfBirth}
              onChange={(event) => setYearOfBirth(event.target.value.replace(/\D/g, '').slice(0, 4))}
              className={inputCls}
              placeholder="1984"
              inputMode="numeric"
              maxLength={4}
            />
          </div>

          {error && (
            <div className="flex items-center gap-2 bg-red-50 border border-red-100 text-alert-critical px-4 py-3 rounded-xl text-[13px]">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center items-center gap-1.5 py-3.5 px-4 rounded-full text-[14px] font-semibold text-white bg-primary hover:bg-primary-dark active:scale-[0.98] transition-all disabled:opacity-70 cursor-pointer"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
            {loading ? 'Verifying' : 'Continue'}
          </button>
        </form>

        <div className="mt-5 flex items-center justify-center gap-2 text-[12px] text-slate-400">
          <ShieldCheck className="w-3.5 h-3.5" />
          Link access expires automatically. The doctor remains the final authority on all clinical details.
        </div>
      </main>
    </div>
  );
}
