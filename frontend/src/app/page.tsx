"use client";

import { useState } from "react";

import { ChatPanel } from "@/components/ChatPanel";
import { DocumentUpload } from "@/components/DocumentUpload";
import { EvaluationPanel } from "@/components/EvaluationPanel";
import { Header } from "@/components/Header";
import { useEnterpriseAuth } from "@/components/Providers";
import { EvaluationResult } from "@/lib/types";

export default function HomePage() {
  const auth = useEnterpriseAuth();
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <Header />
      {auth.loading && <section className="panel">Completing secure sign-in…</section>}
      {!auth.loading && auth.configured && !auth.authenticated && (
        <section className="panel">
          <h2 className="text-lg font-semibold text-ink">Sign in required</h2>
          <p className="mt-2 text-sm text-slate-600">
            Use your organization&apos;s identity provider to access authorized knowledge.
          </p>
        </section>
      )}
      {!auth.loading && auth.authenticated && (
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <section className="space-y-6 lg:col-span-4">
          <DocumentUpload />
          <EvaluationPanel evaluation={evaluation} />
        </section>
        <section className="lg:col-span-8">
          <ChatPanel onEvaluationChange={setEvaluation} />
        </section>
      </div>
      )}
    </main>
  );
}
