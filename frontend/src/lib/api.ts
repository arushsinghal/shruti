import axios from 'axios';
import type {
  AudioUploadResponse,
  ConsultationSession,
  CreateSessionRequest,
  TranscribeResponse,
  ProcessClinicalResponse,
} from '../types/clinical';

export const API_BASE = import.meta.env.VITE_API_URL || '';

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

let useOfflineMock = false;

// ---------------------------------------------------------
// LocalStorage Database Simulation
// ---------------------------------------------------------

const getMockSessions = (): ConsultationSession[] => {
  try {
    return JSON.parse(localStorage.getItem('shruti_sessions') || '[]');
  } catch {
    return [];
  }
};

const saveMockSessions = (sessions: ConsultationSession[]) => {
  localStorage.setItem('shruti_sessions', JSON.stringify(sessions));
};

const uuid = () => Math.random().toString(36).substring(2, 9);

// Default mock transcript for demoing
const DEMO_TRANSCRIPT = 
  "Patient is a 34-year-old male presenting with fever since two days. " +
  "Temperature was 38.5 C. BP is 150/90. Start paracetamol 500 mg twice daily. " +
  "Patient says he had rash with penicillin last year. " +
  "Note that allergy — penicillin allergy confirmed. " +
  "Also check CBC and CRP. Follow up in three days. " +
  "No chest pain, no vomiting. Also a headache and nausea. " +
  "Allergic to penicillin.";

// ---------------------------------------------------------
// Local NLP & Rule Engine Simulation
// ---------------------------------------------------------

function simulateLocalExtraction(transcript: string) {
  const lower = transcript.toLowerCase();
  
  // Extract Symptoms
  const symptoms: string[] = [];
  const symptomsMap: Record<string, string> = {
    fever: 'fever', bukhar: 'fever', bukhaar: 'fever',
    cough: 'cough', khasi: 'cough', khansi: 'cough',
    headache: 'headache', 'sir dard': 'headache', 'sar dard': 'headache',
    pain: 'pain', dard: 'pain',
    nausea: 'nausea', vomiting: 'vomiting', ulti: 'vomiting'
  };
  for (const [key, canonical] of Object.entries(symptomsMap)) {
    if (lower.includes(key) && !symptoms.includes(canonical)) {
      symptoms.push(canonical);
    }
  }

  // Extract Vitals
  const vitals: string[] = [];
  const bpMatch = transcript.match(/\b(\d{2,3}\s*\/\s*\d{2,3})\b/);
  if (bpMatch) vitals.push(`BP ${bpMatch[1].replace(/\s+/g, '')}`);
  
  const tempMatch = transcript.match(/\b(\d{2,3}(?:\.\d)?)\s*(?:°?\s*(?:C|F|fahrenheit|celsius))/i);
  if (tempMatch) {
    vitals.push(`Temp ${tempMatch[1]} C`);
  } else if (lower.includes('38.5')) {
    vitals.push('Temp 38.5 C');
  }

  // Extract Allergies
  const allergies: string[] = [];
  if (lower.includes('penicillin')) allergies.push('penicillin');

  // Extract Investigations
  const investigations: string[] = [];
  const invs = ['cbc', 'x-ray', 'crp', 'mri', 'ultrasound'];
  for (const inv of invs) {
    if (lower.includes(inv)) {
      investigations.push(inv === 'cbc' || inv === 'crp' ? inv.toUpperCase() : 'X-Ray');
    }
  }

  // Extract Medications
  const medications: Array<{ name: string; dosage: string; frequency: string }> = [];
  if (lower.includes('paracetamol') || lower.includes('dolo') || lower.includes('crocin')) {
    medications.push({
      name: 'paracetamol',
      dosage: '500 mg',
      frequency: 'twice daily'
    });
  }

  // Create contexts mock
  const contexts: Record<string, string> = {};
  symptoms.forEach(s => { contexts[s] = `Patient reported suffering from ${s}.`; });
  vitals.forEach(v => { contexts[v] = `Vitals recorded: ${v}.`; });
  allergies.forEach(a => { contexts[a] = `Patient reported allergy to ${a}.`; });
  medications.forEach(m => { contexts[m.name] = `Prescribed ${m.name} ${m.dosage} ${m.frequency}.`; });

  return { symptoms, vitals, allergies, investigations, medications, contexts };
}

