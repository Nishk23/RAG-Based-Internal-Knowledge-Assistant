import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Internal Knowledge Assistant",
  description: "Vectorless RAG with LangChain, LangGraph, and RAGAS"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
