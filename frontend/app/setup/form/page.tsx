"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { HouseholdCreatePayload, createHousehold } from "@/lib/api";
import toast from "react-hot-toast";

const STATES = ["Madhya Pradesh", "Rajasthan", "Uttar Pradesh", "Maharashtra", "Telangana", "Bihar"];
const DISTRICTS: Record<string, string[]> = {
  "Madhya Pradesh": ["Harda", "Bhopal", "Indore", "Jabalpur", "Ujjain", "Hoshangabad"],
  "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Ajmer", "Sikar"],
  "Uttar Pradesh": ["Lucknow", "Varanasi", "Agra", "Meerut", "Kanpur", "Barabanki"],
  "Maharashtra": ["Nagpur", "Pune", "Nashik", "Amravati", "Aurangabad", "Latur"],
  "Telangana": ["Warangal", "Karimnagar", "Nizamabad", "Khammam", "Nalgonda"],
  "Bihar": ["Patna", "Gaya", "Muzaffarpur", "Bhagalpur", "Darbhanga"],
};
const CROPS = ["Soybean", "Wheat", "Mustard", "Cotton", "Maize", "Gram", "Tur Dal", "Onion", "Rice", "Sugarcane"];

interface FamilyMember {
  name: string;
  age: string;
  relation: string;
  is_pregnant: boolean;
}

