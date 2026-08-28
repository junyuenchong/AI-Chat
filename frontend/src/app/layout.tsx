import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AppProviders } from "./providers";

import "./globals.css";

export const metadata: Metadata = {
  title: "AI Chat",
  description: "Next.js UI for the FastAPI LangChain / RAG chat backend.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
