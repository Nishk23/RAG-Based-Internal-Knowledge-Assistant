import {
  ChatRequest,
  ChatResponse,
  EvaluationRequest,
  EvaluationResult,
  HealthResponse,
  SampleLoadResponse,
  UploadResponse,
  DocumentSummary
} from "@/lib/types";
import {
  DEMO_MODE,
  demoChat,
  demoDocuments,
  demoEvaluation,
  demoSampleLoad,
  demoUpload
} from "@/lib/demo";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

function authorizationHeaders(accessToken?: string): HeadersInit {
  return accessToken ? { Authorization: `Bearer ${accessToken}` } : {};
}

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const fallback = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      throw new Error(body?.detail ?? fallback);
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error(fallback);
    }
  }
  return response.json() as Promise<T>;
}

export async function uploadDocument(file: File, accessToken?: string): Promise<UploadResponse> {
  if (DEMO_MODE) {
    return demoUpload(file);
  }

  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${BACKEND_URL}/documents/upload`, {
    method: "POST",
    headers: authorizationHeaders(accessToken),
    body: formData
  });
  return parseJson<UploadResponse>(response);
}

export async function listDocuments(accessToken?: string): Promise<DocumentSummary[]> {
  if (DEMO_MODE) {
    return demoDocuments;
  }

  const response = await fetch(`${BACKEND_URL}/documents`, {
    headers: authorizationHeaders(accessToken)
  });
  const body = await parseJson<{ documents: DocumentSummary[] }>(response);
  return body.documents;
}

export async function loadSampleDocuments(accessToken?: string): Promise<SampleLoadResponse> {
  if (DEMO_MODE) {
    return demoSampleLoad();
  }

  const response = await fetch(`${BACKEND_URL}/documents/load-sample`, {
    method: "POST",
    headers: authorizationHeaders(accessToken)
  });
  return parseJson<SampleLoadResponse>(response);
}

export async function askQuestion(payload: ChatRequest, accessToken?: string): Promise<ChatResponse> {
  if (DEMO_MODE) {
    return demoChat(payload);
  }

  const response = await fetch(`${BACKEND_URL}/chat`, {
    method: "POST",
    headers: {
      ...authorizationHeaders(accessToken),
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  return parseJson<ChatResponse>(response);
}

export async function runEvaluation(
  payload: EvaluationRequest,
  accessToken?: string
): Promise<EvaluationResult> {
  if (DEMO_MODE) {
    return demoEvaluation();
  }

  const response = await fetch(`${BACKEND_URL}/evaluate`, {
    method: "POST",
    headers: {
      ...authorizationHeaders(accessToken),
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  return parseJson<EvaluationResult>(response);
}

export async function healthCheck(): Promise<HealthResponse> {
  if (DEMO_MODE) {
    return { status: "ok", service: "sample-demo", version: "1.0.0" };
  }

  const response = await fetch(`${BACKEND_URL}/health`);
  return parseJson<HealthResponse>(response);
}
