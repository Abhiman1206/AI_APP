import type { Metadata } from "next";
import "./globals.css";

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
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
