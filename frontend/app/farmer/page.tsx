"use client";

import { useState, useRef } from "react";
import { api, type DiseaseDetectionResponse } from "@/lib/api";

const CROPS = ["wheat", "rice", "tomato", "maize", "cotton", "potato", "soybean"];

export default function FarmerPage() {
  const [selectedCrop, setSelectedCrop] = useState("wheat");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [result, setResult] = useState<DiseaseDetectionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    setImageFile(f);
    setImagePreview(URL.createObjectURL(f));
    setResult(null);
    setError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!imageFile) { setError("Please select an image."); return; }
    setLoading(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("image", imageFile);
      fd.append("crop_type", selectedCrop);
      const res = await api.detectDisease(fd);
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Detection failed.");
    } finally {
      setLoading(false);
    }
  }

  const severityClass: Record<string, string> = {
    none: "badge-none", low: "badge-low", medium: "badge-medium", high: "badge-high",
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">🌾 Crop Disease Detector</h1>
        <p className="text-slate-400">Upload a photo of your crop to get an instant AI diagnosis.</p>
      </div>

      <form onSubmit={handleSubmit} className="glass p-6 flex flex-col gap-6">
        {/* Crop selection */}
        <div>
          <label className="text-sm font-medium text-slate-300 mb-2 block">Select Crop Type</label>
          <div className="flex flex-wrap gap-2">
            {CROPS.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setSelectedCrop(c)}
                className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-all
                  ${selectedCrop === c
                    ? "bg-emerald-600 text-white shadow-lg shadow-emerald-900/50"
                    : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white border border-white/10"
                  }`}
              >
                {c}
              </button>
            ))}
          </div>
        </div>

        {/* Image upload */}
        <div>
          <label className="text-sm font-medium text-slate-300 mb-2 block">Upload Crop Image</label>
          <div
            onClick={() => fileRef.current?.click()}
            className="border-2 border-dashed border-white/20 rounded-xl p-8 text-center cursor-pointer hover:border-emerald-500/50 transition-colors"
          >
            {imagePreview ? (
              /* eslint-disable-next-line @next/next/no-img-element */
              <img src={imagePreview} alt="Crop preview" className="max-h-48 mx-auto rounded-lg object-cover" />
            ) : (
              <div className="text-slate-500">
                <div className="text-4xl mb-2">📷</div>
                <p className="text-sm">Click to upload or drag & drop</p>
                <p className="text-xs mt-1">JPG, PNG, WEBP up to 10 MB</p>
              </div>
            )}
          </div>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="hidden"
            id="crop-image-input"
          />
        </div>

        {error && (
          <div className="bg-red-500/20 border border-red-500/30 rounded-lg px-4 py-3 text-red-300 text-sm">
            {error}
          </div>
        )}

        <button type="submit" disabled={loading} className="btn-primary justify-center disabled:opacity-60 disabled:cursor-not-allowed">
          {loading ? (
            <>
              <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              Analyzing…
            </>
          ) : "🔍 Detect Disease"}
        </button>
      </form>

      {/* Result card */}
      {result && (
        <div className="glass p-6 mt-6 flex flex-col gap-4 border-emerald-700/30">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-widest mb-1">Detected Disease</p>
              <h2 className="text-2xl font-bold text-white">{result.disease_name}</h2>
            </div>
            <span className={severityClass[result.severity] ?? "badge-low"}>
              {result.severity}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex-1 bg-white/10 rounded-full h-2">
              <div
                className="h-2 rounded-full bg-gradient-to-r from-emerald-500 to-green-400"
                style={{ width: `${Math.round(result.confidence * 100)}%` }}
              />
            </div>
            <span className="text-sm text-slate-300 font-medium tabular-nums">
              {Math.round(result.confidence * 100)}% confident
            </span>
          </div>

          <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4">
            <p className="text-xs text-amber-400 font-semibold uppercase tracking-widest mb-2">Advisory</p>
            <p className="text-slate-200 text-sm leading-relaxed">{result.advisory}</p>
          </div>
        </div>
      )}
    </div>
  );
}
