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
  disease_name_formatted: string;
  severity_pct: number;
  severity_category: string;
  crop_name: string;
  growth_stage: string;
  language: string;
  treatments: AdvisoryTreatments;
  urgency_level: string;
}

export interface RAGAdvisoryResponse {
  advisory: {
    en: { summary: string; action_steps: string[] };
    hi: { summary: string; action_steps: string[] };
    mr: { summary: string; action_steps: string[] };
  };
  match_confidence: string;
  kb_entry_found: boolean;
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

export interface RiskHotspot {
  cluster_id: string | number;
  district: string;
  taluka: string;
  village: string;
  center_lat: number;
  center_lng: number;
  farm_count: number;
  crop_count: number;
  avg_risk_score: number;
  case_count: number;
  dominant_disease: string;
  risk_level: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
}

export interface OfficerQueueItem {
  ai_result_id: string;
  observation_id: string;
  disease_label: string;
  confidence: number;
  severity_pct: number;
  image_urls: string[];
  crop_name: string;
  crop_id: string | null;
  farm_name: string;
  farm_id: string | null;
  district: string;
  taluka: string;
  village: string;
  gps_lat: number | null;
  gps_lng: number | null;
  distance_km: number;
  risk_level: string;
  risk_score: number;
  priority_score: number;
  timestamp: string;
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

  getRAGAdvisory: (cropId: string, aiResultId: string) =>
    apiFetch<RAGAdvisoryResponse>("/api/advisory", {
      method: "POST",
      body: JSON.stringify({
        crop_id: cropId,
        ai_result_id: aiResultId,
      }),
    }),

  officerDashboard: () => apiFetch<OfficerDashboardStats>("/api/officer/dashboard"),

  riskMap: (state: string = "Maharashtra") =>
    apiFetch<DistrictRiskMapItem[]>(`/api/officer/risk-map?state=${encodeURIComponent(state)}`),

  getValidations: () => apiFetch<ValidationItem[]>("/api/officer/validations"),

  getHotspots: (state: string = "Maharashtra", clusterRadiusKm: number = 10.0) =>
    apiFetch<RiskHotspot[]>(`/api/officer/hotspots?state=${encodeURIComponent(state)}&cluster_radius_km=${clusterRadiusKm}`),

  getOfficerQueue: (officerLat?: number, officerLng?: number, limit: number = 50) => {
    const params = new URLSearchParams();
    if (officerLat !== undefined) params.append("officer_lat", officerLat.toString());
    if (officerLng !== undefined) params.append("officer_lng", officerLng.toString());
    params.append("limit", limit.toString());
    return apiFetch<OfficerQueueItem[]>(`/api/officer/queue?${params.toString()}`);
  },

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
