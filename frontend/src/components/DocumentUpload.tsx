"use client";

import { useState } from "react";
import useSWR from "swr";

import { listDocuments, loadSampleDocuments, uploadDocument } from "@/lib/api";
import { DocumentSummary } from "@/lib/types";
import { useEnterpriseAuth } from "@/components/Providers";

interface DocumentUploadProps {
  onUploaded?: () => void;
}

export function DocumentUpload({ onUploaded }: DocumentUploadProps) {
  const auth = useEnterpriseAuth();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>("Ready to upload documents.");
  const [loading, setLoading] = useState(false);
  const {
    data: documents = [],
    error: documentError,
    mutate: refreshDocuments
  } = useSWR<DocumentSummary[]>(
    ["documents", auth.accessToken ?? "development"],
    () => listDocuments(auth.accessToken),
    { shouldRetryOnError: true, errorRetryCount: 3 }
  );

  const handleUpload = async () => {
    if (!selectedFile) {
      setStatus("Select a .txt, .md, or .pdf file first.");
      return;
    }

    setLoading(true);
    setStatus("Uploading and indexing document...");

    try {
      const result = await uploadDocument(selectedFile, auth.accessToken);
      setStatus(`${result.document_name} uploaded with ${result.chunk_count} chunks.`);
      setSelectedFile(null);
      await refreshDocuments();
      onUploaded?.();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Upload failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleLoadSample = async () => {
    setLoading(true);
    setStatus("Loading bundled sample documents...");
    try {
      const result = await loadSampleDocuments(auth.accessToken);
      setStatus(
        `Loaded ${result.documents_loaded} sample docs with ${result.chunks_indexed} total chunks.`
      );
      await refreshDocuments();
      onUploaded?.();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to load sample docs.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel">
      <h3 className="mb-3 text-lg font-semibold text-ink">Document Upload</h3>

      <div className="space-y-3">
        <input
          className="w-full rounded-lg border border-slate-300 p-2 text-sm"
          type="file"
          accept=".txt,.md,.pdf"
          onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
        />
        <div className="flex flex-wrap gap-2">
          <button
            className="rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white transition hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={loading}
            onClick={handleUpload}
            type="button"
          >
            {loading ? "Working..." : "Upload Document"}
          </button>
          <button
            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={loading}
            onClick={handleLoadSample}
            type="button"
          >
            Load Sample Docs
          </button>
        </div>
        <p className="text-xs text-slate-600">
          {documentError instanceof Error ? documentError.message : status}
        </p>
      </div>

      <div className="mt-5">
        <h4 className="mb-2 text-sm font-semibold text-slate-700">Indexed Documents</h4>
        <ul className="space-y-2">
          {documents.length === 0 && <li className="text-sm text-slate-500">No documents yet.</li>}
          {documents.map((doc) => (
            <li className="rounded-lg border border-slate-200 bg-slate-50 p-3" key={doc.document_id}>
              <p className="text-sm font-medium text-slate-800">{doc.document_name}</p>
              <p className="text-xs text-slate-600">Chunks: {doc.chunk_count}</p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
