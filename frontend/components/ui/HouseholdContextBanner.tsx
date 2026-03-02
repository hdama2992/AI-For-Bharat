"use client";
import { useEffect, useState } from "react";
import { getContextInsights } from "@/lib/api";

const ICON_MAP: Record<string, string> = {
  shield: "🛡️",
  rupee: "💰",
  heart: "❤️",
  calendar: "📅",
};

const SEVERITY_STYLES: Record<string, string> = {
  critical: "bg-red-50 border-red-300",
  warning: "bg-amber-50 border-amber-300",
  info: "bg-blue-50 border-blue-300",
};

const SEVERITY_TEXT: Record<string, string> = {
  critical: "text-red-700",
  warning: "text-amber-700",
  info: "text-blue-700",
};

interface Insight {
  type: string;
  severity: string;
  module_trigger: string;
  icon: string;
  message_en: string;
  message_hi: string;
  action_en: string;
  action_hi: string;
}

export default function HouseholdContextBanner({
  householdId,
  lang = "en",
}: {
  householdId: string;
  lang?: "en" | "hi";
}) {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [open, setOpen] = useState(true);

  const fetchInsights = async () => {
    try {
      const data = await getContextInsights(householdId);
      setInsights(data);
    } catch {}
  };

  useEffect(() => {
    fetchInsights();
    const interval = setInterval(fetchInsights, 30000);
    return () => clearInterval(interval);
  }, [householdId]);

  if (!insights.length) return null;

  return (
    <div className="mx-4 mt-3">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between bg-amber-50 border border-amber-300 rounded-t-xl px-3 py-2 text-left"
      >
        <span className="text-amber-700 text-sm font-semibold flex items-center gap-1.5">
          ⚡ Household Insights ({insights.length})
        </span>
        <span className="text-amber-600 text-xs">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="border-x border-b border-amber-300 rounded-b-xl overflow-hidden divide-y divide-amber-200">
          {insights.map((ins, i) => (
            <div key={i} className={`p-3 ${SEVERITY_STYLES[ins.severity] || "bg-gray-50"}`}>
              <div className="flex items-start gap-2">
                <span className="text-lg mt-0.5">{ICON_MAP[ins.icon] || "📌"}</span>
                <div className="flex-1">
                  <p className={`text-sm font-medium ${SEVERITY_TEXT[ins.severity]}`}>
                    {lang === "hi" ? ins.message_hi : ins.message_en}
                  </p>
                  <p className={`text-xs mt-0.5 ${SEVERITY_TEXT[ins.severity]} opacity-80`}>
                    → {lang === "hi" ? ins.action_hi : ins.action_en}
                  </p>
                  <span className="inline-block mt-1 text-xs bg-white/70 px-2 py-0.5 rounded-full text-gray-500">
                    {ins.module_trigger} module
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
