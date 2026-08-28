"use client";

import { useEnterpriseAuth } from "@/components/Providers";

export function Header() {
  const auth = useEnterpriseAuth();
  return (
    <header className="panel mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
      <div className="flex flex-col gap-2">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">Secure AI Workspace</p>
        <h1 className="text-3xl font-semibold text-ink">Internal Knowledge Assistant</h1>
        <p className="text-sm text-slate-600">
          Tenant-isolated retrieval with validated source citations
        </p>
      </div>
      <div className="flex flex-col items-start gap-2 sm:items-end">
        <span className="text-xs text-slate-500">
          {auth.configured
            ? auth.authenticated ? `Signed in${auth.subject ? ` as ${auth.subject}` : ""}` : "Authentication required"
            : "Local development authentication"}
        </span>
        {auth.configured && (
          <button
            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700"
            onClick={() => void (auth.authenticated ? auth.signOut() : auth.signIn())}
            type="button"
          >
            {auth.authenticated ? "Sign out" : "Sign in with SSO"}
          </button>
        )}
      </div>
    </header>
  );
}
