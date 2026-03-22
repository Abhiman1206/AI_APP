import type { Metadata } from "next";
import { Sora, Source_Sans_3 } from "next/font/google";
import "./globals.css";

const sora = Sora({ subsets: ["latin"], weight: ["500", "600", "700", "800"], variable: "--font-display" });
const sourceSans3 = Source_Sans_3({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "Intelli-Credit | AI-Powered Credit Appraisal",
  description:
    "Automated credit analysis and CAM generation powered by AI. Upload financials, get instant 5Cs scoring and risk assessment.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${sora.variable} ${sourceSans3.variable}`}>{children}</body>
    </html>
  );
}
