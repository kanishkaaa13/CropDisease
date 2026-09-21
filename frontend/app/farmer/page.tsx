"use client";

import { useState, useRef, useEffect } from "react";
import { api, type ScanResponse, type RiskScoreResponse, type AdvisoryResponse } from "@/lib/api";
import { detectBlur } from "@/lib/blurDetection";
import FarmCard from "@/components/farmer/FarmCard";
import { useI18n } from "@/lib/i18n";
import ChatPanel from "@/components/ChatPanel";
import VoiceAssistant, { speakText } from "@/components/VoiceAssistant";
import type { VoiceIntent } from "@/lib/voiceIntents";
import GovResourceLinks from "@/components/GovResourceLinks";

type Screen = "home" | "scan" | "result" | "alerts";

interface Farm {
  id: string;
  name: string;
  cropName: string;
  healthScore: number;
  riskLevel: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  lastScanDate: string | null;
  lastSeverityPct: number | null;
  needsFollowUp: boolean;
  gpsLat?: number;
  gpsLng?: number;
}

interface Alert {
  id: string;
  farmName: string;
  cropName: string;
  disease: string;
  riskLevel: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  timestamp: string;
  severityPct: number;
}

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिंदी (Beta)" },
  { code: "mr", label: "मराठी (Beta)" },
];

