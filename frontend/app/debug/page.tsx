"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { AgentSessionView, listChatSessions } from "@/lib/api";

export default function DebugPage() {
  const router = useRouter();
  const [sessions, setSessions] = useState<AgentSessionView[]>([]);
  const [householdId, setHouseholdId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const id = localStorage.getItem("household_id");
    setHouseholdId(id);
    listChatSessions(id || undefined)
      .then((data) => setSessions(data.sessions))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 pb-8">
      <div className="bg-asha-teal text-white px-4 pt-12 pb-5">
        <div className="flex items-center gap-3">
          <button onClick={() => router.back()} className="text-xl">←</button>
          <div>
            <h1 className="font-bold text-xl">🧠 Agent Debug</h1>
            <p className="text-white/70 text-sm">Supervisor + specialist routing</p>
          </div>
        </div>
      </div>

      <div className="px-4 py-4">
        <div className="bg-white rounded-2xl p-4 border border-gray-200 mb-4">
          <p className="text-xs uppercase tracking-wide text-sky-700 font-semibold">Demo view</p>
          <p className="text-sm text-gray-600 mt-1">
            Household: {householdId || "not selected"}
          </p>
          <p className="text-sm text-gray-600">
            Showing the latest routed sessions with Bedrock model and handoff reason.
          </p>
        </div>

        {loading ? (
          <div className="text-center text-gray-500 py-8">Loading sessions...</div>
        ) : !sessions.length ? (
          <div className="bg-white rounded-2xl p-4 border border-gray-200 text-sm text-gray-500">
            No sessions yet. Use onboarding, mandi, health, or WhatsApp to generate one.
          </div>
        ) : (
          <div className="space-y-3">
            {sessions.map((session) => {
              const latestRoute = session.routing_history[session.routing_history.length - 1];
              return (
                <div key={session.session_id} className="bg-white rounded-2xl p-4 border border-gray-200">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold text-gray-800">{session.active_agent.toUpperCase()}</p>
                      <p className="text-xs text-gray-400">{session.session_id}</p>
                    </div>
                    <span className="bg-sky-100 text-sky-700 text-xs px-2 py-1 rounded-full font-medium">
                      {session.channel}
                    </span>
                  </div>
                  {latestRoute && (
                    <div className="mt-3 text-sm text-gray-700 space-y-1">
                      <p><span className="font-medium">Model:</span> {latestRoute.model || "fallback"}</p>
                      <p><span className="font-medium">Source:</span> {latestRoute.source}</p>
                      <p><span className="font-medium">Confidence:</span> {(latestRoute.confidence * 100).toFixed(0)}%</p>
                      <p><span className="font-medium">Reason:</span> {latestRoute.handoff_reason}</p>
                    </div>
                  )}
                  {session.summary?.text && (
                    <div className="mt-3 rounded-xl bg-gray-50 p-3 text-sm text-gray-600">
                      {session.summary.text}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

