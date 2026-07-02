import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { sendFollowUpReminder } from '../lib/api';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
  defaultFollowUp?: string;
  patientName?: string;
}

export default function FollowUpReminderModal({ isOpen, onClose, sessionId, defaultFollowUp, patientName }: Props) {
  const [phone, setPhone] = useState('');
  const [followUpText, setFollowUpText] = useState(defaultFollowUp || '');
  const [consent, setConsent] = useState(false);
  const [scheduleMode, setScheduleMode] = useState<'now' | 'tomorrow' | 'three_days' | 'custom'>('now');
  const [customDateTime, setCustomDateTime] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [resultStatus, setResultStatus] = useState<'sent' | 'scheduled' | null>(null);

  useEffect(() => {
    if (isOpen) {
      setFollowUpText(defaultFollowUp || 'Please follow up as advised by your doctor.');
      setError('');
      setResultStatus(null);
    }
  }, [defaultFollowUp, isOpen]);

  if (!isOpen) return null;

  const resetAndClose = () => {
    setPhone('');
    setConsent(false);
    setScheduleMode('now');
    setCustomDateTime('');
    setError('');
    setResultStatus(null);
    onClose();
  };

  const scheduledFor = () => {
    const now = new Date();
    if (scheduleMode === 'now') return undefined;
    if (scheduleMode === 'tomorrow') {
      now.setDate(now.getDate() + 1);
      return now.toISOString();
    }
    if (scheduleMode === 'three_days') {
      now.setDate(now.getDate() + 3);
      return now.toISOString();
    }
    if (!customDateTime) return '';
    return new Date(customDateTime).toISOString();
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!consent) {
      setError('Patient consent is required to send a follow-up reminder.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const schedule = scheduledFor();
      if (schedule === '') {
        setError('Choose a custom date and time.');
        return;
      }
      const response = await sendFollowUpReminder(sessionId, phone, consent, followUpText, schedule);
      setResultStatus(response.status);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to send follow-up reminder.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[210] flex items-center justify-center bg-black/60 px-4">
      <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Send follow-up reminder</h3>
            <p className="mt-0.5 text-xs text-slate-500">{patientName || 'Patient'} will receive this on WhatsApp.</p>
          </div>
          <button onClick={resetAndClose} className="text-slate-400 hover:text-slate-700">x</button>
        </div>

        {resultStatus ? (
          <div className="space-y-4 p-5 text-center">
            <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-emerald-50 text-emerald-700">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="text-sm font-semibold text-slate-800">
              {resultStatus === 'scheduled' ? 'Follow-up reminder scheduled.' : 'Follow-up reminder sent.'}
            </p>
            <button onClick={resetAndClose} className="rounded-md bg-primary px-4 py-2 text-xs font-bold text-white">
              Done
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 p-5">
            <div>
              <label className="mb-1.5 block text-xs font-bold uppercase tracking-wide text-slate-500">WhatsApp number</label>
              <input
                required
                type="tel"
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
                placeholder="9876543210 or +91..."
                className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-bold uppercase tracking-wide text-slate-500">Reminder text</label>
              <textarea
                value={followUpText}
                onChange={(event) => setFollowUpText(event.target.value)}
                rows={4}
                className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-bold uppercase tracking-wide text-slate-500">Delivery time</label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  ['now', 'Send now'],
                  ['tomorrow', 'Tomorrow'],
                  ['three_days', 'In 3 days'],
                  ['custom', 'Custom'],
                ].map(([value, label]) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => setScheduleMode(value as typeof scheduleMode)}
                    className={`rounded-md border px-3 py-2 text-xs font-semibold ${
                      scheduleMode === value
                        ? 'border-primary bg-primary/10 text-primary'
                        : 'border-slate-200 bg-white text-slate-600'
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
              {scheduleMode === 'custom' && (
                <input
                  type="datetime-local"
                  value={customDateTime}
                  onChange={(event) => setCustomDateTime(event.target.value)}
                  className="mt-2 w-full rounded-md border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary"
                />
              )}
            </div>
            <label className="flex items-start gap-2 rounded-md border border-emerald-100 bg-emerald-50 p-3 text-xs text-emerald-800">
              <input
                type="checkbox"
                checked={consent}
                onChange={(event) => setConsent(event.target.checked)}
                className="mt-0.5"
              />
              Patient consents to receiving a follow-up reminder on WhatsApp.
            </label>
            {error && <div className="rounded-md border border-red-100 bg-red-50 px-3 py-2 text-xs text-red-700">{error}</div>}
            <div className="flex justify-end gap-2">
              <button type="button" onClick={resetAndClose} className="px-4 py-2 text-xs font-semibold text-slate-500">
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || !phone.trim() || !followUpText.trim() || !consent}
                className="rounded-md bg-primary px-4 py-2 text-xs font-bold text-white disabled:opacity-50"
              >
                {loading ? 'Sending...' : 'Send reminder'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
