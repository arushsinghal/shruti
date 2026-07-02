import axios from 'axios';
import type {
  AudioUploadResponse,
  ConsultationSession,
  CreateSessionRequest,
  TranscribeResponse,
  ProcessClinicalResponse,
  AuditLogEntry,
  AssistantTask,
  DoctorProfile,
} from '../types/clinical';

const baseUrl = import.meta.env.VITE_API_BASE_URL || '';
export const API_BASE = baseUrl.endsWith('/api') ? baseUrl : `${baseUrl}/api`;

export function apiPath(path: string) {
  return `${API_BASE}${path}`;
}

export function getWebSocketBase() {
  const configured = import.meta.env.VITE_WS_URL;
  if (configured) return configured;

  if (API_BASE) {
    const url = new URL(API_BASE, window.location.origin);
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    return url.origin;
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}`;
}

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default client;

export async function createSession(data: CreateSessionRequest = {}): Promise<ConsultationSession> {
  const res = await client.post<ConsultationSession>('/sessions', data);
  return res.data;
}

export async function grantConsent(
  sessionId: string,
  consentMode: string = "verbal",
  consentTextVersion: string = "v1"
): Promise<ConsultationSession> {
  const res = await client.patch<ConsultationSession>(`/sessions/${sessionId}/consent`, {
    consent_mode: consentMode,
    consent_text_version: consentTextVersion
  });
  return res.data;
}

export async function getSession(id: string): Promise<ConsultationSession> {
  const res = await client.get<ConsultationSession>(`/sessions/${id}`);
  return res.data;
}

export async function listSessions(): Promise<ConsultationSession[]> {
  const res = await client.get<ConsultationSession[]>('/sessions');
  return res.data;
}

export async function uploadAudio(
  sessionId: string,
  file: File,
  onProgress?: (pct: number) => void,
): Promise<AudioUploadResponse> {
  const form = new FormData();
  form.append('file', file);
  const res = await client.post<AudioUploadResponse>(
    `/sessions/${sessionId}/audio`,
    form,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (e) => {
        if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100));
      },
    },
  );
  return res.data;
}

export async function transcribeAudio(sessionId: string, diarize = true): Promise<TranscribeResponse> {
  const res = await client.post<TranscribeResponse>(
    `/sessions/${sessionId}/transcribe?language_code=hi-IN&diarize=${diarize}&num_speakers=2`,
    null,
    { timeout: 120000 },
  );
  return res.data;
}

export async function submitTranscriptText(sessionId: string, transcript: string): Promise<TranscribeResponse> {
  const res = await client.post<TranscribeResponse>(`/sessions/${sessionId}/transcript`, { transcript });
  return res.data;
}

export async function processClinical(sessionId: string): Promise<ProcessClinicalResponse> {
  const res = await client.post<ProcessClinicalResponse>(`/sessions/${sessionId}/process-clinical`);
  return res.data;
}

export async function getFhirBundle(sessionId: string): Promise<any> {
  const res = await client.get(`/sessions/${sessionId}/fhir`);
  return res.data;
}

// ── Fact review ──────────────────────────────────────────────────────────────
export async function reviewExtractedFact(
  sessionId: string,
  factId: string,
  action: 'accept' | 'reject' | 'edit',
  value?: string,
  metadata?: Record<string, unknown>,
): Promise<ProcessClinicalResponse> {
  const res = await client.put<ProcessClinicalResponse>(`/sessions/${sessionId}/facts/${factId}`, {
    action,
    edited_value: value,
    metadata,
  });
  return res.data;
}

export async function finalizeReviewedFacts(sessionId: string): Promise<ProcessClinicalResponse> {
  const res = await client.post<ProcessClinicalResponse>(`/sessions/${sessionId}/facts/finalize`);
  return res.data;
}

export async function updateFactsAndRegenerate(
  sessionId: string,
  facts: Record<string, unknown>,
): Promise<ProcessClinicalResponse> {
  const res = await client.post<ProcessClinicalResponse>(`/sessions/${sessionId}/facts/regenerate`, {
    facts,
  });
  return res.data;
}

export async function submitExtractionFeedback(
  sessionId: string,
  category: string | { category: string; detail: string },
  original?: string,
  corrected?: string,
  feedbackType?: string,
): Promise<{ ok: boolean }> {
  const feedback =
    typeof category === 'string'
      ? { category, original, corrected, feedback_type: feedbackType }
      : category;
  const res = await client.post<{ ok: boolean }>(`/sessions/${sessionId}/extraction-feedback`, feedback);
  return res.data;
}

// ── WhatsApp ──────────────────────────────────────────────────────────────────
export async function sharePrescriptionViaWhatsapp(
  sessionId: string,
  phoneOrData: string | { phone_number: string; doctor_name?: string; consent?: boolean },
  consent?: boolean,
): Promise<{ success: boolean; provider?: string; link: string; error?: string }> {
  const data =
    typeof phoneOrData === 'string'
      ? { phone_number: phoneOrData, consent }
      : phoneOrData;
  const res = await client.post<{ success: boolean; provider?: string; link?: string; error?: string }>(
    `/sessions/${sessionId}/share-whatsapp`,
    data,
  );
  return { ...res.data, link: res.data.link || '' };
}

export async function sendFollowUpReminder(
  sessionId: string,
  phoneOrData: string | { phone_number: string; doctor_name?: string; follow_up_text: string; consent?: boolean; scheduled_for?: string },
  consent?: boolean,
  followUpText?: string,
  scheduledFor?: string,
): Promise<{ success: boolean; status: 'sent' | 'scheduled'; error?: string }> {
  const data =
    typeof phoneOrData === 'string'
      ? {
          phone_number: phoneOrData,
          consent,
          follow_up_text: followUpText || '',
          scheduled_for: scheduledFor,
        }
      : phoneOrData;
  const res = await client.post<{ success: boolean; error?: string }>(`/sessions/${sessionId}/send-follow-up`, data);
  return {
    ...res.data,
    status: data.scheduled_for ? 'scheduled' : 'sent',
  };
}

// ── Audit logs ────────────────────────────────────────────────────────────────
export async function getAuditLogs(sessionId: string): Promise<AuditLogEntry[]>;
export async function getAuditLogs(limit: number, offset: number): Promise<{ entries: AuditLogEntry[]; total: number }>;
export async function getAuditLogs(
  sessionIdOrLimit: string | number,
  offset = 0,
): Promise<AuditLogEntry[] | { entries: AuditLogEntry[]; total: number }> {
  if (typeof sessionIdOrLimit === 'number') {
    const res = await client.get<{ entries: AuditLogEntry[]; total: number }>(
      `/audit?limit=${sessionIdOrLimit}&offset=${offset}`,
    );
    return res.data;
  }
  const res = await client.get<AuditLogEntry[]>(`/sessions/${sessionIdOrLimit}/audit`);
  return res.data;
}

// ── Assistant tasks ───────────────────────────────────────────────────────────
export async function listTasks(status?: string): Promise<AssistantTask[]> {
  const params = status ? `?status=${encodeURIComponent(status)}` : '';
  const res = await client.get<AssistantTask[]>(`/tasks${params}`);
  return res.data;
}

export async function updateTask(
  taskId: string,
  update: { status?: string; notes?: string; owner?: string },
): Promise<AssistantTask> {
  const res = await client.patch<AssistantTask>(`/tasks/${taskId}`, update);
  return res.data;
}

export async function sendTaskFollowup(
  taskId: string,
  data: { phone_number: string; consent: boolean; follow_up_text: string },
): Promise<{ success: boolean; task_id: string; status: string; error?: string }> {
  const res = await client.post<{ success: boolean; task_id: string; status: string; error?: string }>(
    `/tasks/${taskId}/send-followup`,
    data,
  );
  return res.data;
}

// ── Doctor profile ────────────────────────────────────────────────────────────
export async function getDoctorProfile(): Promise<DoctorProfile> {
  const res = await client.get<DoctorProfile>('/auth/doctor-profile');
  return res.data;
}

export async function updateDoctorProfile(profile: DoctorProfile): Promise<DoctorProfile> {
  const res = await client.put<DoctorProfile>('/auth/doctor-profile', profile);
  return res.data;
}

export async function completeOnboarding(data: {
  nmc_number: string;
  specialization: string;
  clinic_name?: string;
  clinic_address?: string;
  clinic_phone?: string;
}): Promise<DoctorProfile> {
  const res = await client.put<DoctorProfile>('/auth/doctor-profile', {
    mci_number: data.nmc_number,
    clinic_name: data.clinic_name,
    clinic_address: data.clinic_address,
    clinic_phone: data.clinic_phone,
  });
  return res.data;
}

export async function verifyPublicAccess(
  token: string,
  data: { patient_name: string; initials: string; year_of_birth: string },
): Promise<{ success: boolean; download_token: string }> {
  const res = await client.post<{ success: boolean; download_token: string }>(
    `/public/verify-access/${token}`,
    data,
  );
  return res.data;
}

export async function getPublicPrescriptionHtml(downloadToken: string): Promise<string> {
  const res = await client.get<string>(`/public/download/${downloadToken}`, { responseType: 'text' });
  return res.data;
}

// ── Patient intake (assistant → doctor session) ───────────────────────────────
export async function createIntakeSession(data: {
  patient_name: string;
  patient_phone: string;
  patient_age?: string;
  patient_sex?: string;
  chief_complaint?: string;
}): Promise<ConsultationSession> {
  const res = await client.post<ConsultationSession>('/sessions/intake', data);
  return res.data;
}

export interface VoiceExtractResult {
  transcript: string;
  language_detected: string;
  is_stub: boolean;
  patient_name?: string;
  patient_age?: string;
  patient_sex?: string;
  chief_complaint?: string;
}

export async function voiceExtractIntake(audioBlob: Blob): Promise<VoiceExtractResult> {
  const form = new FormData();
  form.append('file', audioBlob, 'intake.webm');
  const res = await client.post<VoiceExtractResult>('/intake/voice-extract', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}

export async function dispatchPrescription(
  taskId: string,
  consent: boolean,
): Promise<{ success: boolean; task_id: string; status: string; link: string }> {
  const res = await client.post<{ success: boolean; task_id: string; status: string; link: string }>(
    `/tasks/${taskId}/dispatch-prescription`,
    { consent },
  );
  return res.data;
}

// ── Clinic invite / join ───────────────────────────────────────────────────────

export async function getClinicInviteCode(): Promise<{ code: string; clinic_id: string; clinic_name: string }> {
  const res = await client.get<{ code: string; clinic_id: string; clinic_name: string }>('/clinic/invite-code');
  return res.data;
}

export async function joinClinic(code: string): Promise<{ success: boolean; clinic: { id: string; name: string } }> {
  const res = await client.post<{ success: boolean; clinic: { id: string; name: string } }>('/clinic/join', { code });
  return res.data;
}

export async function getMyClinicStatus(): Promise<{ linked: boolean; clinic_id?: string; clinic_name?: string; doctor_name?: string }> {
  const res = await client.get<{ linked: boolean; clinic_id?: string; clinic_name?: string; doctor_name?: string }>('/clinic/my-clinic-status');
  return res.data;
}

export interface RevenueSummary {
  month: string;
  dhis_transactions: number;
  dhis_clinic_amount: number;
  dhis_dsc_amount: number;
  lab_dispatches_sent: number;
  follow_ups_confirmed: number;
  follow_ups_sent: number;
}

export async function getRevenueSummary(): Promise<RevenueSummary> {
  const res = await client.get<RevenueSummary>('/analytics/revenue-summary');
  return res.data;
}

export type { AuditLogEntry, ProcessClinicalResponse } from '../types/clinical';
