import type { Metadata } from "next";

import { Providers } from "@/components/Providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "Enterprise Internal Knowledge Assistant",
  description: "Access-controlled and source-grounded internal knowledge retrieval"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body><Providers>{children}</Providers></body>
    </html>
  );
}
