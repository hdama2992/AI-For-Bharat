"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getMandi, getCrops } from "@/lib/api";
import toast from "react-hot-toast";

const DISTRICTS: Record<string, string[]> = {
  "Madhya Pradesh": ["Harda", "Bhopal", "Indore", "Jabalpur", "Hoshangabad"],
  "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Sikar"],
  "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi", "Barabanki"],
  "Maharashtra": ["Nagpur", "Pune", "Amravati"],
  "Telangana": ["Warangal", "Karimnagar"],
  "Bihar": ["Patna", "Gaya"],
};

const ALL_DISTRICTS = Object.values(DISTRICTS).flat();

export default function MandiPage() {
  const router = useRouter();
  const [crop, setCrop] = useState("Soybean");
  const [district, setDistrict] = useState("Harda");
  const [crops, setCrops] = useState<string[]>([]);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [householdId, setHouseholdId] = useState<string | null>(null);

  useEffect(() => {
    const id = localStorage.getItem("household_id");
    setHouseholdId(id);
    getCrops().then(d => setCrops(d.crops)).catch(() => {});
  }, []);

  const handleCompare = async () => {
    setLoading(true);
    setResult(null);
    try {
      const data = await getMandi(crop, district, householdId || undefined);
      setResult(data);
    } catch (e: any) {
      toast.error(e.message || "Failed to fetch Mandi prices");
    } finally {
      setLoading(false);
    }
  };

  const bestMandi = result?.all_mandis?.reduce((best: any, m: any) =>
    m.net_price > (best?.net_price || 0) ? m : best, null);

  return (
    <div className="min-h-screen bg-gray-100 pb-8">
      {/* Header */}
      <div className="bg-asha-teal text-white px-4 pt-12 pb-5">
        <div className="flex items-center gap-3 mb-3">
          <button onClick={() => router.back()} className="text-white text-xl">←</button>
          <div>
            <h1 className="font-bold text-xl">🌾 Mandi Advisor</h1>
            <p className="text-white/70 text-sm">मंडी मूल्य तुलनाकर्ता</p>
          </div>
        </div>
      </div>

      <div className="px-4 py-4 space-y-4">
        {/* Inputs */}
        <div className="bg-white rounded-2xl p-4 border border-gray-200 space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">Crop / फसल</label>
            <select
              value={crop}
              onChange={e => setCrop(e.target.value)}
              className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-asha-green"
            >
              {(crops.length ? crops : ["Soybean","Wheat","Mustard","Cotton","Maize","Gram"]).map(c => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">District / जिला</label>
            <select
              value={district}
              onChange={e => setDistrict(e.target.value)}
              className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-asha-green"
            >
              {ALL_DISTRICTS.map(d => <option key={d}>{d}</option>)}
            </select>
          </div>
          <button
            onClick={handleCompare}
            disabled={loading}
            className="w-full bg-asha-green text-white py-3.5 rounded-xl font-bold text-base disabled:opacity-60"
          >
            {loading ? "Comparing Mandis..." : "Compare Prices 🔍"}
          </button>
        </div>

        {/* Loading */}
        {loading && (
          <div className="text-center py-8">
            <div className="text-4xl mb-2 animate-bounce">🌾</div>
            <p className="text-gray-500">Checking prices across Mandis...</p>
            <p className="text-gray-400 text-sm">मंडियों में भाव जांचा जा रहा है...</p>
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <>
            {/* Savings callout */}
            <div className={`rounded-2xl p-4 ${result.best_net_gain > 0 ? "bg-green-50 border border-green-200" : "bg-blue-50 border border-blue-200"}`}>
              <p className={`font-bold text-base ${result.best_net_gain > 0 ? "text-green-700" : "text-blue-700"}`}>
                {result.best_net_gain > 0 ? "💡 Better Price Available!" : "✅ Local Mandi is Best"}
              </p>
              <p className={`text-sm mt-1 ${result.best_net_gain > 0 ? "text-green-600" : "text-blue-600"}`}>
                {result.savings_message_en}
              </p>
              <p className={`text-xs mt-1 ${result.best_net_gain > 0 ? "text-green-500" : "text-blue-500"}`}>
                {result.savings_message_hi}
              </p>
              {result.msp && (
                <p className="text-xs text-gray-400 mt-2">MSP 2025-26: ₹{result.msp}/qtl</p>
              )}
            </div>

            {/* Mandi table */}
            <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-100">
                <p className="font-semibold text-gray-700">{result.crop} Prices — {result.district}</p>
                <p className="text-xs text-gray-400">Updated: {result.last_updated}</p>
              </div>
              <div className="divide-y divide-gray-100">
                {result.all_mandis?.map((mandi: any, i: number) => {
                  const isBest = mandi.mandi_name === result.best_mandi && result.best_net_gain > 0;
                  return (
                    <div key={i} className={`px-4 py-3 ${isBest ? "bg-green-50" : ""}`}>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-gray-800 text-sm">{mandi.mandi_name}</p>
                            {isBest && (
                              <span className="bg-green-500 text-white text-xs px-2 py-0.5 rounded-full font-medium">Best</span>
                            )}
                          </div>
                          <p className="text-xs text-gray-500 mt-0.5">
                            {mandi.distance_km === 0 ? "Your local Mandi" : `${mandi.distance_km} km away`}
                            {mandi.transport_cost_per_quintal > 0 && ` • ₹${mandi.transport_cost_per_quintal}/qtl transport`}
                          </p>
                          <p className="text-xs text-gray-400">
                            Trend: {mandi.trend_7d} (7 days)
                            {mandi.arrivals_tonnes && ` • ${mandi.arrivals_tonnes}t arrivals`}
                          </p>
                        </div>
                        <div className="text-right ml-3">
                          <p className="font-bold text-gray-800">₹{mandi.modal_price}</p>
                          <p className="text-xs text-gray-500">₹{mandi.net_price} net</p>
                          {mandi.net_gain_vs_local > 0 && (
                            <p className="text-xs text-green-600 font-medium">+₹{mandi.net_gain_vs_local}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <p className="text-xs text-gray-400 text-center px-4">
              Prices simulated from Agmarknet patterns. Connect eNAM API for live data.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
