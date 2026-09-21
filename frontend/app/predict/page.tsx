"use client";

import { useEffect, useRef, useState } from "react";
import { api, type CropRiskPrediction, type ScanResponse } from "@/lib/api";
import SeverityBadge from "@/components/SeverityBadge";
import { useI18n } from "@/lib/i18n";

const DISTRICTS: Record<string, { latitude: number; longitude: number }> = {
  Nashik: { latitude: 20.0059, longitude: 73.7897 },
  Pune: { latitude: 18.5204, longitude: 73.8567 },
  Nagpur: { latitude: 21.1458, longitude: 79.0882 },
  Kolhapur: { latitude: 16.705, longitude: 74.2433 },
  Solapur: { latitude: 17.6599, longitude: 75.9064 },
};

const initialForm = {
  district: "Nashik",
  crop: "Tomato",
  sowing_date: "",
  soil_type: "Loamy",
  temperature: "28",
  humidity: "72",
  rainfall: "8",
  soil_ph: "6.5",
};

function withTimeout<T>(promise: Promise<T>, milliseconds: number): Promise<T> {
  return Promise.race([
    promise,
    new Promise<T>((_, reject) => window.setTimeout(() => reject(new Error("Analysis timed out after 30 seconds. Please try again.")), milliseconds)),
  ]);
}