function simulateSoapGeneration(state: any) {
  const subjective = state.symptoms.length > 0 
    ? `Patient presents with complaints of ${state.symptoms.join(', ')}. ${state.allergies.length > 0 ? `Allergies: ${state.allergies.join(', ')}.` : ''}`
    : "No subjective complaints noted.";
  const objective = state.vitals.length > 0 ? state.vitals.join(', ') : "No objective vitals recorded.";
  const assessment = state.symptoms.includes('fever') ? "Likely viral infection or pyrexia." : "Clinical presentation requiring investigation.";
  
  const planParts: string[] = [];
  if (Object.keys(state.medications).length > 0) {
    const meds = Object.entries(state.medications).map(([name, det]: any) => `${name} ${det.dosage} ${det.frequency}`);
    planParts.push(`Prescribe: ${meds.join(', ')}.`);
  }
  if (state.investigations.length > 0) {
    planParts.push(`Order: ${state.investigations.join(', ')}.`);
  }
  planParts.push("Follow up in 3 days.");
  const plan = planParts.join(' ');

  return { S: subjective, O: objective, A: assessment, P: plan };
}

function simulateCdsEngine(state: any) {
  const suggestions: any[] = [];
  
  // Allergy Check
  if (state.allergies.includes('penicillin') && (state.medications['penicillin'] || state.medications['amoxicillin'])) {
    suggestions.push({
      suggestion: "High risk: Possible allergic reaction to Penicillin class",
      rationale: "Patient has documented history of penicillin allergy.",
      urgency: "critical",
      safety_label: "drug_allergy_interaction"
    });
  }

  // Missing Dosage Check
  for (const [name, det] of Object.entries(state.medications) as any) {
    if (!det.dosage) {
      suggestions.push({
        suggestion: `Specify dosage for ${name}`,
        rationale: "Missing medication parameters can lead to clinical errors.",
        urgency: "medium",
        safety_label: "missing_parameters"
      });
    }
  }

  // BP Check
  const bpVital = state.vitals.find((v: string) => v.startsWith('BP'));
  if (bpVital && bpVital.includes('150')) {
    suggestions.push({
      suggestion: "Monitor and re-evaluate Blood Pressure",
      rationale: `Elevated systolic BP detected during consultation (${bpVital}).`,
      urgency: "high",
      safety_label: "vital_out_of_bounds"
    });
  }

  return suggestions;
}

// ---------------------------------------------------------
// API Export Methods
// ---------------------------------------------------------

export async function createSession(data: CreateSessionRequest = {}): Promise<ConsultationSession> {
  if (useOfflineMock) {
    const sessions = getMockSessions();
    const newSession: ConsultationSession = {
      id: uuid(),
      patient_name: data.patient_name || 'Anonymous Patient',
      doctor_name: data.doctor_name || '',
      cloud_ai_consent: !!data.cloud_ai_consent,
      status: 'created',
      created_at: new Date().toISOString(),
    };
    sessions.unshift(newSession);
    saveMockSessions(sessions);
    return newSession;
  }

  try {
    const res = await client.post<ConsultationSession>('/sessions', data);
    return res.data;
  } catch (e) {
    console.warn("Backend down. Falling back to offline client-side simulation.");
    useOfflineMock = true;
    return createSession(data);
  }
}

export async function getSession(id: string): Promise<ConsultationSession> {
  if (useOfflineMock) {
    const sessions = getMockSessions();
    const session = sessions.find(s => s.id === id);
    if (!session) throw new Error("Session not found");
    return session;
  }

  try {
    const res = await client.get<ConsultationSession>(`/sessions/${id}`);
    return res.data;
  } catch (e) {
    useOfflineMock = true;
    return getSession(id);
  }
}

export async function listSessions(): Promise<ConsultationSession[]> {
  if (useOfflineMock) {
    return getMockSessions();
  }

  try {
    const res = await client.get<ConsultationSession[]>('/sessions');
    return res.data;
  } catch (e) {
    console.warn("Backend down. Toggling offline-demo mode.");
    useOfflineMock = true;
    return listSessions();
  }
}

export async function uploadAudio(
  sessionId: string,
  file: File,
  onProgress?: (pct: number) => void,
): Promise<AudioUploadResponse> {
  if (useOfflineMock) {
    if (onProgress) {
      onProgress(50);
      setTimeout(() => onProgress(100), 200);
    }
    const sessions = getMockSessions();
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      session.status = 'audio_uploaded';
      session.audio_file_path = file.name;
      saveMockSessions(sessions);
    }
    return { session_id: sessionId, file_path: file.name, status: 'audio_uploaded' };
  }

  const form = new FormData();
  form.append('file', file);
  try {
    const res = await axios.post<AudioUploadResponse>(
      `${API_BASE}/sessions/${sessionId}/audio`,
      form,
      {
        onUploadProgress: (e) => {
          if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100));
        },
      },
    );
    return res.data;
  } catch (e) {
    useOfflineMock = true;
    return uploadAudio(sessionId, file, onProgress);
  }
}

