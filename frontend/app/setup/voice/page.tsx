"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { FamilyMember, HouseholdCreatePayload, createHousehold, extractOnboardingData } from "@/lib/api";

// ─── Question script ─────────────────────────────────────────────────────────

interface Question {
  id: string;
  text: string;                          // base question
  confirmText?: (val: string) => string; // used when prefill provides a value
}

const QUESTIONS: Question[] = [
  {
    id: "name",
    text: "नमस्ते! मैं आशा हूं। पहले मुझे अपना नाम बताइए।",
    confirmText: (v) => `PM-KISAN record से मिला कि आपका नाम ${v} है — क्या यह सही है?`,
  },
  {
    id: "location",
    text: "आप किस राज्य और जिले में रहते हैं?",
    confirmText: (v) => `क्या आप ${v} में रहते हैं — यह सही है?`,
  },
  {
    id: "crop",
    text: "आपकी मुख्य फसल कौन सी है?",
    confirmText: (v) => `PM-KISAN के अनुसार आपकी मुख्य फसल ${v} है — क्या सही है?`,
  },
  {
    id: "land",
    text: "आपके पास कितनी ज़मीन है, एकड़ में?",
    confirmText: (v) => `आपके पास ${v} एकड़ ज़मीन है — क्या यह सही है?`,
  },
  {
    id: "family",
    text: "परिवार में कौन-कौन हैं? नाम, उम्र, और रिश्ता बताइए।",
  },
  {
    id: "pregnancy",
    text: "क्या घर में कोई महिला गर्भवती है?",
  },
];

type VoiceStep = "idle" | "speaking" | "listening" | "processing" | "confirming" | "submitting";

// ─── TTS helper ──────────────────────────────────────────────────────────────

