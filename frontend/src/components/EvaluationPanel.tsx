"use client";

import { EvaluationResult } from "@/lib/types";

interface EvaluationPanelProps {
  evaluation: EvaluationResult | null;
}

const metricLabels: Record<string, string> = {
  faithfulness: "Faithfulness",
  answer_relevancy: "Answer Relevance",
  context_precision: "Context Precision",
  context_recall: "Context Recall",
  context_relevancy: "Context Relevancy"
};

export function EvaluationPanel({ evaluation }: EvaluationPanelProps) {
  return (
    <section className="panel">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-ink">RAGAS Evaluation</h3>
        <span className="text-xs text-slate-500">Optional quality scoring</span>
      </div>

      {!evaluation ? (
        <p className="rounded-xl border border-dashed border-slate-300 p-4 text-sm text-slate-600">
          Evaluation is optional. Turn on the evaluate toggle when asking a question to generate
          RAGAS metrics.
        </p>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {Object.entries(metricLabels).map(([key, label]) => {
              const value = evaluation.metrics[key];
              return (
                <div className="metric-card" key={key}>
                  <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
                  <p className="mt-2 text-2xl font-semibold text-slate-800">
                    {typeof value === "number" ? value.toFixed(3) : "N/A"}
                  </p>
                </div>
              );
            })}
          </div>
          {evaluation.skipped_metrics.length > 0 && (
            <p className="text-xs text-amber-700">
              Skipped metrics: {evaluation.skipped_metrics.join(", ")} (not available in current RAGAS
              version)
            </p>
          )}
          <p className="text-xs text-slate-500">{evaluation.message}</p>
        </div>
      )}
    </section>
  );
}
