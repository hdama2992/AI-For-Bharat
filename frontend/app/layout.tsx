import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "react-hot-toast";

export const metadata: Metadata = {
  title: "VikasGPT — Rural Health & Wealth Companion",
  description: "India's first voice-first conversational OS for rural health and agricultural livelihood",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "VikasGPT",
  },
};

export const viewport = {
  themeColor: "#128C7E",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased max-w-md mx-auto min-h-screen bg-gray-100">
        {children}
        <Toaster position="top-center" toastOptions={{ duration: 3000 }} />
      </body>
    </html>
  );
}
