import { SourceChunk } from "@/lib/types";

interface SourceCardProps {
  source: SourceChunk;
}

export function SourceCard({ source }: SourceCardProps) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="mb-2 flex items-center justify-between gap-2">
        <h4 className="text-sm font-semibold text-slate-800">{source.document_name}</h4>
        <span className="rounded-full bg-soft px-2 py-1 font-mono text-xs text-slate-700">
          score {source.score.toFixed(4)}
        </span>
      </div>
      <p className="mb-1 font-mono text-xs text-slate-500">{source.chunk_id}</p>
      <p className="line-clamp-5 text-sm leading-6 text-slate-700">{source.text}</p>
    </article>
  );
}
