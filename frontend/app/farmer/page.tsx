"use client";

import { useState, useRef } from "react";
import { api, type ScanResponse, type RiskScoreResponse, type AdvisoryResponse } from "@/lib/api";
import { detectBlur } from "@/lib/blurDetection";
import FarmCard from "@/components/farmer/FarmCard";

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
  { code: "hi", label: "हिंदी" },
  { code: "mr", label: "मराठी" },
];

// Mock farm data - in production, this would come from the API
const MOCK_FARMS: Farm[] = [
  { id: "1", name: "Main Field", cropName: "Tomato", healthScore: 85, riskLevel: "LOW", lastScanDate: "2026-09-10", lastSeverityPct: 25, needsFollowUp: false },
  { id: "2", name: "North Plot", cropName: "Cotton", healthScore: 62, riskLevel: "MODERATE", lastScanDate: "2026-09-08", lastSeverityPct: 42, needsFollowUp: true },
  { id: "3", name: "East Section", cropName: "Chilli", healthScore: 45, riskLevel: "HIGH", lastScanDate: "2026-09-05", lastSeverityPct: 65, needsFollowUp: true },
];

// Mock alerts data - in production, this would come from the API
const MOCK_ALERTS: Alert[] = [
  { id: "1", farmName: "East Section", cropName: "Chilli", disease: "Leaf Curl Virus", riskLevel: "HIGH", timestamp: "2026-09-11T10:30:00Z", severityPct: 65 },
  { id: "2", farmName: "North Plot", cropName: "Cotton", disease: "Bollworm", riskLevel: "MODERATE", timestamp: "2026-09-09T14:15:00Z", severityPct: 42 },
  { id: "3", farmName: "Main Field", cropName: "Tomato", disease: "Early Blight", riskLevel: "LOW", timestamp: "2026-09-07T09:00:00Z", severityPct: 25 },
];

export default function FarmerPage() {
  const [screen, setScreen] = useState<Screen>("home");
  const [selectedFarm, setSelectedFarm] = useState<Farm | null>(null);
  const [selectedLang, setSelectedLang] = useState("en");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null);
  const [riskResult, setRiskResult] = useState<RiskScoreResponse | null>(null);
  const [advisory, setAdvisory] = useState<AdvisoryResponse | null>(null);
  const [showGradCAM, setShowGradCAM] = useState(true);
  const [showWhy, setShowWhy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [blurError, setBlurError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

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

      // 1. Scan image with AI classifier + Grad-CAM + HSV severity
      setLoadingStep("Analyzing leaf with AI...");
      const scanRes = await api.scanImage(fd);
      setScanResult(scanRes);

      // 2. Get risk score
      if (selectedFarm) {
        setLoadingStep("Calculating risk score...");
        try {
          const riskRes = await api.getRiskScore(selectedFarm.id);
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
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            🌱 My Farms
          </h1>
          <p className="text-slate-400 text-sm mt-1">Select a farm to scan for diseases</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {MOCK_FARMS.map((farm) => (
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

        <button
          onClick={() => setScreen("alerts")}
          className="mt-6 w-full py-3 glass border border-white/10 text-slate-300 rounded-xl text-sm font-semibold hover:bg-white/5 transition-all"
        >
          🔔 View Alerts
        </button>
      </div>
    );
  }

  // Render Scan Screen
  if (screen === "scan") {
    return (
      <div className="max-w-4xl mx-auto px-4 py-6">
        <button onClick={goBack} className="mb-4 text-slate-400 text-sm hover:text-white flex items-center gap-1">
          ← Back
        </button>

        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            📸 Scan {selectedFarm?.cropName}
          </h1>
          <p className="text-slate-400 text-sm mt-1">{selectedFarm?.name}</p>
        </div>

        <div className="glass p-6 rounded-2xl">
          <form onSubmit={handleSubmit} className="flex flex-col gap-6">
            <div
              onClick={() => fileRef.current?.click()}
              className="border-2 border-dashed border-emerald-500/30 hover:border-emerald-500 rounded-2xl p-8 text-center cursor-pointer transition-all bg-white/[0.02] hover:bg-emerald-500/5"
            >
              {imagePreview ? (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img src={imagePreview} alt="Crop preview" className="max-h-64 mx-auto rounded-xl object-cover shadow-lg" />
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
              <div className="bg-amber-500/20 border border-amber-500/30 rounded-xl px-4 py-3 text-amber-300 text-sm">
                ⚠️ {blurError}
              </div>
            )}

            {error && (
              <div className="bg-red-500/20 border border-red-500/30 rounded-xl px-4 py-3 text-red-300 text-sm">
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
              className="w-full py-4 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl text-lg transition-all disabled:opacity-50"
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
      <div className="max-w-4xl mx-auto px-4 py-6">
        <button onClick={goBack} className="mb-4 text-slate-400 text-sm hover:text-white flex items-center gap-1">
          ← Back to Farms
        </button>

        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              🔬 Scan Results
            </h1>
            <p className="text-slate-400 text-sm mt-1">{selectedFarm?.name} • {selectedFarm?.cropName}</p>
          </div>

          <div className="flex items-center gap-2 bg-white/5 border border-white/10 p-1 rounded-lg">
            {LANGUAGES.map((l) => (
              <button
                key={l.code}
                type="button"
                onClick={() => handleLanguageChange(l.code)}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                  selectedLang === l.code
                    ? "bg-emerald-500 text-slate-950 font-bold"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                {l.label}
              </button>
            ))}
          </div>
        </div>

        {/* Diagnosis Card */}
        <div className="glass p-6 rounded-2xl mb-4 border-emerald-500/30">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold text-white">
                {scanResult.label.replace("___", " - ").replace("_", " ")}
              </h2>
              {scanResult.low_confidence && (
                <span className="bg-amber-500/20 border border-amber-500/30 text-amber-300 text-xs px-2 py-1 rounded-md font-medium mt-2 inline-block">
                  ⚠️ Low Confidence
                </span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white/5 rounded-xl p-4">
              <p className="text-xs text-slate-400 mb-1">Confidence</p>
              <p className="text-2xl font-bold text-emerald-400">{(scanResult.confidence * 100).toFixed(0)}%</p>
            </div>
            <div className="bg-white/5 rounded-xl p-4">
              <p className="text-xs text-slate-400 mb-1">Severity</p>
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
        <button onClick={() => setScreen("home")} className="mb-4 text-slate-400 text-sm hover:text-white flex items-center gap-1">
          ← Back
        </button>

        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            🔔 Alerts
          </h1>
          <p className="text-slate-400 text-sm mt-1">Past disease alerts and notifications</p>
        </div>

        <div className="space-y-3">
          {MOCK_ALERTS.map((alert) => (
            <div key={alert.id} className="glass p-4 rounded-xl border border-white/10">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="font-bold text-white">{alert.farmName}</p>
                  <p className="text-sm text-slate-400">{alert.cropName} • {alert.disease}</p>
                </div>
                <span className={`px-2 py-1 rounded-lg text-xs font-bold ${riskColors[alert.riskLevel]}`}>
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
      </div>
    );
  }

  return null;
}