export default function SetupFormPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  const [form, setForm] = useState({
    name: "",
    state: "Madhya Pradesh",
    district: "Harda",
    crop_primary: "Soybean",
    crop_secondary: "",
    land_acres: "",
  });

  const [members, setMembers] = useState<FamilyMember[]>([
    { name: "", age: "", relation: "self", is_pregnant: false },
  ]);

  // Read PM-KISAN prefill from sessionStorage on mount
  useEffect(() => {
    try {
      const raw = sessionStorage.getItem("voice_prefill");
      if (!raw) return;
      const prefill = JSON.parse(raw);
      setForm(prev => ({
        ...prev,
        name: prefill.name || prev.name,
        state: prefill.state || prev.state,
        district: prefill.district || prev.district,
        crop_primary: prefill.crop_primary || prev.crop_primary,
        land_acres: prefill.land_acres ? String(prefill.land_acres) : prev.land_acres,
      }));
      if (prefill.name) {
        setMembers([{ name: prefill.name, age: "", relation: "self", is_pregnant: false }]);
      }
    } catch {}
  }, []);

  const addMember = () => {
    if (members.length < 4) {
      setMembers([...members, { name: "", age: "", relation: "spouse", is_pregnant: false }]);
    }
  };

  const updateMember = (i: number, field: keyof FamilyMember, val: any) => {
    const updated = [...members];
    updated[i] = { ...updated[i], [field]: val };
    setMembers(updated);
  };

  const handleSubmit = async () => {
    if (!form.name.trim()) { toast.error("Please enter your name"); return; }
    setLoading(true);
    try {
      const payload: HouseholdCreatePayload = {
        ...form,
        land_acres: parseFloat(form.land_acres) || undefined,
        family_members: members
          .filter(m => m.name.trim())
          .map(m => ({
            name: m.name.trim(),
            age: parseInt(m.age, 10) || 30,
            relation: m.relation,
            gender: undefined,
            is_pregnant: m.is_pregnant,
            chronic_conditions: [],
          })),
      };
      const res = await createHousehold(payload);
      localStorage.setItem("household_id", res.household_id);
      localStorage.setItem("household_name", form.name);
      sessionStorage.removeItem("voice_prefill");
      router.push("/dashboard");
    } catch (e: any) {
      toast.error(e.message || "Failed to create profile");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-asha-teal text-white px-4 py-4">
        <div className="flex items-center gap-3">
          <button onClick={() => step > 1 ? setStep(step - 1) : router.back()} className="text-white">
            ←
          </button>
          <div>
            <h1 className="font-bold text-lg">Set Up Your Profile</h1>
            <p className="text-white/70 text-sm">Step {step} of 3</p>
          </div>
        </div>
        <div className="mt-3 flex gap-1">
          {[1,2,3].map(s => (
            <div key={s} className={`h-1 flex-1 rounded-full ${s <= step ? "bg-asha-light" : "bg-white/30"}`} />
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {step === 1 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-gray-800">Basic Information</h2>
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">Your Name *</label>
              <input
                value={form.name}
                onChange={e => setForm({...form, name: e.target.value})}
                placeholder="e.g. Rajesh Kumar"
                className="w-full border border-gray-300 rounded-xl px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-asha-green"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">State</label>
              <select
                value={form.state}
                onChange={e => setForm({...form, state: e.target.value, district: DISTRICTS[e.target.value]?.[0] || ""})}
                className="w-full border border-gray-300 rounded-xl px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-asha-green"
              >
                {STATES.map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">District</label>
              <select
                value={form.district}
                onChange={e => setForm({...form, district: e.target.value})}
                className="w-full border border-gray-300 rounded-xl px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-asha-green"
              >
                {(DISTRICTS[form.state] || []).map(d => <option key={d}>{d}</option>)}
              </select>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-gray-800">Farm Details</h2>
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">Primary Crop</label>
              <select
                value={form.crop_primary}
                onChange={e => setForm({...form, crop_primary: e.target.value})}
                className="w-full border border-gray-300 rounded-xl px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-asha-green"
              >
                {CROPS.map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">Secondary Crop (optional)</label>
              <select
                value={form.crop_secondary}
                onChange={e => setForm({...form, crop_secondary: e.target.value})}
                className="w-full border border-gray-300 rounded-xl px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-asha-green"
              >
                <option value="">None</option>
                {CROPS.filter(c => c !== form.crop_primary).map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">Land (acres)</label>
              <input
                type="number"
                value={form.land_acres}
                onChange={e => setForm({...form, land_acres: e.target.value})}
                placeholder="e.g. 4"
                className="w-full border border-gray-300 rounded-xl px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-asha-green"
              />
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-gray-800">Family Members</h2>
            <p className="text-sm text-gray-500">This helps us personalize health & safety advice.</p>
            {members.map((m, i) => (
              <div key={i} className="bg-white rounded-xl p-4 border border-gray-200 space-y-3">
                <div className="flex gap-2">
                  <input
                    value={m.name}
                    onChange={e => updateMember(i, "name", e.target.value)}
                    placeholder="Name"
                    className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-asha-green"
                  />
                  <input
                    type="number"
                    value={m.age}
                    onChange={e => updateMember(i, "age", e.target.value)}
                    placeholder="Age"
                    className="w-20 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-asha-green"
                  />
                </div>
                <div className="flex gap-2 items-center">
                  <select
                    value={m.relation}
                    onChange={e => updateMember(i, "relation", e.target.value)}
                    className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-asha-green"
                  >
                    {["self","spouse","child","parent","other"].map(r => <option key={r}>{r}</option>)}
                  </select>
                  <label className="flex items-center gap-1.5 text-sm text-gray-600 whitespace-nowrap">
                    <input
                      type="checkbox"
                      checked={m.is_pregnant}
                      onChange={e => updateMember(i, "is_pregnant", e.target.checked)}
                      className="w-4 h-4 accent-asha-green"
                    />
                    Pregnant
                  </label>
                </div>
              </div>
            ))}
            {members.length < 4 && (
              <button onClick={addMember} className="w-full border-2 border-dashed border-gray-300 text-gray-500 py-3 rounded-xl text-sm">
                + Add Family Member
              </button>
            )}
          </div>
        )}
      </div>

      <div className="p-4 bg-white border-t border-gray-200">
        {step < 3 ? (
          <button
            onClick={() => setStep(step + 1)}
            className="w-full bg-asha-green text-white py-4 rounded-2xl text-base font-bold"
          >
            Next →
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full bg-asha-green text-white py-4 rounded-2xl text-base font-bold disabled:opacity-60"
          >
            {loading ? "Setting up..." : "Start Using VikasGPT"}
          </button>
        )}
      </div>
    </div>
  );
}