export default function PredictPage() {
  const { locale } = useI18n();
  const [tab, setTab] = useState<"weather" | "image">("weather");
  const [form, setForm] = useState(initialForm);
  const [weatherResult, setWeatherResult] = useState<CropRiskPrediction | null>(null);
  const [imageResult, setImageResult] = useState<ScanResponse | null>(null);
  const [imageAdvisory, setImageAdvisory] = useState<string[]>([]);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [autoFilling, setAutoFilling] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);

  function updateForm(name: keyof typeof initialForm, value: string) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function autoFillWeather() {
    const location = DISTRICTS[form.district] ?? DISTRICTS.Nashik;
    setAutoFilling(true);
    setError("");
    try {
      const weather = await api.getWeather(location.latitude, location.longitude);
      setForm((current) => ({ ...current, temperature: String(weather.temperature), humidity: String(weather.humidity) }));
    } catch {
      setError("Weather data is unavailable right now. Enter the values manually.");
    } finally {
      setAutoFilling(false);
    }
  }

  async function submitRisk(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    const location = DISTRICTS[form.district] ?? DISTRICTS.Nashik;
    try {
      const result = await withTimeout(api.predictRisk({
        district: form.district,
        crop: form.crop,
        sowing_date: form.sowing_date || undefined,
        soil_type: form.soil_type,
        temperature: Number(form.temperature),
        humidity: Number(form.humidity),
        rainfall: Number(form.rainfall),
        soil_ph: Number(form.soil_ph),
        ...location,
      }), 30000);
      setWeatherResult(result);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Risk prediction failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  function chooseFile(file?: File) {
    if (!file) return;
    if (!file.type.startsWith("image/")) { setError("Please choose a JPG, PNG, or WEBP image."); return; }
    setImageFile(file);
    setPreview(URL.createObjectURL(file));
    setImageResult(null);
    setImageAdvisory([]);
    setError("");
  }

  async function analyzeImage() {
    if (!imageFile) return;
    setLoading(true);
    setError("");
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 30000);
    try {
      const data = new FormData();
      data.append("file", imageFile);
      const result = await api.scanImage(data, locale, controller.signal);
      setImageResult(result);
      try {
        const advisory = await api.getAdvisory(result.label, result.severity_pct, locale);
        setImageAdvisory([...advisory.treatments.chemical, ...advisory.treatments.organic, ...advisory.treatments.cultural].slice(0, 4));
      } catch {
        setImageAdvisory([]);
      }
    } catch (reason) {
      setError(reason instanceof DOMException && reason.name === "AbortError" ? "Analysis timed out after 30 seconds. Please try again." : reason instanceof Error ? reason.message : "Image analysis failed. Please try again.");
    } finally {
      window.clearTimeout(timeout);
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,#12352a_0%,#071411_40%,#020807_100%)] px-4 py-8 text-white sm:py-12">
      <div className="mx-auto max-w-5xl">
        <header className="mb-8 text-center sm:mb-10">
          <p className="mb-3 text-xs font-bold uppercase tracking-[0.28em] text-emerald-300">Dual-mode crop intelligence</p>
          <h1 className="text-3xl font-black tracking-tight text-white sm:text-5xl">Crop Prediction</h1>
          <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-slate-400 sm:text-base">Combine live weather, soil conditions, and your crop image to understand disease pressure before it spreads.</p>
        </header>

        <div className="mx-auto mb-8 grid max-w-xl grid-cols-2 rounded-xl border border-white/10 bg-black/30 p-1 shadow-2xl">
          <button onClick={() => setTab("weather")} className={`rounded-lg px-3 py-3 text-xs font-bold uppercase tracking-wider transition sm:text-sm ${tab === "weather" ? "bg-emerald-500 text-slate-950" : "text-slate-400 hover:text-white"}`}>🌦 Weather &amp; Soil Data</button>
          <button onClick={() => setTab("image")} className={`rounded-lg px-3 py-3 text-xs font-bold uppercase tracking-wider transition sm:text-sm ${tab === "image" ? "bg-emerald-500 text-slate-950" : "text-slate-400 hover:text-white"}`}>🔬 Image Analysis</button>
        </div>

        <section className="rounded-2xl border border-white/10 bg-[#08100d]/90 p-5 shadow-2xl sm:p-8">
          {error && <div className="mb-5 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">{error}</div>}
          {tab === "weather" ? (
            <div>
              <div className="mb-6 flex flex-col justify-between gap-3 sm:flex-row sm:items-start"><div><h2 className="text-2xl font-black text-emerald-300">Weather &amp; Soil Risk</h2><p className="mt-1 text-sm text-slate-400">Seven-day disease pressure from local field conditions.</p></div><button onClick={autoFillWeather} disabled={autoFilling} className="rounded-lg border border-sky-500/30 bg-sky-500/10 px-3 py-2 text-xs font-bold text-sky-300 disabled:opacity-50">{autoFilling ? "Loading weather..." : "↻ Auto-fill weather"}</button></div>
              <form onSubmit={submitRisk} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {(["district", "crop", "sowing_date", "soil_type", "temperature", "humidity", "rainfall", "soil_ph"] as const).map((name) => <label key={name} className="text-xs font-bold uppercase tracking-wider text-slate-400">{name.replaceAll("_", " ")}<input required={name !== "sowing_date"} type={name === "sowing_date" ? "date" : name === "temperature" || name === "humidity" || name === "rainfall" || name === "soil_ph" ? "number" : "text"} step="any" value={form[name]} onChange={(event) => updateForm(name, event.target.value)} className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-3 text-sm normal-case text-white outline-none focus:border-emerald-400" /></label>)}
                <button type="submit" disabled={loading} className="sm:col-span-2 rounded-lg bg-emerald-500 px-5 py-3 text-sm font-black text-slate-950 transition hover:bg-emerald-400 disabled:cursor-wait disabled:opacity-50">{loading ? "Predicting..." : "Predict 7-day risk"}</button>
              </form>
              {weatherResult && <div className="mt-8 border-t border-white/10 pt-6"><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-xs uppercase tracking-widest text-slate-500">Predicted risk</p><p className="mt-1 text-4xl font-black text-white">{weatherResult.score.toFixed(0)}<span className="text-base text-slate-500">/100</span></p></div><SeverityBadge severity={weatherResult.risk_level} /></div><div className="mt-6 grid gap-3 sm:grid-cols-3">{weatherResult.factors.map((factor) => <div key={factor.name} className="rounded-xl bg-white/5 p-4"><p className="text-sm font-bold text-slate-200">{factor.name}</p><p className="mt-2 text-2xl font-black text-emerald-300">{factor.value.toFixed(0)}</p><p className="mt-1 text-xs leading-5 text-slate-500">{factor.detail}</p></div>)}</div><div className="mt-6 grid gap-6 lg:grid-cols-2"><div><h3 className="mb-3 text-sm font-black uppercase tracking-wider text-emerald-300">Preventive actions</h3><ul className="space-y-2 text-sm text-slate-300">{weatherResult.actions.map((action) => <li key={action} className="rounded-lg bg-white/5 p-3">✓ {action}</li>)}</ul></div><div><h3 className="mb-3 text-sm font-black uppercase tracking-wider text-emerald-300">7-day outlook</h3><div className="space-y-2">{weatherResult.forecast.map((day) => <div key={`${day.date}-${day.day}`} className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2 text-xs"><span className="text-slate-400">{day.day} · {day.date}</span><span className="font-bold text-white">{day.predicted_risk_score.toFixed(0)} · {day.risk_level}</span></div>)}</div></div></div></div>}
            </div>
          ) : (
            <div><div className="mb-6"><h2 className="text-2xl font-black text-emerald-300">Image Analysis</h2><p className="mt-1 text-sm text-slate-400">Upload a clear leaf photo for diagnosis and severity analysis.</p></div><div onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); chooseFile(event.dataTransfer.files[0]); }} onClick={() => fileRef.current?.click()} className="flex min-h-64 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-emerald-500/40 bg-black/20 p-6 text-center transition hover:border-emerald-300">{preview ? <img src={preview} alt="Leaf preview" className="max-h-56 rounded-xl object-contain" /> : <><span className="text-5xl">🌿</span><p className="mt-4 font-bold text-slate-200">Drop a leaf image or tap to browse</p><p className="mt-2 text-xs text-slate-500">JPG · PNG · WEBP · camera upload supported</p></>}<input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" capture="environment" className="hidden" onChange={(event) => chooseFile(event.target.files?.[0])} /></div>{imageFile && <div className="mt-4 flex flex-wrap gap-2"><button onClick={() => { setImageFile(null); setPreview(null); setImageResult(null); }} className="rounded-lg border border-white/10 px-4 py-2 text-xs font-bold text-slate-300">Remove</button><button onClick={analyzeImage} disabled={loading} className="rounded-lg bg-emerald-500 px-5 py-2 text-xs font-black text-slate-950 disabled:opacity-50">{loading ? "Analyzing..." : "Analyze image"}</button></div>}{imageResult && <div className="mt-8 grid gap-5 border-t border-white/10 pt-6 lg:grid-cols-2"><div><p className="text-xs uppercase tracking-wider text-slate-500">Diagnosis</p><h3 className="mt-2 text-2xl font-black text-white">{imageResult.localized_label || imageResult.label.replaceAll("_", " ")}</h3><div className="mt-4 flex flex-wrap gap-2"><span className="rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-bold text-emerald-300">Confidence {(imageResult.confidence * 100).toFixed(1)}%</span><SeverityBadge severity={imageResult.severity_key || "moderate"} /><span className="rounded-full bg-orange-500/15 px-3 py-1 text-xs font-bold text-orange-300">Severity {imageResult.severity_pct.toFixed(1)}%</span></div><p className="mt-5 text-sm leading-6 text-slate-400">Review the result with the advisory recommendations and contact a field officer if confidence is low or symptoms worsen.</p></div><div className="rounded-xl bg-black/30 p-3"><p className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-500">Grad-CAM focus</p><img src={imageResult.gradcam_image_base64} alt="Grad-CAM analysis overlay" className="max-h-64 w-full rounded-lg object-contain" /></div></div>}</div>
          )}
          {tab === "image" && imageResult && <div className="mt-5 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4"><p className="mb-2 text-xs font-bold uppercase tracking-wider text-emerald-300">Advisory</p><ul className="space-y-2 text-sm leading-5 text-slate-300">{imageAdvisory.length > 0 ? imageAdvisory.map((action) => <li key={action}>✓ {action}</li>) : <li>Review the result with a field officer if confidence is low or symptoms worsen.</li>}</ul></div>}
        </section>
      </div>
    </main>
  );
}
