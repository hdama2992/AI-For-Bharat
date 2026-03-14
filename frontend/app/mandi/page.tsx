"use client";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { MandiCompareResponse, MandiPrice, getCrops, getDistricts, getMandi } from "@/lib/api";
import toast from "react-hot-toast";

export default function MandiPage() {
  const router = useRouter();
  const [crop, setCrop] = useState("Soybean");
  const [district, setDistrict] = useState("Harda");
  const [crops, setCrops] = useState<string[]>([]);
  const [districts, setDistricts] = useState<string[]>([]);
  const [result, setResult] = useState<MandiCompareResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [householdId, setHouseholdId] = useState<string | null>(null);

  useEffect(() => {
    const id = localStorage.getItem("household_id");
    setHouseholdId(id);

    getCrops()
      .then((data) => setCrops(data.crops))
      .catch(() => {});

    getDistricts()
      .then((data) => setDistricts(data.districts))
      .catch(() => {});
  }, []);

  const allMandis = useMemo<MandiPrice[]>(() => {
    if (!result) return [];
    return [result.home_mandi, ...result.alternatives];
  }, [result]);

  const handleCompare = async () => {
    setLoading(true);
    setResult(null);
    try {
      const data = await getMandi(crop, district, householdId || undefined);
      setResult(data);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Failed to fetch Mandi prices";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 pb-8">
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
        <div className="bg-white rounded-2xl p-4 border border-gray-200 space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">Crop / फसल</label>
            <select
              value={crop}
              onChange={(e) => setCrop(e.target.value)}
              className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-asha-green"
            >
              {(crops.length ? crops : ["Soybean", "Wheat", "Mustard", "Cotton", "Maize", "Gram"]).map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">District / जिला</label>
            <select
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-asha-green"
            >
              {(districts.length ? districts : ["Harda", "Bhopal", "Indore"]).map((item) => (
                <option key={item}>{item}</option>
              ))}
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

        {loading && (
          <div className="text-center py-8">
            <div className="text-4xl mb-2 animate-bounce">🌾</div>
            <p className="text-gray-500">Checking prices across Mandis...</p>
            <p className="text-gray-400 text-sm">मंडियों में भाव जांचा जा रहा है...</p>
          </div>
        )}

        {result && !loading && (
          <>
            <div className={`rounded-2xl p-4 ${result.potential_savings > 0 ? "bg-green-50 border border-green-200" : "bg-blue-50 border border-blue-200"}`}>
              <p className={`font-bold text-base ${result.potential_savings > 0 ? "text-green-700" : "text-blue-700"}`}>
                {result.potential_savings > 0 ? "💡 Better Price Available!" : "✅ Local Mandi is Best"}
              </p>
              <p className={`text-sm mt-1 ${result.potential_savings > 0 ? "text-green-600" : "text-blue-600"}`}>
                {result.recommendation}
              </p>
              <p className={`text-xs mt-1 ${result.potential_savings > 0 ? "text-green-500" : "text-blue-500"}`}>
                {result.recommendation_hi}
              </p>
              <p className="text-xs text-gray-400 mt-2">MSP 2025-26: ₹{result.msp_price}/qtl</p>
            </div>

            <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-100">
                <p className="font-semibold text-gray-700">{result.crop} Prices</p>
                <p className="text-xs text-gray-400">Best market: {result.best_mandi}</p>
              </div>
              <div className="divide-y divide-gray-100">
                {allMandis.map((mandi, index) => {
                  const isBest = mandi.mandi_name === result.best_mandi && result.potential_savings > 0;
                  const isHome = mandi.distance_km === 0;
                  const netPrice = Math.round(mandi.modal_price - mandi.transport_cost);
                  return (
                    <div key={`${mandi.mandi_name}-${index}`} className={`px-4 py-3 ${isBest ? "bg-green-50" : ""}`}>
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-gray-800 text-sm">{mandi.mandi_name}</p>
                            {isHome && (
                              <span className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full font-medium">Local</span>
                            )}
                            {isBest && (
                              <span className="bg-green-500 text-white text-xs px-2 py-0.5 rounded-full font-medium">Best</span>
                            )}
                          </div>
                          <p className="text-xs text-gray-500 mt-0.5">
                            {isHome ? "Your local Mandi" : `${mandi.distance_km} km away`}
                            {!isHome && ` • ₹${mandi.transport_cost}/qtl transport`}
                          </p>
                          <p className="text-xs text-gray-400">
                            {mandi.district}, {mandi.state}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-gray-800">₹{mandi.modal_price}</p>
                          <p className="text-xs text-gray-500">₹{netPrice} net</p>
                          {mandi.net_gain > 0 && (
                            <p className="text-xs text-green-600 font-medium">+₹{Math.round(mandi.net_gain)}/qtl</p>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <p className="text-xs text-gray-400 text-center px-4">
              Prices use prototype mock data. For the demo, the recommendation already accounts for transport cost.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