export default function FarmerPage() {
  const { locale, t } = useI18n();
  const [screen, setScreen] = useState<Screen>("home");
  const [selectedFarm, setSelectedFarm] = useState<Farm | null>(null);
  const [selectedLang, setSelectedLang] = useState<string>(locale);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null);
  const [riskResult, setRiskResult] = useState<RiskScoreResponse | null>(null);
  const [advisory, setAdvisory] = useState<AdvisoryResponse | null>(null);
  const [showGradCAM, setShowGradCAM] = useState(true);
  const [showWhy, setShowWhy] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [voiceMessage, setVoiceMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [blurError, setBlurError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // Dynamic state loaded from backend API
  const [farms, setFarms] = useState<Farm[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [farmerId, setFarmerId] = useState<string>("seed-farmer-1");
  const [fetchingData, setFetchingData] = useState<boolean>(true);
  const [showAddFarmModal, setShowAddFarmModal] = useState<boolean>(false);
  const [newFarmName, setNewFarmName] = useState("");
  const [newCropType, setNewCropType] = useState("Tomato");
  const [newVillage, setNewVillage] = useState("Nashik");

  useEffect(() => {
    async function loadData() {
      try {
        setFetchingData(true);
        const remoteFarms = await api.getFarmerFarms(farmerId);
        if (remoteFarms && remoteFarms.length > 0) {
          setFarms(remoteFarms.map((f: any) => ({
            id: f.id,
            name: f.name,
            cropName: f.crop_name || "Tomato",
            healthScore: 85,
            riskLevel: "LOW",
            lastScanDate: f.created_at ? f.created_at.slice(0, 10) : null,
            lastSeverityPct: null,
            needsFollowUp: false,
            gpsLat: f.gps_lat,
            gpsLng: f.gps_lng,
          })));
        } else {
          // If no farms registered yet in DB, default to empty state
          setFarms([]);
        }

        const reports = await api.getFarmerReports(farmerId);
        if (reports && reports.length > 0) {
          setAlerts(reports.map((r: any) => ({
            id: r.report_id,
            farmName: "My Field",
            cropName: r.crop_type,
            disease: r.disease_name || "Observation",
            riskLevel: r.severity && parseFloat(r.severity) > 50 ? "HIGH" : "LOW",
            timestamp: r.created_at,
            severityPct: r.severity && parseFloat(r.severity) ? parseFloat(r.severity) : 20,
          })));
        }
      } catch (err) {
        console.warn("Could not fetch remote farms/alerts:", err);
      } finally {
        setFetchingData(false);
      }
    }
    loadData();
  }, [farmerId]);

  useEffect(() => {
    setSelectedLang(locale);
  }, [locale]);

  async function handleVoiceIntent(intent: VoiceIntent) {
    if (intent === "scan_crop") {
      if (selectedFarm) setScreen("scan");
      else setVoiceMessage("Select a farm first, then say scan my crop.");
    } else if (intent === "show_farms") {
      setScreen("home");
    } else if (intent === "talk_officer") {
      if (selectedFarm || farms[0]) {
        if (!selectedFarm) setSelectedFarm(farms[0]);
        setShowChat(true);
        if (scanResult) setScreen("result");
      } else {
        setVoiceMessage("Register a farm before contacting an officer.");
      }
    } else if (intent === "weather") {
      const farm = selectedFarm || farms[0];
      if (!farm) {
        setVoiceMessage("Register a farm to hear its weather.");
        return;
      }
      try {
        const weather = await api.getWeather(farm.gpsLat ?? 19.9975, farm.gpsLng ?? 73.7898);
        speakText(`${weather.description}. Temperature ${weather.temperature} degrees. Humidity ${weather.humidity} percent.`, locale, () => setVoiceMessage("No matching voice found; using the browser default voice."));
      } catch {
        setVoiceMessage("Weather is temporarily unavailable.");
      }
    }
  }

  const voiceAssistant = (
    <VoiceAssistant
      lastResultText={scanResult ? `${scanResult.localized_label || scanResult.label}. Severity ${scanResult.severity_pct} percent. ${advisory?.treatments.cultural?.[0] || "Please monitor the crop and contact an officer if symptoms worsen."}` : undefined}
      diseaseLabel={scanResult?.label}
      cropName={selectedFarm?.cropName}
      severityPct={scanResult?.severity_pct}
      onIntent={handleVoiceIntent}
    />
  );


  function handleScanCrop(farm: Farm) {
    setSelectedFarm(farm);
    setScreen("scan");
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    setImageFile(f);
    setImagePreview(URL.createObjectURL(f));
    setScanResult(null);
    setRiskResult(null);
    setAdvisory(null);
    setError(null);
    setBlurError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!imageFile) {
      setError("Please select a crop leaf image.");
      return;
    }

    // Blur detection
    setLoading(true);
    setLoadingStep("Checking image quality...");
    
    try {
      const blurResult = await detectBlur(imageFile);
      if (blurResult.isBlurry) {
        setBlurError("Image is too blurry. Please take a clearer photo and try again.");
        setLoading(false);
        return;
      }
    } catch (blurErr) {
      console.warn("Blur detection failed, proceeding:", blurErr);
    }

    try {
      const fd = new FormData();
      fd.append("file", imageFile);
      if (selectedFarm) {
        fd.append("farmer_id", farmerId);
        fd.append("crop_id", selectedFarm.id);
      }

      // 1. Scan image with AI classifier + Grad-CAM + HSV severity
      setLoadingStep("Analyzing leaf with AI...");
      const scanRes = await api.scanImage(fd, selectedLang);
      setScanResult(scanRes);

      // 2. Get risk score
      if (selectedFarm) {
        setLoadingStep("Calculating risk score...");
        try {
          const riskRes = await api.getRiskScore(selectedFarm.id, selectedLang);
          setRiskResult(riskRes);
        } catch (riskErr) {
          console.warn("Risk score failed, continuing:", riskErr);
        }
      }

      // 3. Fetch multilingual advisory action plan
      setLoadingStep("Generating treatment advice...");
      const advRes = await api.getAdvisory(scanRes.label, scanRes.severity_pct, selectedLang);
      setAdvisory(advRes);

      setScreen("result");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Diagnostic scan failed. Please try again.");
    } finally {
      setLoading(false);
      setLoadingStep("");
    }
  }

  async function handleCreateFarm(e: React.FormEvent) {
    e.preventDefault();
    if (!newFarmName.trim()) return;
    try {
      setLoading(true);
      const createdFarm = await api.createFarm({
        owner_id: farmerId,
        name: newFarmName,
        village: newVillage || "Nashik",
        taluka: "Nashik",
        district: "Nashik",
        state: "Maharashtra",
        gps_lat: 19.9975,
        gps_lng: 73.7898,
        area_acres: 2.5,
      });

      let cropName = newCropType;
      try {
        const createdCrop = await api.createCrop({
          farm_id: createdFarm.id,
          crop_type: newCropType,
          sowing_date: new Date().toISOString(),
          stage: "vegetative",
          acreage: 2.5,
        });
        cropName = createdCrop.crop_type;
      } catch (cropErr) {
        console.warn("Crop creation error:", cropErr);
      }

      setFarms((prev) => [
        ...prev,
        {
          id: createdFarm.id,
          name: createdFarm.name,
          cropName: cropName,
          healthScore: 90,
          riskLevel: "LOW",
          lastScanDate: null,
          lastSeverityPct: null,
          needsFollowUp: false,
          gpsLat: createdFarm.gps_lat,
          gpsLng: createdFarm.gps_lng,
        },
      ]);
      setShowAddFarmModal(false);
      setNewFarmName("");
    } catch (err) {
      console.error("Failed to create farm:", err);
      alert("Failed to register farm. Please verify backend is running.");
    } finally {
      setLoading(false);
    }
  }

  async function handleLanguageChange(langCode: string) {
    setSelectedLang(langCode);
    if (scanResult) {
      try {
        const advRes = await api.getAdvisory(scanResult.label, scanResult.severity_pct, langCode);
        setAdvisory(advRes);
      } catch (err) {
        console.error("Failed to update language advisory:", err);
      }
    }
  }

  function resetScan() {
    setImageFile(null);
    setImagePreview(null);
    setScanResult(null);
    setRiskResult(null);
    setAdvisory(null);
    setError(null);
    setBlurError(null);
    setShowGradCAM(true);
    setShowWhy(false);
  }

  function goBack() {
    resetScan();
    setScreen("home");
  }

  // Render Home Screen
  if (screen === "home") {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        {voiceAssistant}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
              🌱 {t("farmer.my_farms")}
            </h1>
            <p className="text-slate-400 text-sm mt-2">{t("farmer.select_farm")}</p>
          </div>
          <button
            onClick={() => setShowAddFarmModal(true)}
            className="px-5 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg text-sm font-semibold transition-all duration-200 shadow-lg shadow-emerald-500/20"
          >
            {t("farmer.add_farm")}
          </button>
        </div>

        {fetchingData ? (
          <div className="text-center py-12 text-slate-400">{t("farmer.loading_farms")}</div>
        ) : farms.length === 0 ? (
          <div className="glass p-8 rounded-xl text-center max-w-md mx-auto my-12 border border-white/10">
            <div className="text-5xl mb-4">🌾</div>
            <h3 className="text-lg font-semibold text-white mb-2">{t("farmer.no_farms")}</h3>
            <p className="text-sm text-slate-400 mb-6">
              {t("farmer.register_hint")}
            </p>
            <button
              onClick={() => setShowAddFarmModal(true)}
              className="px-6 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg text-sm font-semibold transition-all duration-200 shadow-lg shadow-emerald-500/20"
            >
              {t("farmer.register_farm")}
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {farms.map((farm) => (
              <FarmCard
                key={farm.id}
                farmName={farm.name}
                cropName={farm.cropName}
                healthScore={farm.healthScore}
                riskLevel={farm.riskLevel}
                needsFollowUp={farm.needsFollowUp}
                onScan={() => handleScanCrop(farm)}
              />
            ))}
          </div>
        )}

        {/* Modal for adding new farm */}
        {showAddFarmModal && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="glass p-6 rounded-xl max-w-md w-full border border-white/20">
              <h2 className="text-lg font-semibold text-white mb-5">🌱 Register New Farm</h2>
              <form onSubmit={handleCreateFarm} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-2">Farm Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Main Plot"
                    value={newFarmName}
                    onChange={(e) => setNewFarmName(e.target.value)}
                    className="w-full px-4 py-2.5 bg-slate-900/50 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:border-emerald-500 transition-all duration-200"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-2">Primary Crop</label>
                  <select
                    value={newCropType}
                    onChange={(e) => setNewCropType(e.target.value)}
                    className="w-full px-4 py-2.5 bg-slate-900/50 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:border-emerald-500 transition-all duration-200"
                  >
                    <option value="Tomato">Tomato</option>
                    <option value="Maize">Maize</option>
                    <option value="Cassava">Cassava</option>
                    <option value="Cashew">Cashew</option>
                    <option value="Cotton">Cotton</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-2">Village / Location</label>
                  <input
                    type="text"
                    placeholder="e.g. Nashik"
                    value={newVillage}
                    onChange={(e) => setNewVillage(e.target.value)}
                    className="w-full px-4 py-2.5 bg-slate-900/50 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:border-emerald-500 transition-all duration-200"
                  />
                </div>
                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowAddFarmModal(false)}
                    className="px-5 py-2.5 text-slate-400 hover:text-white text-sm font-semibold transition-colors duration-200"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-5 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg text-sm font-semibold transition-all duration-200 disabled:opacity-50 shadow-lg shadow-emerald-500/20"
                  >
                    {loading ? "Saving..." : "Save Farm"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        <button
          onClick={() => setScreen("alerts")}
          className="mt-8 w-full py-3 glass border border-white/10 text-slate-300 rounded-lg text-sm font-semibold hover:bg-white/5 transition-all duration-200"
        >
          {t("farmer.alerts")} ({alerts.length})
        </button>
        <div className="mt-6">
          <GovResourceLinks />
        </div>
        {showChat && farms[0] && <div className="mb-6"><ChatPanel userId={farmerId} role="farmer" farmId={farms[0].id} officerId="officer-1" onClose={() => setShowChat(false)} /></div>}
        {voiceMessage && <p className="mb-4 rounded-lg bg-amber-500/10 px-3 py-2 text-xs text-amber-200">{voiceMessage}</p>}
      </div>
    );
  }


  // Render Scan Screen
  if (screen === "scan") {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        {voiceAssistant}
        <button onClick={goBack} className="mb-4 text-slate-400 text-sm hover:text-white flex items-center gap-1 transition-colors duration-200">
          ← Back
        </button>

        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            📸 Scan {selectedFarm?.cropName}
          </h1>
          <p className="text-slate-400 text-sm mt-2">{selectedFarm?.name}</p>
        </div>

        <div className="glass p-6 rounded-xl border border-white/10">
          <form onSubmit={handleSubmit} className="flex flex-col gap-6">
            <div
              onClick={() => fileRef.current?.click()}
              className="border-2 border-dashed border-emerald-500/30 hover:border-emerald-500 rounded-xl p-8 text-center cursor-pointer transition-all duration-200 bg-white/[0.02] hover:bg-emerald-500/5"
            >
              {imagePreview ? (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img src={imagePreview} alt="Crop preview" className="max-h-64 mx-auto rounded-lg object-cover shadow-lg" />
              ) : (
                <div className="text-slate-400 py-8">
                  <div className="text-5xl mb-3">📸</div>
                  <p className="text-lg font-semibold text-slate-200">Take or upload a photo</p>
                  <p className="text-sm text-slate-500 mt-2">Tap to open camera or gallery</p>
                </div>
              )}
            </div>
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handleFileChange}
              className="hidden"
            />

            {blurError && (
              <div className="bg-amber-500/20 border border-amber-500/30 rounded-lg px-4 py-3 text-amber-300 text-sm">
                ⚠️ {blurError}
              </div>
            )}

            {error && (
              <div className="bg-red-500/20 border border-red-500/30 rounded-lg px-4 py-3 text-red-300 text-sm">
                ⚠️ {error}
              </div>
            )}

            {loading && (
              <div className="text-center py-4">
                <div className="animate-spin w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full mx-auto mb-2" />
                <p className="text-sm text-slate-400">{loadingStep}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !imageFile}
              className="w-full py-4 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg text-lg font-semibold transition-all duration-200 disabled:opacity-50 shadow-lg shadow-emerald-500/20"
            >
              {loading ? "Analyzing..." : "🔍 Scan Crop"}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // Render Result Screen
  if (screen === "result" && scanResult) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        {voiceAssistant}
        <button onClick={goBack} className="mb-4 text-slate-400 text-sm hover:text-white flex items-center gap-1 transition-colors duration-200">
          ← Back to Farms
        </button>

        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
              🔬 Scan Results
            </h1>
            <p className="text-slate-400 text-sm mt-2">{selectedFarm?.name} • {selectedFarm?.cropName}</p>
          </div>

          <div className="flex items-center gap-2 bg-white/5 border border-white/10 p-1 rounded-lg">
            {LANGUAGES.map((l) => (
              <button
                key={l.code}
                type="button"
                onClick={() => handleLanguageChange(l.code)}
                className={`px-4 py-2 rounded-md text-xs font-semibold transition-all duration-200 ${
                  selectedLang === l.code
                    ? "bg-emerald-500 text-white font-semibold"
                    : "text-slate-400 hover:text-white hover:bg-white/5"
                }`}
              >
                {l.label}
              </button>
            ))}
          </div>
        </div>

        {/* Diagnosis Card */}
        <div className="glass p-6 rounded-xl mb-6 border border-emerald-500/30">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-white">
                {scanResult.label.replace("___", " - ").replace("_", " ")}
              </h2>
              {scanResult.low_confidence && (
                <span className="bg-amber-500/20 border border-amber-500/30 text-amber-300 text-xs px-3 py-1 rounded-md font-medium mt-2 inline-block">
                  ⚠️ Low Confidence
                </span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white/5 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-2">Confidence</p>
              <p className="text-2xl font-bold text-emerald-400">{(scanResult.confidence * 100).toFixed(0)}%</p>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-2">Severity</p>
              <p className="text-2xl font-bold text-amber-400">{scanResult.severity_pct}%</p>
            </div>
          </div>

          {/* Follow-up comparison */}
          {selectedFarm?.needsFollowUp && selectedFarm.lastSeverityPct !== null && (
            <div className="mt-4 pt-4 border-t border-white/10">
              <p className="text-xs text-slate-400 mb-2">Compared to previous scan</p>
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-300">Previous: {selectedFarm.lastSeverityPct}%</span>
                <span className="text-slate-500">→</span>
                <span className="text-sm text-white">Current: {scanResult.severity_pct}%</span>
                {scanResult.severity_pct < selectedFarm.lastSeverityPct ? (
                  <span className="text-xs text-emerald-400 font-semibold">✓ Improving</span>
                ) : scanResult.severity_pct > selectedFarm.lastSeverityPct ? (
                  <span className="text-xs text-red-400 font-semibold">⚠ Worsening</span>
                ) : (
                  <span className="text-xs text-slate-400 font-semibold">→ Stable</span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Grad-CAM */}
        <div className="glass p-6 rounded-2xl mb-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-white">🔥 Heatmap</h3>
            <button
              onClick={() => setShowGradCAM(!showGradCAM)}
              className="text-xs text-emerald-400 font-semibold"
            >
              {showGradCAM ? "Show Original" : "Show Heatmap"}
            </button>
          </div>
          <div className="rounded-xl overflow-hidden bg-slate-950 flex items-center justify-center">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={showGradCAM ? scanResult.gradcam_image_base64 : (imagePreview || "")}
              alt="Grad-CAM"
              className="max-h-64 object-contain"
            />
          </div>
        </div>

        {/* Risk Score */}
        {riskResult && (
          <div className="glass p-6 rounded-2xl mb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-white">📊 Risk Score</h3>
              <button
                onClick={() => setShowWhy(!showWhy)}
                className="text-xs text-emerald-400 font-semibold"
              >
                {showWhy ? "Hide Details" : "Why?"}
              </button>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-4xl font-bold text-white">{riskResult.overall_score.toFixed(0)}</div>
              <div>
                <div className={`px-3 py-1 rounded-lg text-sm font-bold ${
                  riskResult.risk_level === "CRITICAL" ? "bg-red-500/20 text-red-400" :
                  riskResult.risk_level === "HIGH" ? "bg-orange-500/20 text-orange-400" :
                  riskResult.risk_level === "MODERATE" ? "bg-yellow-500/20 text-yellow-400" :
                  "bg-emerald-500/20 text-emerald-400"
                }`}>
                  {riskResult.risk_level}
                </div>
              </div>
            </div>
            {showWhy && (
              <div className="mt-4 space-y-2">
                {riskResult.why.map((item, idx) => (
                  <div key={idx} className="bg-white/5 rounded-lg p-3">
                    <p className="text-xs font-semibold text-white">{item.factor}</p>
                    <p className="text-xs text-slate-400 mt-1">{item.details}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Advisory */}
        {advisory && (
          <div className="glass p-6 rounded-2xl">
            <h3 className="text-sm font-bold text-white mb-4">💊 Treatment Advice</h3>
            
            {/* Chemical Controls */}
            {advisory.treatments.chemical.length > 0 && (
              <div className="mb-4">
                <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2">
                  🧪 Chemical Control
                </h4>
                <ul className="list-disc list-inside text-sm text-slate-300 space-y-1">
                  {advisory.treatments.chemical.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Organic Controls */}
            {advisory.treatments.organic.length > 0 && (
              <div className="mb-4">
                <h4 className="text-xs font-bold text-green-400 uppercase tracking-wider mb-2">
                  🌿 Organic & Biological Solutions
                </h4>
                <ul className="list-disc list-inside text-sm text-slate-300 space-y-1">
                  {advisory.treatments.organic.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Cultural Practices */}
            {advisory.treatments.cultural.length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-sky-400 uppercase tracking-wider mb-2">
                  🚜 Cultural & Field Practices
                </h4>
                <ul className="list-disc list-inside text-sm text-slate-300 space-y-1">
                  {advisory.treatments.cultural.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // Render Alerts Screen
  if (screen === "alerts") {
    const riskColors: Record<string, string> = {
      LOW: "bg-emerald-500/20 border-emerald-500/30 text-emerald-400",
      MODERATE: "bg-yellow-500/20 border-yellow-500/30 text-yellow-400",
      HIGH: "bg-orange-500/20 border-orange-500/30 text-orange-400",
      CRITICAL: "bg-red-500/20 border-red-500/30 text-red-400",
    };

    const formatDate = (dateStr: string) => {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
    };

    return (
      <div className="max-w-4xl mx-auto px-4 py-6">
        {voiceAssistant}
        <button onClick={() => setScreen("home")} className="mb-4 text-slate-400 text-sm hover:text-white flex items-center gap-1">
          ← Back
        </button>

        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            🔔 Alerts
          </h1>
          <p className="text-slate-400 text-sm mt-1">Past disease alerts and notifications</p>
        </div>

        {alerts.length === 0 ? (
          <div className="glass p-8 rounded-2xl text-center max-w-md mx-auto my-8 border border-white/10">
            <div className="text-4xl mb-3">🔔</div>
            <h3 className="text-base font-bold text-white mb-1">No alerts or past scans</h3>
            <p className="text-xs text-slate-400">
              When you scan crops or disease outbreaks are detected nearby, reports will appear here.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert) => (
              <div key={alert.id} className="glass p-4 rounded-xl border border-white/10">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-bold text-white">{alert.farmName}</p>
                    <p className="text-sm text-slate-400">{alert.cropName} • {alert.disease}</p>
                  </div>
                  <span className={`px-2 py-1 rounded-lg text-xs font-bold ${riskColors[alert.riskLevel] || riskColors.LOW}`}>
                    {alert.riskLevel}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span>{formatDate(alert.timestamp)}</span>
                  <span>Severity: {alert.severityPct}%</span>
                </div>
              </div>
            ))}
          </div>
        )}

      </div>
    );
  }

  return null;
}