function speak(text: string, onEnd: () => void) {
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "hi-IN";
  u.rate = 0.9;
  u.pitch = 1.05;
  u.onend = onEnd;
  u.onerror = onEnd; // still advance on error
  window.speechSynthesis.speak(u);
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function VoiceOnboardPage() {
  const router = useRouter();
  const recognitionRef = useRef<any>(null);

  const [voiceStep, setVoiceStep] = useState<VoiceStep>("idle");
  const [currentQ, setCurrentQ] = useState(0);
  const [turns, setTurns] = useState<{ question: string; answer: string }[]>([]);
  const [prefill, setPrefill] = useState<Record<string, any>>({});
  const [retryCount, setRetryCount] = useState(0);
  const [fallbackInput, setFallbackInput] = useState("");
  const [showFallback, setShowFallback] = useState(false);
  const [transcript, setTranscript] = useState(""); // live interim display
  const [extractedProfile, setExtractedProfile] = useState<Partial<HouseholdCreatePayload> | null>(null);
  const [confidence, setConfidence] = useState(0);

  // ── Check browser support on mount ──────────────────────────────────────
  useEffect(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      toast.error("आवाज़ पहचान Chrome में काम करती है। फ़ॉर्म पर जाएं।");
      setTimeout(() => router.replace("/setup/form"), 1800);
      return;
    }

    // Load prefill
    try {
      const raw = sessionStorage.getItem("voice_prefill");
      if (raw) setPrefill(JSON.parse(raw));
    } catch {}

    setVoiceStep("speaking");
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Build question text (with prefill confirm variant) ─────────────────
  const getQuestionText = useCallback(
    (qIdx: number): string => {
      const q = QUESTIONS[qIdx];
      if (!q) return "";
      if (q.confirmText) {
        let val = "";
        if (q.id === "name") val = prefill.name || "";
        if (q.id === "location") val = prefill.district ? `${prefill.district}, ${prefill.state || ""}` : "";
        if (q.id === "crop") val = prefill.crop_primary || "";
        if (q.id === "land") val = prefill.land_acres ? `${prefill.land_acres}` : "";
        if (val) return q.confirmText(val);
      }
      return q.text;
    },
    [prefill],
  );

  // ── State machine driver ────────────────────────────────────────────────
  useEffect(() => {
    if (voiceStep === "speaking") {
      const text = getQuestionText(currentQ);
      speak(text, () => setVoiceStep("listening"));
    }

    if (voiceStep === "listening") {
      startListening();
    }
  }, [voiceStep, currentQ]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── STT ─────────────────────────────────────────────────────────────────
  function startListening() {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SR();
    recognition.lang = "hi-IN";
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onresult = (e: any) => {
      let interim = "";
      let final = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        if (e.results[i].isFinal) final += e.results[i][0].transcript;
        else interim += e.results[i][0].transcript;
      }
      setTranscript(final || interim);
      if (final) handleAnswer(final.trim());
    };

    recognition.onerror = (e: any) => {
      setTranscript("");
      if (e.error !== "no-speech") {
        handleAnswer("");
      }
    };

    recognition.onend = () => {
      // If no result event fired, treat as empty answer
    };

    recognitionRef.current = recognition;
    recognition.start();
  }

  // ── Handle a recognised answer ──────────────────────────────────────────
  function handleAnswer(answer: string) {
    recognitionRef.current?.stop();
    setTranscript("");
    setVoiceStep("processing");

    // Empty / too short → retry or fallback
    if (answer.length < 2) {
      if (retryCount < 2) {
        setRetryCount(r => r + 1);
        speak("मुझे समझ नहीं आया, एक बार और बोलिए।", () => setVoiceStep("listening"));
        return;
      }
      // 2 retries exhausted → show text fallback for this Q
      setRetryCount(0);
      setShowFallback(true);
      return;
    }

    setRetryCount(0);
    const questionText = getQuestionText(currentQ);
    const newTurns = [...turns, { question: questionText, answer }];
    setTurns(newTurns);

    const next = currentQ + 1;
    if (next < QUESTIONS.length) {
      setCurrentQ(next);
      setVoiceStep("speaking");
    } else {
      // All questions answered — call extraction
      runExtraction(newTurns);
    }
  }

  // ── Fallback text input submit ──────────────────────────────────────────
  function handleFallbackSubmit() {
    if (!fallbackInput.trim()) return;
    setShowFallback(false);
    handleAnswer(fallbackInput.trim());
    setFallbackInput("");
  }

  // ── Call backend extraction ─────────────────────────────────────────────
  async function runExtraction(completedTurns: { question: string; answer: string }[]) {
    setVoiceStep("processing");
    try {
      const result = await extractOnboardingData(completedTurns, prefill);
      setExtractedProfile(result.household);
      setConfidence(result.confidence);
      speak("आपकी जानकारी तैयार है। कृपया नीचे देखें और पुष्टि करें।", () => {});
      setVoiceStep("confirming");
    } catch (e: any) {
      toast.error("जानकारी निकालने में समस्या। दोबारा कोशिश करें।");
      // Reset to start
      setCurrentQ(0);
      setTurns([]);
      setVoiceStep("speaking");
    }
  }

  // ── Create household and navigate to dashboard ──────────────────────────
  async function handleConfirm() {
    if (!extractedProfile) return;
    setVoiceStep("submitting");
    try {
      const payload: HouseholdCreatePayload = {
        name: extractedProfile.name || "Farmer",
        state: extractedProfile.state || "Madhya Pradesh",
        district: extractedProfile.district || "Harda",
        village: extractedProfile.village,
        crop_primary: extractedProfile.crop_primary,
        crop_secondary: extractedProfile.crop_secondary,
        land_acres: extractedProfile.land_acres,
        family_members: (extractedProfile.family_members || []) as FamilyMember[],
      };
      const res = await createHousehold(payload);
      localStorage.setItem("household_id", res.household_id);
      localStorage.setItem("household_name", payload.name);
      sessionStorage.removeItem("voice_prefill");
      router.push("/dashboard");
    } catch (e: any) {
      toast.error(e.message || "Profile बनाने में समस्या।");
      setVoiceStep("confirming");
    }
  }

  function handleRestart() {
    setCurrentQ(0);
    setTurns([]);
    setExtractedProfile(null);
    setRetryCount(0);
    setShowFallback(false);
    setTranscript("");
    setVoiceStep("speaking");
  }

  // ─── Render ─────────────────────────────────────────────────────────────

  const progress = Math.round(((currentQ) / QUESTIONS.length) * 100);
  const extractedFamilyMembers = extractedProfile?.family_members ?? [];

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-asha-teal text-white px-4 pt-12 pb-5">
        <div className="flex items-center gap-3 mb-3">
          <button onClick={() => router.replace("/setup")} className="text-white text-xl">←</button>
          <div>
            <h1 className="font-bold text-lg">आवाज़ से प्रोफ़ाइल बनाएं</h1>
            <p className="text-white/70 text-xs">Voice Onboarding — Hindi</p>
          </div>
        </div>
        {voiceStep !== "confirming" && voiceStep !== "submitting" && (
          <div className="w-full bg-white/20 rounded-full h-1.5">
            <div
              className="bg-asha-light h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
      </div>

      <div className="flex-1 flex flex-col items-center justify-center p-5 space-y-6">

        {/* ── SPEAKING / LISTENING / PROCESSING states ── */}
        {(voiceStep === "idle" || voiceStep === "speaking" || voiceStep === "listening" || voiceStep === "processing") && !showFallback && (
          <>
            {/* Asha avatar */}
            <div className={`w-28 h-28 rounded-full bg-asha-teal flex items-center justify-center text-5xl shadow-lg transition-all
              ${voiceStep === "listening" ? "ring-4 ring-asha-light ring-offset-4 animate-pulse" : ""}
              ${voiceStep === "speaking" ? "ring-4 ring-white/40 ring-offset-4" : ""}
            `}>
              🌿
            </div>

            {/* Status label */}
            <div className="text-center space-y-1">
              {voiceStep === "speaking" && (
                <p className="text-asha-teal font-semibold text-base animate-pulse">आशा बोल रही है...</p>
              )}
              {voiceStep === "listening" && (
                <p className="text-green-600 font-semibold text-base">सुन रहे हैं... बोलिए</p>
              )}
              {voiceStep === "processing" && (
                <p className="text-gray-500 font-semibold text-base">समझ रहे हैं...</p>
              )}
              {voiceStep === "idle" && (
                <p className="text-gray-400 text-sm">शुरू हो रहा है...</p>
              )}
            </div>

            {/* Current question */}
            {currentQ < QUESTIONS.length && (
              <div className="bg-white rounded-2xl px-5 py-4 shadow-sm border border-gray-100 max-w-sm w-full text-center">
                <p className="text-xs text-gray-400 mb-1">सवाल {currentQ + 1} / {QUESTIONS.length}</p>
                <p className="text-gray-800 text-base leading-relaxed">{getQuestionText(currentQ)}</p>
              </div>
            )}

            {/* Live transcript */}
            {transcript && (
              <div className="bg-green-50 border border-green-200 rounded-xl px-4 py-3 max-w-sm w-full text-center">
                <p className="text-green-800 text-sm">{transcript}</p>
              </div>
            )}

            {/* Retry indicator */}
            {retryCount > 0 && (
              <p className="text-orange-500 text-xs text-center">
                कोशिश {retryCount}/2 — ज़ोर से और साफ़ बोलें
              </p>
            )}

            {/* Previous answers */}
            {turns.length > 0 && (
              <div className="w-full max-w-sm space-y-2">
                <p className="text-xs text-gray-400 text-center">पिछले जवाब</p>
                {turns.slice(-3).map((t, i) => (
                  <div key={i} className="bg-white rounded-xl px-4 py-2.5 border border-gray-100 shadow-sm">
                    <p className="text-xs text-gray-400">{t.question.slice(0, 40)}...</p>
                    <p className="text-sm text-gray-800 font-medium">{t.answer}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Skip to form */}
            <button
              onClick={() => router.replace("/setup/form")}
              className="text-gray-400 text-xs underline underline-offset-2 mt-2"
            >
              फ़ॉर्म से भरें
            </button>
          </>
        )}

        {/* ── FALLBACK TEXT INPUT ── */}
        {showFallback && (
          <div className="w-full max-w-sm space-y-4 text-center">
            <p className="text-gray-600 font-semibold">
              {getQuestionText(currentQ)}
            </p>
            <p className="text-sm text-gray-400">आवाज़ नहीं समझ पाए — यहाँ टाइप करें:</p>
            <input
              autoFocus
              value={fallbackInput}
              onChange={e => setFallbackInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleFallbackSubmit()}
              placeholder="यहाँ लिखें..."
              className="w-full border border-gray-300 rounded-xl px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-asha-green"
            />
            <button
              onClick={handleFallbackSubmit}
              disabled={!fallbackInput.trim()}
              className="w-full bg-asha-green text-white py-3 rounded-xl font-semibold disabled:opacity-50"
            >
              ठीक है →
            </button>
          </div>
        )}

        {/* ── CONFIRMING state ── */}
        {voiceStep === "confirming" && extractedProfile && (
          <div className="w-full max-w-sm space-y-4">
            <div className="text-center space-y-1">
              <p className="text-2xl">✅</p>
              <h2 className="text-xl font-bold text-gray-800">प्रोफ़ाइल तैयार है</h2>
              <p className="text-sm text-gray-500">
                विश्वास: {Math.round(confidence * 100)}%
              </p>
            </div>

            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm divide-y divide-gray-100">
              <ProfileRow label="नाम" value={extractedProfile.name} />
              <ProfileRow label="राज्य" value={extractedProfile.state} />
              <ProfileRow label="जिला" value={extractedProfile.district} />
              <ProfileRow label="मुख्य फसल" value={extractedProfile.crop_primary} />
              <ProfileRow label="ज़मीन (एकड़)" value={extractedProfile.land_acres?.toString()} />
              {extractedFamilyMembers.length > 0 && (
                <div className="px-4 py-3">
                  <p className="text-xs text-gray-400 mb-1">परिवार</p>
                  <div className="space-y-1">
                    {extractedFamilyMembers.map((m, i: number) => (
                      <p key={i} className="text-sm text-gray-800">
                        {m.name} ({m.age} वर्ष, {m.relation})
                        {m.is_pregnant && <span className="text-pink-600 ml-1 font-medium">— गर्भवती</span>}
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={handleConfirm}
              className="w-full bg-asha-green text-white py-4 rounded-2xl text-base font-bold shadow-md"
            >
              सही है — शुरू करें
            </button>
            <button
              onClick={handleRestart}
              className="w-full border border-gray-300 text-gray-600 py-3 rounded-2xl text-sm"
            >
              फिर से बोलें
            </button>
          </div>
        )}

        {/* ── SUBMITTING state ── */}
        {voiceStep === "submitting" && (
          <div className="text-center space-y-4">
            <div className="w-16 h-16 border-4 border-asha-teal border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-gray-600 font-semibold">प्रोफ़ाइल बना रहे हैं...</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Small helper component ───────────────────────────────────────────────────

function ProfileRow({ label, value }: { label: string; value?: string }) {
  if (!value) return null;
  return (
    <div className="px-4 py-3 flex items-center justify-between">
      <p className="text-xs text-gray-400">{label}</p>
      <p className="text-sm font-semibold text-gray-800">{value}</p>
    </div>
  );
}
