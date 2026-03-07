const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    let message = `HTTP ${res.status}`;
    if (typeof err.detail === "string") {
      message = err.detail;
    } else if (Array.isArray(err.detail)) {
      message = err.detail.map((e: any) => e.msg || JSON.stringify(e)).join(", ");
    }
    throw new Error(message);
  }
  return res.json();
}

export async function createHousehold(data: object) {
  return apiFetch<{ household_id: string }>("/household", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getHousehold(id: string) {
  return apiFetch<any>(`/household/${id}`);
}

export async function getMandi(crop: string, district: string, householdId?: string) {
  const params = new URLSearchParams({ crop, district });
  if (householdId) params.set("household_id", householdId);
  return apiFetch<any>(`/mandi/compare?${params}`);
}

export async function getCrops() {
  return apiFetch<{ crops: string[] }>("/mandi/crops");
}

export async function getDistricts() {
  return apiFetch<{ districts: string[] }>("/mandi/districts");
}

export async function getContextInsights(householdId: string) {
  return apiFetch<any[]>(`/household/context/${householdId}`);
}

export async function extractOnboardingData(
  turns: { question: string; answer: string }[],
  prefill?: Record<string, any>,
) {
  return apiFetch<{
    household: any;
    confidence: number;
    missing_fields: string[];
  }>("/household/onboard-extract", {
    method: "POST",
    body: JSON.stringify({ turns, prefill: prefill ?? {} }),
  });
}

export function streamHealthChat(
  payload: object,
  onChunk: (text: string) => void,
  onTriage: (triage: any) => void,
  onDone: () => void,
  onError: (e: Error) => void,
): AbortController {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${BASE}/health/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") {
              onDone();
            } else {
              onChunk(data);
            }
          } else if (line.startsWith("event: triage")) {
            // next line will be data:
          } else if (line.startsWith("data: ") && buffer.includes('"triage"')) {
            try {
              const parsed = JSON.parse(line.slice(6));
              if (parsed.triage) onTriage(parsed.triage);
            } catch {}
          }
        }
      }
      onDone();
    } catch (e: any) {
      if (e.name !== "AbortError") onError(e);
    }
  })();

  return controller;
}
