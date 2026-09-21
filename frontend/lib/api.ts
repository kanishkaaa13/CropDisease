/**
 * API Client for KrushiRakshak AI Next.js Frontend.
 * Connects to FastAPI backend endpoints.
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 12000);
  
  // Add auth token if available
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  const headers: HeadersInit = { "Content-Type": "application/json", ...options?.headers };
  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }
  
  try {
    const res = await fetch(url, {
      headers,
      ...options,
      signal: options?.signal ?? controller.signal,
    });
    if (!res.ok) {
      // Handle 401 - clear session and redirect to login
      if (res.status === 401 && typeof window !== 'undefined') {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        window.location.href = '/login';
        throw new Error('Session expired');
      }
      const text = await res.text();
      throw new Error(`API error ${res.status}: ${text}`);
    }
    return res.json() as Promise<T>;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("The backend request timed out. Check that the API is running and try again.");
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
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
  disease_key?: string;
  localized_label?: string;
}

export interface ScanResponse {
  label: string;
  scan_id?: string;
  disease_key?: string;
  localized_label?: string;
  confidence: number;
  top3: TopPrediction[];
  severity_estimate: number;
  severity_pct: number;
  gradcam_image_base64: string;
  low_confidence: boolean;
  status_key?: string;
  severity_key?: string;
  language?: string;
}

export interface CropRiskPrediction {
  risk_level: string;
  score: number;
  factors: { name: string; value: number; detail: string }[];
  actions: string[];
  forecast: { day: string; date: string; predicted_risk_score: number; risk_level: string; temp_max: number; rain_mm: number }[];
  weather: { temperature: number; humidity: number; precipitation: number; wind_speed: number; risk: number };
}

export interface RiskWhyFactor {
  factor: string;
  details: string;
  impact_score: number;
  factor_key?: string;
}

export interface RiskForecastDay {
  day: string;
  date: string;
  predicted_risk_score: number;
  risk_level: string;
  risk_level_key?: string;
  temp_max: number;
  rain_mm: number;
}

export interface RiskScoreResponse {
  crop_id: string;
  overall_score: number;
  risk_level: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  risk_level_key?: string;
  language?: string;
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
  advisory_key?: string;
  disease_key?: string;
  crop_key?: string;
  language?: string;
}

export interface AssistantAskResponse {
  answer: string;
  language: string;
  source: string;
  spoken: boolean;
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

export interface AdminHotspot {
  name: string;
  lat: number;
  lng: number;
  district: string;
  climate_zone: string;
  risk_level: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  dominant_disease_or_pest: string;
  scan_count: number;
  trend_data: number[];
  source: "real" | "seeded" | "none";
}

export interface OfficerQueueItem {
  ai_result_id: string;
  observation_id: string;
  disease_label: string;
  confidence: number;
  severity_pct: number;
  image_urls: string[];
  heat_map_url?: string | null;
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

export interface AdminSummary {
  total_monitored_farms: number;
  active_alerts: number;
  high_risk_villages: number;
  disease_outbreaks_detected: number;
  pending_expert_validations: number;
}

export interface DistrictAnalytics {
  district: string;
  dominant_crop: string;
  dominant_threat: string;
  risk_score: number;
  case_count: number;
  farm_count: number;
}

export interface Outbreak {
  village: string;
  district: string;
  taluka: string;
  crop: string;
  disease: string;
  current_week_cases: number;
  previous_week_cases: number;
  growth_pct: number;
  risk_level: string;
}

export interface RiskTrendData {
  date: string;
  avg_risk_score: number;
  case_count: number;
}

export interface ValidationSubmission {
  ai_result_id: string;
  officer_id: string;
  verdict: "confirmed" | "corrected" | "referred";
  corrected_label?: string;
  notes?: string;
}

export interface ChatMessage {
  id: string;
  conversation_id: string;
  sender_id: string;
  sender_role: "farmer" | "officer" | string;
  body: string;
  attachment_url?: string | null;
  lang: string;
  created_at: string;
  read_at?: string | null;
}

export interface ChatConversation {
  id: string;
  farm_id: string;
  farmer_id: string;
  officer_id: string;
  scan_id?: string | null;
  status: "open" | "closed" | string;
  created_at: string;
  unread_count: number;
  last_message?: ChatMessage | null;
  scan_label?: string | null;
  scan_image_url?: string | null;
  heat_map_url?: string | null;
}

export interface ChatPage {
  items: ChatMessage[];
  total: number;
  offset: number;
  limit: number;
}

// ─── Auth Types ───────────────────────────────────────────────────────────────

export interface User {
  id: string;
  full_name: string;
  email: string;
  phone: string | null;
  role: "farmer" | "officer" | "admin";
  district: string | null;
  preferred_language: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RegisterRequest {
  full_name: string;
  email: string;
  password: string;
  phone?: string;
  role: "farmer" | "officer";
  district?: string;
  preferred_language: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

// ─── Endpoints ────────────────────────────────────────────────────────────────

export const api = {
  health: () => apiFetch<HealthResponse>("/api/health"),

  scanImage: (formData: FormData, language: string = "en", signal?: AbortSignal) =>
    fetch(`${BASE_URL}/api/scan?lang=${encodeURIComponent(language)}`, { method: "POST", body: formData, signal }).then((r) => {
      if (!r.ok) throw new Error(`Scan failed: ${r.statusText}`);
      return r.json() as Promise<ScanResponse>;
    }),

  getRiskScore: (cropId: string, language: string = "en") =>
    apiFetch<RiskScoreResponse>(`/api/risk-score?lang=${encodeURIComponent(language)}`, {
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

  askAssistant: (question: string, lang: string, context?: { disease_label?: string; crop_name?: string; severity_pct?: number }) =>
    apiFetch<AssistantAskResponse>("/api/assistant/ask", {
      method: "POST",
      body: JSON.stringify({ question, lang, ...context }),
    }),

  getWeather: (lat: number, lon: number) =>
    apiFetch<{ temperature: number; humidity: number; description: string; risk_level: string }>(`/api/farmer/weather?lat=${lat}&lon=${lon}`),

  predictRisk: (payload: { district: string; crop: string; sowing_date?: string; soil_type: string; temperature: number; humidity: number; rainfall: number; soil_ph: number; latitude?: number; longitude?: number }) =>
    apiFetch<CropRiskPrediction>("/api/predict/risk", { method: "POST", body: JSON.stringify(payload) }),

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

  submitValidation: (payload: ValidationSubmission) =>
    apiFetch<{ message: string }>("/api/officer/validate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  adminStats: () => apiFetch<AdminCommandStats>("/api/admin/stats"),

  broadcastAlert: (title: string, message: string, level: string = "warning", targetState: string = "Maharashtra") =>
    apiFetch<{ status: string; alert_id: string }>("/api/admin/alert", {
      method: "POST",
      body: JSON.stringify({ title, message, level, target_state: targetState }),
    }),

  // Admin endpoints
  adminSummary: () => apiFetch<AdminSummary>("/api/admin/summary"),

  adminDistrictAnalytics: (state: string = "Maharashtra", sortBy: string = "risk_score", sortOrder: string = "desc") =>
    apiFetch<DistrictAnalytics[]>(`/api/admin/district-analytics?state=${encodeURIComponent(state)}&sort_by=${sortBy}&sort_order=${sortOrder}`),

  adminOutbreaks: (growthThreshold: number = 30.0) =>
    apiFetch<Outbreak[]>(`/api/admin/outbreaks?growth_threshold=${growthThreshold}`),

  adminRiskTrend: (state: string = "Maharashtra", days: number = 30) =>
    apiFetch<RiskTrendData[]>(`/api/admin/risk-trend?state=${encodeURIComponent(state)}&days=${days}`),

  adminHotspots: () => apiFetch<AdminHotspot[]>("/api/admin/hotspots"),

  // Farmer endpoints
  getFarmerFarms: (farmerId: string) =>
    apiFetch<any[]>(`/api/farmer/farms/${encodeURIComponent(farmerId)}`),

  getFarmerReports: (farmerId: string) =>
    apiFetch<any[]>(`/api/farmer/reports/${encodeURIComponent(farmerId)}`),

  registerFarmer: (data: { name: string; phone: string; district?: string; state?: string }) =>
    apiFetch<any>("/api/farmer/register", { method: "POST", body: JSON.stringify(data) }),

  createFarm: (data: any) =>
    apiFetch<any>("/api/farmer/farms", { method: "POST", body: JSON.stringify(data) }),

  createCrop: (data: any) =>
    apiFetch<any>("/api/farmer/crops", { method: "POST", body: JSON.stringify(data) }),

  listConversations: (userId: string) =>
    apiFetch<ChatConversation[]>(`/api/chat/conversations?user_id=${encodeURIComponent(userId)}`),

  createConversation: (userId: string, data: { farm_id: string; officer_id: string; scan_id?: string }) =>
    apiFetch<ChatConversation>(`/api/chat/conversations?user_id=${encodeURIComponent(userId)}`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getMessages: (userId: string, conversationId: string, offset = 0, limit = 50) =>
    apiFetch<ChatPage>(`/api/chat/conversations/${encodeURIComponent(conversationId)}/messages?user_id=${encodeURIComponent(userId)}&offset=${offset}&limit=${limit}`),

  sendChatMessage: (userId: string, conversationId: string, data: { body: string; attachment_url?: string; lang?: string }) =>
    apiFetch<ChatMessage>(`/api/chat/conversations/${encodeURIComponent(conversationId)}/messages?user_id=${encodeURIComponent(userId)}`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  markChatRead: (userId: string, conversationId: string) =>
    apiFetch<{ marked_read: number }>(`/api/chat/conversations/${encodeURIComponent(conversationId)}/read?user_id=${encodeURIComponent(userId)}`, { method: "POST" }),

  uploadChatAttachment: (userId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return fetch(`${BASE_URL}/api/chat/attachments?user_id=${encodeURIComponent(userId)}`, { method: "POST", body: formData }).then(async (response) => {
      if (!response.ok) throw new Error(await response.text());
      return response.json() as Promise<{ attachment_url: string }>;
    });
  },

  chatWebSocketUrl: (conversationId: string, userId: string) => {
    const url = new URL(BASE_URL);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    url.pathname = `/ws/chat/${encodeURIComponent(conversationId)}`;
    url.searchParams.set("user_id", userId);
    return url.toString();
  },

  // Auth endpoints
  register: (data: RegisterRequest) => {
    const formData = new URLSearchParams();
    formData.append("full_name", data.full_name);
    formData.append("email", data.email);
    formData.append("password", data.password);
    if (data.phone) formData.append("phone", data.phone);
    formData.append("role", data.role);
    if (data.district) formData.append("district", data.district);
    formData.append("preferred_language", data.preferred_language);
    
    return fetch(`${BASE_URL}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }).then(async (r) => {
      if (!r.ok) {
        const text = await r.text();
        throw new Error(text || "Registration failed");
      }
      return r.json() as Promise<AuthResponse>;
    });
  },

  login: (data: LoginRequest) => {
    const formData = new URLSearchParams();
    formData.append("username", data.username);
    formData.append("password", data.password);
    
    return fetch(`${BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData,
    }).then(async (r) => {
      if (!r.ok) {
        const text = await r.text();
        throw new Error(text || "Login failed");
      }
      return r.json() as Promise<AuthResponse>;
    });
  },

  getMe: () => apiFetch<User>("/api/auth/me"),

  logout: () => apiFetch<{ message: string }>("/api/auth/logout", { method: "POST" }),
};

