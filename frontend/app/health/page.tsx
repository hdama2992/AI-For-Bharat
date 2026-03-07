"use client";
import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { TriageResult } from "@/lib/api";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface Message {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}

const TRIAGE_CONFIG = {
  GREEN: {
    bg: "bg-green-50",
    border: "border-green-400",
    headerBg: "bg-green-500",
    icon: "🟢",
    title: "Manage at Home",
    titleHi: "घर पर देखभाल करें",
  },
  YELLOW: {
    bg: "bg-yellow-50",
    border: "border-yellow-400",
    headerBg: "bg-yellow-500",
    icon: "🟡",
    title: "Visit PHC Today",
    titleHi: "आज PHC जाएं",
  },
  RED: {
    bg: "bg-red-50",
    border: "border-red-500",
    headerBg: "bg-red-600",
    icon: "🔴",
    title: "CALL 108 NOW",
    titleHi: "अभी 108 कॉल करें",
  },
};

const QUICK_REPLIES = [
  "Fever / बुखार",
  "Stomach pain / पेट दर्द",
  "Cough / खांसी",
  "Chest pain / सीने में दर्द",
  "Headache / सिरदर्द",
  "Weakness / कमज़ोरी",
];

export default function HealthPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Namaste 🙏 I'm Vikas, your health advisor. Please tell me — what symptoms are you or a family member experiencing?\n\nनमस्ते 🙏 मैं विकास हूं, आपका स्वास्थ्य सहायक। बताइए — आप या आपके परिवार में क्या तकलीफ है?",
    },
  ]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [triage, setTriage] = useState<TriageResult | null>(null);
  const [sessionId] = useState(() => Math.random().toString(36).slice(2));
  const [lang, setLang] = useState<"en" | "hi">("en");
  const [householdId, setHouseholdId] = useState("demo-rajesh-001");
  const [isListening, setIsListening] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);
  const whatsappNumber = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || "+14155238886";
  const whatsappDigits = whatsappNumber.replace(/\D/g, "");
  const whatsappUrl = whatsappDigits ? `https://wa.me/${whatsappDigits}?text=${encodeURIComponent("Namaste Vikas")}` : null;

  useEffect(() => {
    const id = localStorage.getItem("household_id");
    if (id) setHouseholdId(id);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || isStreaming) return;
    const userMsg: Message = { role: "user", content: text };
    const history = messages.map(m => ({ role: m.role, content: m.content }));

    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setIsStreaming(true);

    // Add streaming assistant message placeholder
    setMessages(prev => [...prev, { role: "assistant", content: "", isStreaming: true }]);

    try {
      const res = await fetch(`${BASE}/health/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          household_id: householdId,
          message: text,
          conversation_history: history,
          session_id: sessionId,
          language: lang,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let fullText = "";
      let lastEventType = "message";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            lastEventType = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") {
              break;
            } else if (lastEventType === "triage") {
              try {
                const parsed = JSON.parse(data);
                if (parsed.triage) setTriage(parsed.triage);
              } catch {}
              lastEventType = "message";
            } else {
              fullText += data;
              setMessages(prev => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last.isStreaming) {
                  updated[updated.length - 1] = { ...last, content: fullText };
                }
                return updated;
              });
            }
          }
        }
      }

      // Finalize streaming message
      setMessages(prev => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last.isStreaming) {
          // Strip <TRIAGE>...</TRIAGE> from displayed text
          const cleaned = fullText.replace(/<TRIAGE>[\s\S]*?<\/TRIAGE>/g, "").trim();
          updated[updated.length - 1] = { role: "assistant", content: cleaned, isStreaming: false };
        }
        return updated;
      });
    } catch (e: any) {
      setMessages(prev => prev.filter(m => !m.isStreaming));
      toast.error("Connection error. Please try again.");
    } finally {
      setIsStreaming(false);
    }
  };

  const startVoice = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) { toast.error("Voice not supported on this browser. Use Chrome."); return; }

    const recognition = new SpeechRecognition();
    recognition.lang = lang === "hi" ? "hi-IN" : "en-IN";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => { setIsListening(false); toast.error("Voice recognition failed"); };
    recognition.onresult = (e: any) => {
      const transcript = e.results[0][0].transcript;
      setInput(transcript);
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  const resetChat = () => {
    setMessages([{
      role: "assistant",
      content: "Namaste 🙏 I'm Vikas, your health advisor. Please tell me — what symptoms are you or a family member experiencing?\n\nनमस्ते 🙏 मैं विकास हूं, आपका स्वास्थ्य सहायक। बताइए — आप या आपके परिवार में क्या तकलीफ है?",
    }]);
    setTriage(null);
    setInput("");
  };

  const tc = triage ? TRIAGE_CONFIG[triage.triage_level] : null;

  return (
    <div className="min-h-screen flex flex-col bg-gray-100">
      {/* Header */}
      <div className="bg-asha-teal text-white px-4 pt-12 pb-4 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => router.back()} className="text-white text-xl">←</button>
            <div>
              <h1 className="font-bold text-lg">❤️ Health Triage</h1>
              <p className="text-white/70 text-xs">Powered by Bedrock + ICMR guidelines</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setLang(l => l === "en" ? "hi" : "en")}
              className="bg-white/20 text-white text-xs px-2 py-1 rounded-full"
            >
              {lang === "en" ? "हिंदी" : "EN"}
            </button>
            <button onClick={resetChat} className="bg-white/20 text-white text-xs px-2 py-1 rounded-full">
              Reset
            </button>
          </div>
        </div>
      </div>

      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto chat-bg px-3 py-3 space-y-2 scrollbar-hide">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            {msg.role === "assistant" && (
              <div className="w-7 h-7 bg-asha-teal rounded-full flex items-center justify-center text-sm mr-1.5 flex-shrink-0 mt-1">
                🌿
              </div>
            )}
            <div
              className={`max-w-[80%] px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed shadow-sm
                ${msg.role === "user"
                  ? "bg-asha-bubble text-gray-800 rounded-tr-sm"
                  : "bg-white text-gray-800 rounded-tl-sm"
                }`}
            >
              {msg.content || (msg.isStreaming && (
                <span className="flex gap-1 items-center h-4">
                  <span className="w-1.5 h-1.5 bg-gray-400 rounded-full typing-dot" />
                  <span className="w-1.5 h-1.5 bg-gray-400 rounded-full typing-dot" />
                  <span className="w-1.5 h-1.5 bg-gray-400 rounded-full typing-dot" />
                </span>
              ))}
              {msg.isStreaming && msg.content && (
                <span className="inline-block w-0.5 h-4 bg-gray-400 ml-0.5 animate-pulse align-middle" />
              )}
            </div>
          </div>
        ))}

        {/* Triage result card */}
        {triage && tc && (
          <div className={`mx-2 mt-3 rounded-2xl border-2 overflow-hidden ${tc.border}`}>
            <div className={`${tc.headerBg} px-4 py-3 text-white`}>
              <div className="flex items-center gap-2">
                <span className="text-2xl">{tc.icon}</span>
                <div>
                  <p className="font-bold text-lg">{tc.title}</p>
                  <p className="text-white/80 text-sm">{tc.titleHi}</p>
                </div>
                <span className="ml-auto text-white/70 text-sm">{triage.confidence_pct}% confidence</span>
              </div>
            </div>
            <div className={`${tc.bg} p-4 space-y-3`}>
              <p className="text-gray-700 text-sm leading-relaxed">{triage.assessment_summary}</p>

              {triage.immediate_actions?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Immediate Actions</p>
                  <ul className="space-y-1">
                    {triage.immediate_actions.map((a, i) => (
                      <li key={i} className="flex gap-2 text-sm text-gray-700">
                        <span className="text-asha-green flex-shrink-0">•</span> {a}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {triage.follow_up && (
                <p className="text-sm text-gray-600 bg-white/60 rounded-lg p-2">
                  📋 {triage.follow_up}
                </p>
              )}

              {triage.triage_level === "RED" && triage.emergency_number && (
                <a
                  href={`tel:${triage.emergency_number}`}
                  className="flex items-center justify-center gap-2 bg-red-600 text-white py-3 rounded-xl font-bold text-base w-full"
                >
                  📞 Call {triage.emergency_number} — EMERGENCY
                </a>
              )}

              <p className="text-xs text-gray-400 italic">{triage.disclaimer}</p>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Quick replies — show only before triage */}
      {!triage && messages.length <= 2 && (
        <div className="px-3 py-2 flex gap-2 overflow-x-auto scrollbar-hide flex-shrink-0 bg-asha-chat">
          {QUICK_REPLIES.map(q => (
            <button
              key={q}
              onClick={() => sendMessage(q)}
              disabled={isStreaming}
              className="flex-shrink-0 bg-white text-gray-700 text-xs px-3 py-1.5 rounded-full border border-gray-200 shadow-sm"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Input bar */}
      <div className="bg-asha-chat px-3 py-2.5 flex-shrink-0 border-t border-gray-200">
        {whatsappUrl && (
          <a
            href={whatsappUrl}
            target="_blank"
            rel="noreferrer"
            className="mb-2 flex items-center justify-center rounded-xl border border-green-200 bg-green-50 px-3 py-2 text-xs font-medium text-green-700"
          >
            Need to continue on WhatsApp? Open VikasGPT WhatsApp
          </a>
        )}
        <div className="flex items-end gap-2">
          {/* Voice button */}
          <button
            onMouseDown={startVoice}
            onTouchStart={startVoice}
            disabled={isStreaming}
            className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 transition-all
              ${isListening ? "bg-red-500 scale-110" : "bg-gray-200 text-gray-600"}
              disabled:opacity-40`}
          >
            {isListening ? <span className="text-white text-lg">⏹</span> : <span className="text-lg">🎤</span>}
          </button>

          {/* Text input */}
          <div className="flex-1 bg-white rounded-2xl px-4 py-2.5 border border-gray-200 flex items-center">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && !e.shiftKey && sendMessage(input)}
              placeholder={lang === "hi" ? "लक्षण बताएं..." : "Describe your symptoms..."}
              className="flex-1 text-sm focus:outline-none bg-transparent"
              disabled={isStreaming}
            />
          </div>

          {/* Send button */}
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || isStreaming}
            className="w-10 h-10 bg-asha-green rounded-full flex items-center justify-center flex-shrink-0 disabled:opacity-40 active:scale-95 transition-transform"
          >
            <span className="text-white text-lg">➤</span>
          </button>
        </div>
      </div>
    </div>
  );
}
