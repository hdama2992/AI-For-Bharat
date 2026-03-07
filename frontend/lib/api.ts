const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface FamilyMember {
  name: string;
  age: number;
  relation: string;
  gender?: string | null;
  is_pregnant: boolean;
  chronic_conditions: string[];
}

export interface Household {
  household_id: string;
  name: string;
  phone?: string | null;
  state: string;
  district: string;
  village?: string | null;
  crop_primary?: string | null;
  crop_secondary?: string | null;
  land_acres?: number | null;
  family_members: FamilyMember[];
}

export interface HouseholdCreatePayload {
  name: string;
  phone?: string;
  state: string;
  district: string;
  village?: string;
  crop_primary?: string;
  crop_secondary?: string;
  land_acres?: number;
  family_members: FamilyMember[];
}

export interface ContextInsight {
  type: string;
  severity: string;
  module_trigger: string;
  icon: string;
  message_en: string;
  message_hi: string;
  action_en: string;
  action_hi: string;
}

export interface MandiPrice {
  mandi_name: string;
  mandi_name_hi: string;
  district: string;
  state: string;
  modal_price: number;
  min_price?: number | null;
  max_price?: number | null;
  distance_km: number;
  transport_cost: number;
  net_gain: number;
  last_updated: string;
}

export interface MandiCompareResponse {
  crop: string;
  crop_hi: string;
  msp_price: number;
  home_mandi: MandiPrice;
  alternatives: MandiPrice[];
  best_mandi: string;
  potential_savings: number;
  recommendation: string;
  recommendation_hi: string;
}

export interface OnboardingTurn {
  question: string;
  answer: string;
}

export interface OnboardingExtractResponse {
  household: Partial<HouseholdCreatePayload>;
  confidence: number;
  missing_fields: string[];
}

export interface TriageResult {
  triage_level: "GREEN" | "YELLOW" | "RED";
  confidence_pct: number;
  assessment_summary: string;
  immediate_actions: string[];
  follow_up?: string;
  emergency_number?: string;
  disclaimer: string;
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export async function createHousehold(data: HouseholdCreatePayload) {
  return apiFetch<{ household_id: string }>("/household", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getHousehold(id: string) {
  return apiFetch<Household>(`/household/${id}`);
}

export async function getMandi(crop: string, district: string, householdId?: string) {
  const params = new URLSearchParams({ crop, district });
  if (householdId) params.set("household_id", householdId);
  return apiFetch<MandiCompareResponse>(`/mandi/compare?${params}`);
}

export async function getCrops() {
  return apiFetch<{ crops: string[] }>("/mandi/crops");
}

export async function getDistricts() {
  return apiFetch<{ districts: string[] }>("/mandi/districts");
}

export async function getContextInsights(householdId: string) {
  return apiFetch<ContextInsight[]>(`/household/context/${householdId}`);
}

export async function extractOnboardingData(
  turns: OnboardingTurn[],
  prefill?: Record<string, unknown>,
) {
  return apiFetch<OnboardingExtractResponse>("/household/onboard-extract", {
    method: "POST",
    body: JSON.stringify({ turns, prefill: prefill ?? {} }),
  });
}
