export function Header() {
  return (
    <header className="panel mb-6 flex flex-col gap-2">
      <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">AI Workspace</p>
      <h1 className="text-3xl font-semibold text-ink">Internal Knowledge Assistant</h1>
      <p className="text-sm text-slate-600">
        Vectorless RAG with LangChain, LangGraph, and RAGAS Evaluation
      </p>
    </header>
  );
}
