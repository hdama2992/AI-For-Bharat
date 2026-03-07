"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function LandingPage() {
  const router = useRouter();
  const whatsappNumber = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || "+14155238886";
  const whatsappDigits = whatsappNumber.replace(/\D/g, "");
  const whatsappUrl = whatsappDigits ? `https://wa.me/${whatsappDigits}` : null;

  useEffect(() => {
    const id = localStorage.getItem("household_id");
    if (id) router.replace("/dashboard");
  }, [router]);

  return (
    <div className="min-h-screen flex flex-col bg-asha-teal">
      {/* Hero */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 pt-16 pb-8 text-white text-center">
        <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center mb-6 shadow-lg">
          <span className="text-5xl">🌿</span>
        </div>
        <h1 className="text-4xl font-bold mb-2">VikasGPT</h1>
        <p className="text-asha-light text-lg font-medium mb-4">विकास-GPT</p>
        <p className="text-white/80 text-base max-w-xs leading-relaxed">
          Your trusted AI companion for rural health & agricultural livelihood
        </p>
        <p className="text-white/60 text-sm mt-2">
          ग्रामीण स्वास्थ्य और कृषि आय का विश्वसनीय साथी
        </p>
      </div>

      {/* Feature pills */}
      <div className="px-6 pb-6">
        <div className="flex gap-2 justify-center flex-wrap mb-8">
          {[
            { icon: "🌾", label: "Mandi Prices" },
            { icon: "❤️", label: "Health Triage" },
            { icon: "💬", label: "WhatsApp Health" },
          ].map((f) => (
            <span
              key={f.label}
              className="bg-white/20 text-white text-sm px-3 py-1.5 rounded-full font-medium"
            >
              {f.icon} {f.label}
            </span>
          ))}
        </div>

        <Link
          href="/setup"
          className="block w-full bg-asha-light text-white text-center py-4 rounded-2xl text-lg font-bold shadow-lg active:scale-95 transition-transform"
        >
          Get Started — शुरू करें
        </Link>

        <p className="text-white/50 text-xs text-center mt-4">
          No app download needed • Zero cost • Works on 2G
        </p>

        {whatsappUrl && (
          <a
            href={whatsappUrl}
            target="_blank"
            rel="noreferrer"
            className="mt-4 block w-full border border-white/30 text-white text-center py-3 rounded-2xl text-sm font-semibold"
          >
            Open WhatsApp Health Demo
          </a>
        )}
      </div>

      {/* Demo shortcut */}
      <div className="pb-8 px-6 text-center">
        <button
          onClick={() => {
            localStorage.setItem("household_id", "demo-rajesh-001");
            router.push("/dashboard");
          }}
          className="text-white/60 text-sm underline underline-offset-2"
        >
          Try Demo (Rajesh Kumar, Harda MP)
        </button>
      </div>
    </div>
  );
}
