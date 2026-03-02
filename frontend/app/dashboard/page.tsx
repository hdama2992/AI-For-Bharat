"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import HouseholdContextBanner from "@/components/ui/HouseholdContextBanner";
import { getHousehold } from "@/lib/api";

const MODULES = [
  {
    href: "/mandi",
    icon: "🌾",
    title: "Mandi Advisor",
    titleHi: "मंडी सलाहकार",
    desc: "Compare prices across nearby Mandis and maximize profit",
    descHi: "आस-पास की मंडियों में सबसे अच्छा भाव पाएं",
    cta: "Check Prices",
    ctaHi: "भाव देखें",
    bg: "bg-green-50",
    border: "border-green-200",
    iconBg: "bg-green-100",
  },
  {
    href: "/pest",
    icon: "🔬",
    title: "Pest-Vision",
    titleHi: "कीट-दृष्टि",
    desc: "Identify crop diseases from a photo — safe treatment advice",
    descHi: "फोटो से फसल की बीमारी पहचानें, सुरक्षित उपचार पाएं",
    cta: "Analyze Crop",
    ctaHi: "फसल जांचें",
    bg: "bg-yellow-50",
    border: "border-yellow-200",
    iconBg: "bg-yellow-100",
  },
  {
    href: "/health",
    icon: "❤️",
    title: "Health Triage",
    titleHi: "स्वास्थ्य जांच",
    desc: "Describe symptoms, get Green / Yellow / Red guidance",
    descHi: "लक्षण बताएं, तुरंत Green/Yellow/Red मार्गदर्शन पाएं",
    cta: "Check Symptoms",
    ctaHi: "लक्षण जांचें",
    bg: "bg-red-50",
    border: "border-red-200",
    iconBg: "bg-red-100",
  },
];

export default function DashboardPage() {
  const router = useRouter();
  const [householdId, setHouseholdId] = useState<string | null>(null);
  const [household, setHousehold] = useState<any>(null);
  const [lang, setLang] = useState<"en" | "hi">("en");

  useEffect(() => {
    const id = localStorage.getItem("household_id");
    if (!id) { router.replace("/"); return; }
    setHouseholdId(id);
    getHousehold(id).then(setHousehold).catch(() => {});
  }, [router]);

  if (!householdId) return null;

  const name = household?.name || localStorage.getItem("household_name") || "Farmer";
  const crop = household?.crop_primary || "Crop";

  return (
    <div className="min-h-screen bg-gray-100 pb-6">
      {/* Header */}
      <div className="bg-asha-teal text-white px-4 pt-12 pb-6">
        <div className="flex items-center justify-between mb-1">
          <div>
            <p className="text-white/70 text-sm">Namaste 🙏</p>
            <h1 className="text-xl font-bold">{name}</h1>
            <p className="text-white/60 text-sm">{crop} • {household?.district || ""}</p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <button
              onClick={() => setLang(l => l === "en" ? "hi" : "en")}
              className="bg-white/20 text-white text-xs px-3 py-1.5 rounded-full"
            >
              {lang === "en" ? "हिंदी" : "English"}
            </button>
            <button
              onClick={() => { localStorage.clear(); router.push("/"); }}
              className="text-white/40 text-xs"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Context Banner */}
      <HouseholdContextBanner householdId={householdId} lang={lang} />

      {/* Module cards */}
      <div className="px-4 mt-4 space-y-3">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide px-1">
          {lang === "en" ? "Your Services" : "आपकी सेवाएं"}
        </h2>
        {MODULES.map((m) => (
          <Link
            key={m.href}
            href={m.href}
            className={`flex items-center gap-4 p-4 rounded-2xl border ${m.bg} ${m.border} active:scale-95 transition-transform`}
          >
            <div className={`w-14 h-14 ${m.iconBg} rounded-xl flex items-center justify-center text-3xl flex-shrink-0`}>
              {m.icon}
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-bold text-gray-800 text-base">
                {lang === "en" ? m.title : m.titleHi}
              </h3>
              <p className="text-gray-500 text-xs mt-0.5 leading-relaxed">
                {lang === "en" ? m.desc : m.descHi}
              </p>
            </div>
            <div className="text-gray-400 flex-shrink-0">›</div>
          </Link>
        ))}
      </div>

      {/* Footer */}
      <div className="mt-6 px-4">
        <div className="bg-white rounded-xl p-4 border border-gray-200 text-center">
          <p className="text-xs text-gray-400">Powered by Amazon Bedrock + ICAR + ICMR</p>
          <p className="text-xs text-gray-300 mt-1">Built for AI for Bharat Hackathon 2026</p>
        </div>
      </div>
    </div>
  );
}
