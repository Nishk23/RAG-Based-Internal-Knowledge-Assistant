import {
  ChatRequest,
  ChatResponse,
  DocumentSummary,
  EvaluationResult,
  SampleLoadResponse,
  UploadResponse
} from "@/lib/types";

export const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === "true";

const createdAt = "2026-08-28T00:00:00Z";

export const demoDocuments: DocumentSummary[] = [
  {
    document_id: "demo-sla-operations",
    document_name: "sla_operations.md",
    chunk_count: 1,
    created_at: createdAt,
    allowed_roles: ["reader", "editor", "admin"],
    metadata: { sample: true }
  },
  {
    document_id: "demo-ai-governance",
    document_name: "ai_governance.md",
    chunk_count: 1,
    created_at: createdAt,
    allowed_roles: ["reader", "editor", "admin"],
    metadata: { sample: true }
  },
  {
    document_id: "demo-company-policy",
    document_name: "company_policy.md",
    chunk_count: 1,
    created_at: createdAt,
    allowed_roles: ["reader", "editor", "admin"],
    metadata: { sample: true }
  }
];

const evaluation: EvaluationResult = {
  status: "completed",
  metrics: {
    faithfulness: 1,
    answer_relevancy: 0.95,
    context_precision: 1,
    context_recall: 1,
    context_relevancy: 0.96,
    citation_validity: 1
  },
  skipped_metrics: [],
  message: "Deterministic indicators calculated from the cited sample context."
};

const sampleAnswers = [
  {
    terms: ["incident", "severity", "sla", "postmortem", "mitigation"],
    answer:
      "Severity 1 incidents require response initiation within 5 minutes. During active mitigation, status updates are required every 30 minutes, and breach risk must be escalated to the incident commander within 15 minutes [1].",
    document_name: "sla_operations.md",
    chunk_id: "demo-sla-operations-1",
    text:
      "Severity 1 incidents require response initiation within 5 minutes. Status updates must be posted every 30 minutes during active mitigation. Breach risk must be escalated to the incident commander within 15 minutes. Postmortems are due within 5 business days after incident closure."
  },
  {
    terms: ["ai", "model", "hallucination", "prompt", "legal"],
    answer:
      "High-risk AI use cases require model-card documentation and legal review. Production prompts and output examples must be versioned, and hallucination-risk reviews should be completed before a customer-facing release [1].",
    document_name: "ai_governance.md",
    chunk_id: "demo-ai-governance-1",
    text:
      "High-risk AI use cases require model card documentation and legal review. Production prompts and output examples must be versioned. Hallucination risk reviews should be completed before customer-facing release."
  },
  {
    terms: ["employee", "training", "policy", "compliance", "quarterly"],
    answer:
      "Employees must complete security training within 14 days of joining. Policy exceptions require documentation and approval from the compliance lead, while internal process controls require quarterly review [1].",
    document_name: "company_policy.md",
    chunk_id: "demo-company-policy-1",
    text:
      "All employees must complete security training within 14 days of joining. Any policy exception must be documented and approved by the compliance lead. Quarterly reviews are required for all internal process controls."
  }
];

export function demoUpload(file: File): UploadResponse {
  return {
    document_id: `demo-upload-${file.name.replace(/[^a-z0-9]/gi, "-").toLowerCase()}`,
    document_name: file.name,
    chunk_count: 1,
    checksum: "sample-demo-no-persistence",
    message: "Upload simulated locally; the public demo does not transmit or retain files."
  };
}

export function demoSampleLoad(): SampleLoadResponse {
  return {
    documents_loaded: demoDocuments.length,
    chunks_indexed: demoDocuments.reduce((total, document) => total + document.chunk_count, 0),
    message: "Bundled synthetic sample documents are ready."
  };
}

export function demoChat(payload: ChatRequest): ChatResponse {
  const normalizedQuestion = payload.question.toLowerCase();
  const questionTerms = new Set(normalizedQuestion.split(/[^a-z0-9]+/).filter(Boolean));
  const match = sampleAnswers.find((sample) =>
    sample.terms.some((term) => questionTerms.has(term))
  );

  if (!match) {
    return {
      answer:
        "I do not have sufficient evidence in the synthetic sample documents to answer that question.",
      sources: [],
      retrieval_method: "sample-demo-confidence-gate",
      evaluation: payload.evaluate
        ? {
            ...evaluation,
            metrics: { ...evaluation.metrics, answer_relevancy: 0, context_relevancy: 0 },
            message: "The confidence gate correctly abstained for an unsupported sample question."
          }
        : null,
      request_id: "demo-request-abstained"
    };
  }

  return {
    answer: match.answer,
    sources: [
      {
        citation_index: 1,
        document_name: match.document_name,
        chunk_id: match.chunk_id,
        text: match.text,
        score: 0.982
      }
    ],
    retrieval_method: "sample-demo-bm25-char-tfidf",
    evaluation: payload.evaluate ? evaluation : null,
    request_id: `demo-request-${match.chunk_id}`
  };
}

export function demoEvaluation(): EvaluationResult {
  return evaluation;
}