export async function transcribeAudio(sessionId: string): Promise<TranscribeResponse> {
  if (useOfflineMock) {
    const sessions = getMockSessions();
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      session.status = 'transcribed';
      session.transcript = DEMO_TRANSCRIPT;
      (session as any).diarized_transcript = "Doctor: Patient ko bukhar hai? \nPatient: Haan, do din se hai.";
      saveMockSessions(sessions);
    }
    return {
      transcript: DEMO_TRANSCRIPT,
      language_detected: 'hi-IN',
      is_stub: true,
      diarized_transcript: "Doctor: Patient ko bukhar hai? \nPatient: Haan, do din se hai."
    };
  }

  try {
    const res = await client.post<TranscribeResponse>(`/sessions/${sessionId}/transcribe`);
    return res.data;
  } catch (e) {
    useOfflineMock = true;
    return transcribeAudio(sessionId);
  }
}

export async function submitTranscriptText(sessionId: string, transcript: string): Promise<TranscribeResponse> {
  if (useOfflineMock) {
    const sessions = getMockSessions();
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      session.status = 'transcribed';
      session.transcript = transcript;
      saveMockSessions(sessions);
    }
    return {
      transcript,
      language_detected: 'en',
      is_stub: false,
    };
  }

  try {
    const res = await client.post<TranscribeResponse>(`/sessions/${sessionId}/transcript`, { transcript });
    return res.data;
  } catch (e) {
    useOfflineMock = true;
    return submitTranscriptText(sessionId, transcript);
  }
}

export async function processClinical(sessionId: string): Promise<ProcessClinicalResponse> {
  if (useOfflineMock) {
    const sessions = getMockSessions();
    const session = sessions.find(s => s.id === sessionId);
    if (!session || !session.transcript) throw new Error("No transcript found to process");

    const extraction = simulateLocalExtraction(session.transcript);
    
    // Map medications to expected state format
    const medicationsState: Record<string, any> = {};
    extraction.medications.forEach(m => {
      medicationsState[m.name] = { dosage: m.dosage, frequency: m.frequency };
    });

    const state = {
      symptoms: extraction.symptoms,
      medications: medicationsState,
      vitals: extraction.vitals,
      allergies: extraction.allergies,
      investigations: extraction.investigations,
      contexts: extraction.contexts
    };

    const soap = simulateSoapGeneration(state);
    const cds = simulateCdsEngine(state);

    session.status = 'complete';
    session.clinical_facts = extraction as any;
    session.memory_state = state as any;
    session.soap_note = soap as any;
    session.cds_suggestions = cds;
    saveMockSessions(sessions);

    return {
      facts: extraction as any,
      state: state as any,
      soap: soap,
      cds: cds,
      source: 'fallback'
    };
  }

  try {
    const res = await client.post<ProcessClinicalResponse>(`/sessions/${sessionId}/process-clinical`);
    return res.data;
  } catch (e) {
    useOfflineMock = true;
    return processClinical(sessionId);
  }
}

export async function getFhirBundle(sessionId: string): Promise<any> {
  if (useOfflineMock) {
    const session = await getSession(sessionId);
    if (!session.memory_state) throw new Error("Clinical facts not processed");
    
    const state = session.memory_state as any;
    const nowStr = new Date().toISOString();
    const patientId = `pat-${sessionId.substring(0, 8)}`;
    const encounterId = `enc-${sessionId.substring(0, 8)}`;

    const entries: any[] = [
      {
        fullUrl: `urn:uuid:${patientId}`,
        resource: {
          resourceType: "Patient",
          id: patientId,
          name: [{ text: session.patient_name || "Anonymous Patient", use: "official" }],
          active: true
        }
      },
      {
        fullUrl: `urn:uuid:${encounterId}`,
        resource: {
          resourceType: "Encounter",
          id: encounterId,
          status: "finished",
          class: { system: "http://terminology.hl7.org/CodeSystem/v3-ActCode", code: "AMB", display: "ambulatory" },
          subject: { reference: `urn:uuid:${patientId}` },
          period: { start: nowStr }
        }
      }
    ];

    state.symptoms.forEach((symptom: string) => {
      entries.push({
        fullUrl: `urn:uuid:${Math.random().toString(36).substring(7)}`,
        resource: {
          resourceType: "Condition",
          clinicalStatus: { coding: [{ system: "http://terminology.hl7.org/CodeSystem/condition-clinical", code: "active" }] },
          code: { text: symptom },
          subject: { reference: `urn:uuid:${patientId}` }
        }
      });
    });

    return {
      resourceType: "Bundle",
      id: Math.random().toString(36).substring(7),
      type: "document",
      timestamp: nowStr,
      entry: entries
    };
  }

  try {
    const res = await client.get(`/sessions/${sessionId}/fhir`);
    return res.data;
  } catch (e) {
    useOfflineMock = true;
    return getFhirBundle(sessionId);
  }
}
