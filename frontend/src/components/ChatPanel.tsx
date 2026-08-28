"use client";

import { useState } from "react";

import { askQuestion } from "@/lib/api";
import { ChatResponse, EvaluationResult, SourceChunk } from "@/lib/types";
import { SourceCard } from "@/components/SourceCard";
import { useEnterpriseAuth } from "@/components/Providers";

interface ChatPanelProps {
  onEvaluationChange: (evaluation: EvaluationResult | null) => void;
}

export function ChatPanel({ onEvaluationChange }: ChatPanelProps) {
  const auth = useEnterpriseAuth();
  const [question, setQuestion] = useState("");
  const [topK, setTopK] = useState(5);
  const [evaluate, setEvaluate] = useState(false);
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<string>("");
  const [sources, setSources] = useState<SourceChunk[]>([]);
  const [error, setError] = useState<string>("");

  const runChat = async () => {
    if (question.trim().length < 3) {
      setError("Please enter a longer question.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response: ChatResponse = await askQuestion(
        { question, top_k: topK, evaluate },
        auth.accessToken
      );

      setAnswer(response.answer);
      setSources(response.sources);
      onEvaluationChange(response.evaluation);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Chat request failed.";
      setError(message);
      onEvaluationChange(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel">
      <h3 className="mb-3 text-lg font-semibold text-ink">Chat Assistant</h3>

      <div className="space-y-3">
        <textarea
          className="min-h-28 w-full rounded-xl border border-slate-300 p-3 text-sm"
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a question about your internal policies, SLAs, or governance docs..."
          value={question}
        />

        <div className="grid gap-3 sm:grid-cols-3">
          <label className="flex flex-col gap-2 text-xs uppercase tracking-wide text-slate-500">
            Top K
            <input
              className="rounded-lg border border-slate-300 p-2 text-sm text-slate-700"
              max={20}
              min={1}
              onChange={(event) => setTopK(Number(event.target.value))}
              type="number"
              value={topK}
            />
          </label>

          <label className="flex items-center gap-2 pt-6 text-sm text-slate-700">
            <input checked={evaluate} onChange={(event) => setEvaluate(event.target.checked)} type="checkbox" />
            Run quality evaluation
          </label>

          <button
            className="mt-5 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition hover:bg-sky-600 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={loading}
            onClick={runChat}
            type="button"
          >
            {loading ? "Thinking..." : "Submit"}
          </button>
        </div>

        {error && <p className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
      </div>

      <div className="mt-6 space-y-4">
        <div>
          <h4 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">Answer</h4>
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
            {answer || "No answer yet."}
          </div>
        </div>

        <div>
          <h4 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">Sources</h4>
          <div className="grid gap-3">
            {sources.length === 0 && <p className="text-sm text-slate-500">No sources yet.</p>}
            {sources.map((source) => (
              <SourceCard key={source.chunk_id} source={source} />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
