import axios from 'axios';
import type {
  AudioUploadResponse,
  ConsultationSession,
  CreateSessionRequest,
  TranscribeResponse,
  ProcessClinicalResponse,
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
