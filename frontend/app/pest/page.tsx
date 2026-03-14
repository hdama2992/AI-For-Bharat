"use client";
import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const CROPS = ["Soybean", "Wheat", "Mustard", "Cotton", "Maize", "Gram", "Rice", "Tomato", "Onion", "Sugarcane"];

const SEVERITY_COLOR: Record<string, string> = {
  Low: "bg-green-100 text-green-700 border-green-300",
  Medium: "bg-yellow-100 text-yellow-700 border-yellow-300",
  High: "bg-red-100 text-red-700 border-red-300",
};

export default function PestPage() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const [image, setImage] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [crop, setCrop] = useState("Soybean");
  const [symptoms, setSymptoms] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [householdId, setHouseholdId] = useState<string>("demo-rajesh-001");

  useEffect(() => {
    const id = localStorage.getItem("household_id");
    if (id) setHouseholdId(id);
  }, []);

  const handleFile = (file: File) => {
    if (!file.type.startsWith("image/")) { toast.error("Please upload an image"); return; }
    setImage(file);
    setResult(null);
    const url = URL.createObjectURL(file);
    setPreview(url);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleAnalyze = async () => {
    if (!image) { toast.error("Please upload a crop photo first"); return; }
    setLoading(true);
    setResult(null);
    try {
      const form = new FormData();
      form.append("image", image);
      form.append("crop_type", crop);
      form.append("household_id", householdId);
      form.append("symptoms_description", symptoms);

      const res = await fetch(`${BASE}/pest/analyze`, { method: "POST", body: form });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setResult(data);
    } catch (e: any) {
      toast.error(e.message || "Analysis failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 pb-8">
      {/* Header */}
      <div className="bg-asha-teal text-white px-4 pt-12 pb-5">
        <div className="flex items-center gap-3">
          <button onClick={() => router.back()} className="text-white text-xl">←</button>
          <div>
            <h1 className="font-bold text-xl">🔬 Pest-Vision</h1>
            <p className="text-white/70 text-sm">AI Crop Disease Identification</p>
          </div>
        </div>
      </div>

      <div className="px-4 py-4 space-y-4">
        {/* Upload zone */}
        <div
          onDrop={handleDrop}
          onDragOver={e => e.preventDefault()}
          onClick={() => !loading && fileRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl flex flex-col items-center justify-center cursor-pointer transition-colors
            ${preview ? "border-asha-green bg-green-50" : "border-gray-300 bg-white hover:border-asha-green hover:bg-green-50"}`}
          style={{ minHeight: preview ? "auto" : "200px" }}
        >
          {preview ? (
            <div className="w-full">
              <img src={preview} alt="Crop" className="w-full rounded-2xl object-cover max-h-64" />
              <p className="text-center text-xs text-gray-500 py-2">Tap to change photo</p>
            </div>
          ) : (
            <div className="text-center p-8">
              <div className="text-5xl mb-3">📸</div>
              <p className="text-gray-600 font-medium">Tap to take / upload photo</p>
              <p className="text-gray-400 text-sm mt-1">फसल की क्षतिग्रस्त पत्ती की फोटो लें</p>
            </div>
          )}
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            capture="environment"
            className="hidden"
            onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
        </div>

        {/* Crop + symptoms */}
        <div className="bg-white rounded-2xl p-4 border border-gray-200 space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">Crop Type / फसल का नाम</label>
            <select
              value={crop}
              onChange={e => setCrop(e.target.value)}
              className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-asha-green"
            >
              {CROPS.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">Describe what you see (optional)</label>
            <input
              value={symptoms}
              onChange={e => setSymptoms(e.target.value)}
              placeholder="e.g. yellow spots, holes in leaves, wilting..."
              className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-asha-green"
            />
          </div>
          <button
            onClick={handleAnalyze}
            disabled={loading || !image}
            className="w-full bg-asha-green text-white py-3.5 rounded-xl font-bold text-base disabled:opacity-50"
          >
            {loading ? "Analyzing with AI..." : "Analyze Crop 🔍"}
          </button>
        </div>

        {/* Loading */}
        {loading && (
          <div className="bg-white rounded-2xl p-6 border border-gray-200 text-center">
            <div className="text-4xl mb-3 animate-bounce">🌿</div>
            <p className="text-gray-600 font-medium">Vikas is analyzing your crop...</p>
            <p className="text-gray-400 text-sm mt-1">Checking ICAR pest database</p>
            <div className="flex justify-center gap-1.5 mt-4">
              {[0,1,2].map(i => (
                <div key={i} className="w-2 h-2 bg-asha-green rounded-full typing-dot" style={{animationDelay: `${i*0.2}s`}} />
              ))}
            </div>
          </div>
        )}

        {/* Result */}
        {result && !loading && (
          <div className="space-y-3">
            {/* Safety alert - shown FIRST if present */}
            {result.household_safety_alert && (
              <div className="bg-red-50 border-2 border-red-400 rounded-2xl p-4 animate-pulse-border">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">🛡️</span>
                  <div>
                    <p className="font-bold text-red-700 text-base">HOUSEHOLD SAFETY ALERT</p>
                    <p className="text-red-600 text-sm mt-1">{result.household_safety_alert}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Main diagnosis */}
            <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
              <div className="bg-asha-teal px-4 py-3">
                <p className="text-white font-bold text-lg">{result.disease_identified}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${SEVERITY_COLOR[result.severity] || "bg-gray-100 text-gray-600"}`}>
                    {result.severity} Severity
                  </span>
                  <span className="text-white/70 text-xs">{result.confidence_pct}% confidence</span>
                  <span className="text-white/70 text-xs">• {result.primary_cause}</span>
                </div>
              </div>

              {/* Recommended treatment */}
              <div className="p-4 border-b border-gray-100">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Recommended Treatment</p>
                <p className="font-bold text-gray-800">{result.treatment?.recommended_pesticide}</p>
                <p className="text-gray-500 text-sm">{result.treatment?.active_ingredient}</p>
                <div className="mt-3 grid grid-cols-2 gap-2">
                  <div className="bg-gray-50 rounded-lg p-2">
                    <p className="text-xs text-gray-400">Dosage</p>
                    <p className="text-sm font-medium text-gray-700">{result.treatment?.dosage}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-2">
                    <p className="text-xs text-gray-400">Frequency</p>
                    <p className="text-sm font-medium text-gray-700">{result.treatment?.frequency}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-2">
                    <p className="text-xs text-gray-400">Cost (approx)</p>
                    <p className="text-sm font-medium text-gray-700">₹{result.treatment?.cost_estimate_inr}/acre</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-2">
                    <p className="text-xs text-gray-400">Safe interval</p>
                    <p className="text-sm font-medium text-gray-700">{result.treatment?.safety_interval_days || "—"} days</p>
                  </div>
                </div>
                <p className="text-xs text-gray-400 mt-2">Application: {result.treatment?.application_method}</p>
              </div>

              {/* Organic alternative */}
              {result.alternative_treatment && (
                <div className="p-4 bg-green-50 border-b border-gray-100">
                  <p className="text-xs font-semibold text-green-600 uppercase tracking-wide mb-1">🌿 Organic Alternative</p>
                  <p className="font-medium text-green-800">{result.alternative_treatment.name}</p>
                  <p className="text-green-600 text-sm">{result.alternative_treatment.dosage}</p>
                  {result.alternative_treatment.cost_estimate_inr && (
                    <p className="text-green-500 text-xs mt-1">~₹{result.alternative_treatment.cost_estimate_inr}/acre</p>
                  )}
                </div>
              )}

              {/* Prevention tips */}
              {result.prevention_tips?.length > 0 && (
                <div className="p-4">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Prevention Tips</p>
                  <ul className="space-y-1">
                    {result.prevention_tips.map((tip: string, i: number) => (
                      <li key={i} className="flex gap-2 text-sm text-gray-600">
                        <span className="text-asha-green flex-shrink-0">✓</span>
                        {tip}
                      </li>
                    ))}
                  </ul>
                  <p className="text-xs text-gray-300 mt-3">Sources: {result.sources?.join(", ")}</p>
                </div>
              )}
            </div>

            <button
              onClick={() => { setResult(null); setImage(null); setPreview(null); setSymptoms(""); }}
              className="w-full border border-gray-300 text-gray-600 py-3 rounded-xl text-sm"
            >
              Analyze Another Photo
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
