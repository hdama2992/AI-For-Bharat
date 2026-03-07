"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import toast from "react-hot-toast";

const MOCK_PMKISAN: Record<string, object> = {
  "9876543210": {
    name: "Ramesh Yadav",
    state: "Madhya Pradesh",
    district: "Harda",
    crop_primary: "Soybean",
    land_acres: 3.5,
  },
  "9123456789": {
    name: "Sunita Devi",
    state: "Rajasthan",
    district: "Sikar",
    crop_primary: "Mustard",
    land_acres: 2.0,
  },
};

const GENERIC_PREFILL = {
  state: "Madhya Pradesh",
  district: "Harda",
};

export default function SetupEntryPage() {
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [lookupState, setLookupState] = useState<"idle" | "loading" | "done">("idle");
  const [prefillName, setPrefillName] = useState("");

  const handleVoiceStart = () => {
    router.push("/setup/voice");
  };

  const handlePhoneLookup = async () => {
    if (phone.length < 10) {
      toast.error("Please enter a 10-digit phone number");
      return;
    }
    setLookupState("loading");

    // Simulate 2-second PM-KISAN lookup
    await new Promise(r => setTimeout(r, 2000));

    const data = MOCK_PMKISAN[phone] ?? { ...GENERIC_PREFILL };
    sessionStorage.setItem("voice_prefill", JSON.stringify(data));

    const name = (data as any).name || "";
    if (name) setPrefillName(name);

    setLookupState("done");

    // Short pause so user sees the success state, then navigate
    await new Promise(r => setTimeout(r, 800));
    router.push("/setup/voice");
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-asha-teal text-white px-4 pt-12 pb-6 text-center">
        <div className="text-5xl mb-3">🌿</div>
        <h1 className="text-2xl font-bold">VikasGPT में आपका स्वागत है</h1>
        <p className="text-white/70 text-sm mt-1">Welcome to your AI farming companion</p>
      </div>

      <div className="flex-1 p-5 space-y-6">
        {/* PM-KISAN Lookup */}
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 space-y-4">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🏛️</span>
            <div>
              <h2 className="font-bold text-gray-800">PM-KISAN से जोड़ें</h2>
              <p className="text-xs text-gray-500">Auto-fill your profile using government records</p>
            </div>
          </div>

          <div className="flex gap-2">
            <input
              type="tel"
              value={phone}
              onChange={e => setPhone(e.target.value.replace(/\D/g, "").slice(0, 10))}
              placeholder="मोबाइल नंबर / Mobile number"
              className="flex-1 border border-gray-300 rounded-xl px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-asha-green"
              disabled={lookupState !== "idle"}
            />
            <button
              onClick={handlePhoneLookup}
              disabled={lookupState !== "idle" || phone.length < 10}
              className="bg-asha-teal text-white px-4 py-3 rounded-xl font-semibold text-sm disabled:opacity-50 flex-shrink-0"
            >
              {lookupState === "loading" ? (
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin inline-block" />
                  खोज रहे...
                </span>
              ) : lookupState === "done" ? (
                <span className="text-green-300">✓ मिला!</span>
              ) : (
                "खोजें"
              )}
            </button>
          </div>

          {lookupState === "done" && prefillName && (
            <div className="bg-green-50 border border-green-200 rounded-xl px-4 py-3 text-sm text-green-800">
              PM-KISAN record मिला: <strong>{prefillName}</strong>. आवाज़ से पुष्टि करें।
            </div>
          )}
          {lookupState === "done" && !prefillName && (
            <div className="bg-blue-50 border border-blue-200 rounded-xl px-4 py-3 text-sm text-blue-800">
              Record नहीं मिला। आप आवाज़ से पूरी जानकारी दे सकते हैं।
            </div>
          )}

          {phone.length === 10 && lookupState === "idle" && (
            <p className="text-xs text-gray-400 text-center">
              Try demo numbers: 9876543210 or 9123456789
            </p>
          )}
        </div>

        {/* Divider */}
        <div className="flex items-center gap-3">
          <div className="flex-1 h-px bg-gray-200" />
          <span className="text-gray-400 text-sm">या / or</span>
          <div className="flex-1 h-px bg-gray-200" />
        </div>

        {/* Voice start */}
        <div className="space-y-3">
          <button
            onClick={handleVoiceStart}
            className="w-full bg-asha-green text-white py-5 rounded-2xl text-lg font-bold shadow-md active:scale-[0.98] transition-transform flex items-center justify-center gap-3"
          >
            <span className="text-2xl">🎤</span>
            आवाज़ से शुरू करें
          </button>
          <p className="text-center text-xs text-gray-400">
            विकास हिंदी में सवाल पूछेगा — बस बोलिए
          </p>
        </div>

        {/* Text form fallback */}
        <div className="text-center">
          <Link
            href="/setup/form"
            className="text-asha-teal text-sm underline underline-offset-2"
          >
            Prefer typing? Fill the form instead →
          </Link>
        </div>
      </div>

      {/* Demo note */}
      <div className="px-5 pb-8 text-center">
        <p className="text-xs text-gray-400">
          PM-KISAN lookup is a demo simulation. Real integration requires government partnership.
        </p>
      </div>
    </div>
  );
}
