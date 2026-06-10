export type SessionStatus =
  | 'created'
  | 'audio_uploaded'
  | 'transcribed'
  | 'extracted'
  | 'memory_resolved'
  | 'soap_ready'
  | 'complete';

export interface ClinicalFact {
  id: string;
  category: string;
  value: string;
  status: 'active' | 'superseded' | 'uncertain' | 'negated';
  confidence: number;
  source_text: string;
  timestamp_order: number;
  supersedes?: string;
  requires_confirmation: boolean;
}

export interface MedicationHistory {
  dose?: string;
  route?: string;
  frequency?: string;
  duration?: string;
  timing?: string;
  status: string;
  changed_at: string;
  reason?: string;
}

export interface Medication {
  name: string;
  dose?: string;
  route?: string;
  frequency?: string;
  duration?: string;
  timing?: string;
  indication?: string;
  status: 'active' | 'superseded' | 'uncertain' | 'negated';
  source_text: string;
  history: MedicationHistory[];
}

export interface MemoryState {
  active_facts: ClinicalFact[];
  superseded_facts: ClinicalFact[];
  uncertain_facts: ClinicalFact[];
  unresolved_references: string[];
  audit_trail: Record<string, unknown>[];
}

export interface SOAPSubjective {
  chief_complaint?: string;
  hpi?: string;
  symptoms: string[];
  allergies: string[];
  current_medications: Medication[];
}

export interface SOAPObjective {
  vitals: Record<string, string>;
  exam?: string;
  labs: string[];
  imaging: string[];
}

export interface SOAPAssessment {
  diagnosis?: string;
  differentials: string[];
  impression?: string;
  severity?: string;
}

export interface SOAPPlan {
  medications: Medication[];
  investigations: string[];
  lifestyle: string[];
  follow_up?: string;
  red_flags: string[];
  referrals: string[];
}

export interface SOAPNote {
  subjective: SOAPSubjective;
  objective: SOAPObjective;
  assessment: SOAPAssessment;
  plan: SOAPPlan;
}

export interface CDSSuggestion {
  suggestion: string;
  rationale: string;
  urgency: 'low' | 'medium' | 'high' | 'critical';
  evidence_from_transcript: string[];
  safety_label: 'doctor_review_required';
}

export interface ConsultationSession {
  id: string;
  patient_name?: string;
  doctor_name?: string;
  created_at: string;
  cloud_ai_consent: boolean;
  status: SessionStatus;
  audio_file_path?: string;
  transcript?: string;
  clinical_facts?: ClinicalFact[];
  memory_state?: MemoryState;
  soap_note?: SOAPNote;
  cds_suggestions?: CDSSuggestion[];
}

export interface CreateSessionRequest {
  patient_name?: string;
  doctor_name?: string;
  cloud_ai_consent?: boolean;
}

export interface AudioUploadResponse {
  session_id: string;
  file_path: string;
  status: string;
}

export interface TranscribeResponse {
  transcript: string;
  language_detected: string;
  is_stub: boolean;
  diarized_transcript?: string;
}

export interface DeterministicMedication {
  name: string;
  dosage: string;
  frequency: string;
}

export interface DeterministicFacts {
  symptoms: string[];
  medications: DeterministicMedication[];
  vitals: string[];
  allergies: string[];
  investigations: string[];
}

export interface DeterministicState {
  symptoms: string[];
  medications: Record<string, Omit<DeterministicMedication, 'name'>>;
  vitals: string[];
  allergies: string[];
  investigations: string[];
  contexts: Record<string, string>;
}

export interface DeterministicSOAP {
  S: string;
  O: string;
  A: string;
  P: string;
}

export interface DeterministicCDS {
  suggestion: string;
  rationale: string;
  urgency: 'low' | 'medium' | 'high' | 'critical';
  safety_label: string;
}

export interface ProcessClinicalResponse {
  facts: DeterministicFacts;
  state: DeterministicState;
  soap: DeterministicSOAP;
  cds: DeterministicCDS[];
  source?: string;
}
