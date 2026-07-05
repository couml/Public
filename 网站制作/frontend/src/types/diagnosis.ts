export interface DiagnosisSession {
  id: string;
  user_id: string;
  printer_id: string | null;
  session_title: string;
  status: 'active' | 'resolved' | 'closed';
  error_codes: string[];
  resolution_summary: string | null;
  created_at: string;
  updated_at: string;
  messages?: DiagnosisMessage[];
}

export interface DiagnosisMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  message: string;
  diagnosis_result: DiagnosisResult | null;
  sources: string[];
  step_number: number | null;
  created_at: string;
}

export interface DriverRecommendation {
  os: string;
  version: string;
  id: string;
}

export interface PrinterContext {
  brand: string;
  model: string;
  status: string;
  toner_level: number;
  paper_level: number;
  latest_error_code: string | null;
  latest_error_message: string | null;
}

export interface DiagnosisResult {
  fault_type: string;
  root_cause: string;
  severity: 'info' | 'warning' | 'critical';
  steps: string[];
  parts: string[];
  safety: string[];
  confidence: number;
  driver_recommendations?: DriverRecommendation[];
  printer_context?: PrinterContext;
  diagnosis_method?: string;
}
