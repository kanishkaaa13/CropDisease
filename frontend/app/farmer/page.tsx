"use client";

import { useState, useRef } from "react";
import { api, type ScanResponse, type AdvisoryResponse } from "@/lib/api";

const CROPS = ["Tomato", "Cotton", "Rice", "Chilli", "Sugarcane", "Soybean", "Wheat"];
const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिंदी (Hindi)" },
  { code: "mr", label: "मराठी (Marathi)" },
];

export default function FarmerPage() {
  const [selectedCrop, setSelectedCrop] = useState("Tomato");
  const [selectedLang, setSelectedLang] = useState("en");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null);
  const [advisory, setAdvisory] = useState<AdvisoryResponse | null>(null);
  const [showGradCAM, setShowGradCAM] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    setImageFile(f);
    setImagePreview(URL.createObjectURL(f));
    setScanResult(null);
    setAdvisory(null);
    setError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!imageFile) {
      setError("Please select a crop leaf image.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const fd = new FormData();
      fd.append("file", imageFile);

      // 1. Scan image with AI classifier + Grad-CAM + HSV severity
      const scanRes = await api.scanImage(fd);
      setScanResult(scanRes);

      // 2. Fetch multilingual advisory action plan
      const advRes = await api.getAdvisory(scanRes.label, scanRes.severity_pct, selectedLang);
      setAdvisory(advRes);

    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Diagnostic scan failed. Please try again.");
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

  return (
    <div className="max-w-4xl mx-auto px-4 py-10">
      {/* Page Header */}
      <div className="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
            🌱 KrushiRakshak AI Diagnostic Scan
          </h1>
          <p className="text-slate-400 mt-1">
            Instant AI crop disease identification, Grad-CAM focus heatmaps & localized treatment plans.
          </p>
        </div>

        {/* Language selector */}
        <div className="flex items-center gap-2 bg-white/5 border border-white/10 p-1.5 rounded-xl">
          {LANGUAGES.map((l) => (
            <button
              key={l.code}
              type="button"
              onClick={() => handleLanguageChange(l.code)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                selectedLang === l.code
                  ? "bg-emerald-500 text-slate-950 font-bold shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {l.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Upload Form (5 cols) */}
        <form onSubmit={handleSubmit} className="lg:col-span-5 glass p-6 flex flex-col gap-6 h-fit">
          {/* Crop Selector */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2 block">
              Crop Type
            </label>
            <div className="flex flex-wrap gap-2">
              {CROPS.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setSelectedCrop(c)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    selectedCrop === c
                      ? "bg-emerald-600 text-white shadow"
                      : "bg-white/5 text-slate-400 border border-white/10 hover:bg-white/10 hover:text-white"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>

          {/* Upload Area */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2 block">
              Upload Crop Leaf Photo
            </label>
            <div
              onClick={() => fileRef.current?.click()}
              className="border-2 border-dashed border-emerald-500/30 hover:border-emerald-500 rounded-2xl p-6 text-center cursor-pointer transition-all bg-white/[0.02] hover:bg-emerald-500/5"
            >
              {imagePreview ? (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img src={imagePreview} alt="Crop preview" className="max-h-48 mx-auto rounded-xl object-cover shadow-lg" />
              ) : (
                <div className="text-slate-400 py-4">
                  <div className="text-4xl mb-2">📸</div>
                  <p className="text-sm font-semibold text-slate-200">Take or upload a photo</p>
                  <p className="text-xs text-slate-500 mt-1">JPEG, PNG, WEBP up to 10 MB</p>
                </div>
              )}
            </div>
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>

          {error && (
            <div className="bg-red-500/20 border border-red-500/30 rounded-xl px-4 py-3 text-red-300 text-xs">
              ⚠️ {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 px-4 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl shadow-lg shadow-emerald-950/50 transition-all flex items-center justify-center gap-2 text-sm disabled:opacity-50"
          >
            {loading ? (
              <>
                <svg className="animate-spin w-4 h-4 text-slate-950" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                AI Analyzing Leaf & Heatmap...
              </>
            ) : (
              "🔍 Run AI Diagnostic Scan"
            )}
          </button>
        </form>

        {/* Results & Grad-CAM Display (7 cols) */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          {scanResult ? (
            <>
              {/* Scan Summary Card */}
              <div className="glass p-6 border-emerald-500/30">
                <div className="flex items-start justify-between gap-4 mb-4">
                  <div>
                    <span className="text-[10px] uppercase font-bold tracking-widest text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-md border border-emerald-500/20">
                      Top AI Detection
                    </span>
                    <h2 className="text-2xl font-black text-white mt-1">
                      {scanResult.label.replace("___", " - ").replace("_", " ")}
                    </h2>
                  </div>

                  {scanResult.low_confidence && (
                    <span className="bg-amber-500/20 border border-amber-500/30 text-amber-300 text-xs px-2.5 py-1 rounded-md font-medium">
                      ⚠️ Low Confidence (&lt;60%)
                    </span>
                  )}
                </div>

                {/* Calibrated Confidence & HSV Severity Meter */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="bg-white/5 border border-white/10 rounded-xl p-3.5">
                    <p className="text-[11px] text-slate-400 font-semibold uppercase">Calibrated Confidence</p>
                    <p className="text-xl font-extrabold text-emerald-400 tabular-nums">
                      {(scanResult.confidence * 100).toFixed(1)}%
                    </p>
                    <div className="w-full bg-white/10 rounded-full h-1.5 mt-2">
                      <div
                        className="bg-emerald-400 h-1.5 rounded-full"
                        style={{ width: `${scanResult.confidence * 100}%` }}
                      />
                    </div>
                  </div>

                  <div className="bg-white/5 border border-white/10 rounded-xl p-3.5">
                    <p className="text-[11px] text-slate-400 font-semibold uppercase">HSV Severity Estimate</p>
                    <p className="text-xl font-extrabold text-amber-400 tabular-nums">
                      {scanResult.severity_pct}% <span className="text-xs text-slate-400">leaf area</span>
                    </p>
                    <div className="w-full bg-white/10 rounded-full h-1.5 mt-2">
                      <div
                        className="bg-amber-400 h-1.5 rounded-full"
                        style={{ width: `${scanResult.severity_pct}%` }}
                      />
                    </div>
                  </div>
                </div>

                {/* Top-3 Predictions */}
                <div className="border-t border-white/10 pt-4">
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Top-3 Probabilities</p>
                  <div className="flex flex-col gap-2">
                    {scanResult.top3.map((pred, i) => (
                      <div key={i} className="flex items-center justify-between text-xs text-slate-300">
                        <span>{pred.label.replace("___", " - ").replace("_", " ")}</span>
                        <span className="font-mono font-bold text-slate-200">{(pred.confidence * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Grad-CAM Heatmap Section */}
              <div className="glass p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    🔥 Grad-CAM Explainability Heatmap
                  </h3>
                  <button
                    onClick={() => setShowGradCAM(!showGradCAM)}
                    className="text-xs text-emerald-400 font-semibold hover:underline"
                  >
                    {showGradCAM ? "Show Original Photo" : "Show Grad-CAM Focus"}
                  </button>
                </div>

                <div className="relative rounded-2xl overflow-hidden border border-white/10 bg-slate-950 flex items-center justify-center p-2">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={showGradCAM ? scanResult.gradcam_image_base64 : (imagePreview || "")}
                    alt="Grad-CAM visual heatmap"
                    className="max-h-64 object-contain rounded-xl shadow-2xl transition-all"
                  />
                </div>
                <p className="text-[11px] text-slate-500 mt-2 text-center">
                  Red/warm regions highlight pixel areas that drove the AI model's prediction.
                </p>
              </div>

              {/* Multilingual Agronomic Advisory Action Plan */}
              {advisory && (
                <div className="glass p-6 border-amber-500/30">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-extrabold text-white flex items-center gap-2">
                      💊 Agronomic Action Plan ({advisory.language.toUpperCase()})
                    </h3>
                    <span className="text-xs px-2.5 py-1 rounded-md font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      {advisory.urgency_level}
                    </span>
                  </div>

                  {/* Chemical Treatments */}
                  <div className="mb-4">
                    <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2">
                      🧪 Chemical Control
                    </h4>
                    <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
                      {advisory.treatments.chemical.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Organic Controls */}
                  <div className="mb-4">
                    <h4 className="text-xs font-bold text-green-400 uppercase tracking-wider mb-2">
                      🌿 Organic & Biological Solutions
                    </h4>
                    <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
                      {advisory.treatments.organic.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Cultural Practices */}
                  <div>
                    <h4 className="text-xs font-bold text-sky-400 uppercase tracking-wider mb-2">
                      🚜 Cultural & Field Practices
                    </h4>
                    <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
                      {advisory.treatments.cultural.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="glass p-12 text-center text-slate-500 flex flex-col items-center justify-center min-h-[400px]">
              <div className="text-5xl mb-3 opacity-60">🔬</div>
              <h3 className="text-lg font-bold text-slate-300">Ready to Scan Crop</h3>
              <p className="text-xs max-w-sm mt-1">
                Upload a crop photo on the left to view instant disease diagnosis, calibrated confidence scores, Grad-CAM focus heatmaps, and localized treatment advisories.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
