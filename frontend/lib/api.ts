/**
 * API Client for KrushiRakshak AI Next.js Frontend.
 * Connects to FastAPI backend endpoints.
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ─── Types ────────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
  db_connected: boolean;
}

export interface TopPrediction {
  label: string;
  confidence: number;
}

export interface ScanResponse {
  label: string;
  confidence: number;
  top3: TopPrediction[];
  severity_estimate: number;
  severity_pct: number;
  gradcam_image_base64: string;
  low_confidence: boolean;
}

export interface RiskWhyFactor {
  factor: string;
  details: string;
  impact_score: number;
}

export interface RiskForecastDay {
  day: string;
  date: string;
  predicted_risk_score: number;
  risk_level: string;
  temp_max: number;
  rain_mm: number;
}

export interface RiskScoreResponse {
  crop_id: string;
  overall_score: number;
  risk_level: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  disease_risk: number;
  pest_risk: number;
  weather_risk: number;
  why: RiskWhyFactor[];
  forecast: RiskForecastDay[];
}

export interface AdvisoryTreatments {
  chemical: string[];
  organic: string[];
  cultural: string[];
}

export interface AdvisoryResponse {
  disease_label: string;
  disease_name_formatted: str;
  severity_pct: number;
  severity_category: string;
  crop_name: string;
  growth_stage: string;
  language: string;
  treatments: AdvisoryTreatments;
  urgency_level: string;
}

export interface OfficerDashboardStats {
  total_reports: number;
  high_severity_count: number;
  affected_districts: number;
  top_diseases: { name: string; count: number }[];
}

export interface DistrictRiskMapItem {
  district: string;
  total_farms: number;
  high_risk_crops: number;
  avg_risk_score: number;
  risk_level: string;
}

export interface ValidationItem {
  ai_result_id: string;
  observation_id: string;
  disease_label: string;
  confidence: number;
  severity_pct: number;
  image_urls: string[];
  crop_name: string;
  farm_name: string;
  district: string;
  timestamp: string;
  is_validated: boolean;
}

export interface AdminCommandStats {
  total_farmers: number;
  total_reports: number;
  states_covered: number;
  model_accuracy: number;
  alerts_issued: number;
}

// ─── Endpoints ────────────────────────────────────────────────────────────────

export const api = {
  health: () => apiFetch<HealthResponse>("/api/health"),

  scanImage: (formData: FormData) =>
    fetch(`${BASE_URL}/api/scan`, { method: "POST", body: formData }).then((r) => {
      if (!r.ok) throw new Error(`Scan failed: ${r.statusText}`);
      return r.json() as Promise<ScanResponse>;
    }),

  getRiskScore: (cropId: string) =>
    apiFetch<RiskScoreResponse>("/api/risk-score", {
      method: "POST",
      body: JSON.stringify({ crop_id: cropId }),
    }),

  getAdvisory: (diseaseLabel: string, severityPct: number, languagePref: string = "en") =>
    apiFetch<AdvisoryResponse>("/api/advisory", {
      method: "POST",
      body: JSON.stringify({
        disease_label: diseaseLabel,
        severity_pct: severityPct,
        language_pref: languagePref,
      }),
    }),

  officerDashboard: () => apiFetch<OfficerDashboardStats>("/api/officer/dashboard"),

  riskMap: (state: string = "Maharashtra") =>
    apiFetch<DistrictRiskMapItem[]>(`/api/officer/risk-map?state=${encodeURIComponent(state)}`),

  getValidations: () => apiFetch<ValidationItem[]>("/api/officer/validations"),

  submitValidation: (aiResultId: string, officerId: string, verdict: string, correctedLabel?: string, notes?: string) =>
    apiFetch<{ id: string; verdict: string }>("/api/officer/validate", {
      method: "POST",
      body: JSON.stringify({
        ai_result_id: aiResultId,
        officer_id: officerId,
        verdict,
        corrected_label: correctedLabel,
        notes,
      }),
    }),

  adminStats: () => apiFetch<AdminCommandStats>("/api/admin/stats"),

  broadcastAlert: (title: string, message: string, level: string = "warning", targetState: string = "Maharashtra") =>
    apiFetch<{ status: string; alert_id: string }>("/api/admin/alert", {
      method: "POST",
      body: JSON.stringify({ title, message, level, target_state: targetState }),
    }),
};
