/**
 * API client for KrushiRakshak AI backend.
 * Uses the NEXT_PUBLIC_API_URL env variable set in .env.local.
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

export interface WeatherResponse {
  temperature: number;
  humidity: number;
  wind_speed: number;
  description: string;
  risk_level: "low" | "medium" | "high";
}

export interface DiseaseDetectionResponse {
  disease_name: string;
  confidence: number;
  severity: string;
  advisory: string;
  report_id?: string;
}

export interface OfficerDashboardStats {
  total_reports: number;
  high_severity_count: number;
  affected_districts: number;
  top_diseases: { name: string; count: number }[];
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

  detectDisease: (formData: FormData) =>
    fetch(`${BASE_URL}/api/farmer/detect`, { method: "POST", body: formData })
      .then((r) => r.json() as Promise<DiseaseDetectionResponse>),

  getWeather: (lat: number, lon: number) =>
    apiFetch<WeatherResponse>(`/api/farmer/weather?lat=${lat}&lon=${lon}`),

  officerDashboard: () => apiFetch<OfficerDashboardStats>("/api/officer/dashboard"),

  riskMap: (state?: string) =>
    apiFetch<{ district: string; risk_level: string; report_count: number }[]>(
      `/api/officer/risk-map${state ? `?state=${state}` : ""}`
    ),

  adminStats: () => apiFetch<AdminCommandStats>("/api/admin/stats"),

  broadcastAlert: (state: string, message: string) =>
    apiFetch<{ status: string }>(`/api/admin/alert?state=${encodeURIComponent(state)}&message=${encodeURIComponent(message)}`, { method: "POST" }),
};
