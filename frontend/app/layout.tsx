import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AppProvider } from "@/lib/store";
import { Toaster } from "react-hot-toast";

const inter = Inter({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ResumeAI — Intelligent Career Platform",
  description:
    "AI-powered resume analysis, skill gap detection, ATS scoring and career guidance for students and employers.",
  keywords: ["resume analyzer", "AI", "ATS score", "skill gap", "career"],
  openGraph: {
    title: "ResumeAI — Intelligent Career Platform",
    description: "Upload your resume and get instant AI-powered insights.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className={inter.variable}>
      <body>
        <AppProvider>
          <Toaster
            position="top-right"
            toastOptions={{
              style: {
                background: "#16162a",
                color: "#e2e8f0",
                border: "1px solid rgba(99,102,241,0.2)",
                borderRadius: "12px",
              },
            }}
          />
          {children}
        </AppProvider>
      </body>
    </html>
  );
}
