# Security controls

## Security objectives

The application is designed to prevent cross-tenant retrieval, require centrally managed identity,
reduce malicious-upload and prompt-injection risk, avoid sensitive telemetry, and fail closed when
production security dependencies are absent.

## Identity and authorization

- Production accepts only OIDC bearer access tokens. Disabled authentication is rejected at startup.
- JWTs are verified against JWKS with an algorithm allowlist and configured issuer and audience.
  `exp`, `iat`, and `sub` are required.
- Tenant and role claim names are configurable. Only `reader`, `editor`, and `admin` are recognized.
- Endpoint permissions follow least privilege. Deletion, audit access, and evaluation require admin.
- Documents and chunks carry a tenant ID and allowed roles. Store queries enforce both before
  retrieval, preventing unauthorized content from influencing scores or model prompts.

## Data and upload protection

- File bodies are streamed with hard byte limits and extracted text/page limits.
- Filenames are sanitized; supported extensions are `.txt`, `.md`, and `.pdf`.
- PDF signatures and strict parsing are checked. Text-like uploads containing NUL bytes are rejected.
- SHA-256 deduplicates within a tenant. Database ingestion is transactional.
- ClamAV scanning is supported. High-assurance deployments should require it and monitor scanner
  health; an unavailable required scanner rejects ingestion.
- The database connection must use PostgreSQL in production. Enforce TLS and least-privilege
  credentials in the platform connection configuration.

## RAG-specific defenses

Retrieved documents are labeled as untrusted data. The model is instructed not to follow commands
inside documents, to use only supplied evidence, and to abstain when evidence is insufficient.
Generated factual answers must cite valid source indexes. Confidence filtering avoids generation on
weak retrieval results.

These are defense-in-depth controls, not proof against every prompt injection. Keep model tools
disabled unless separately sandboxed and authorized, test adversarial documents, and review any
future tool-calling or agentic capability as a new trust boundary.

## Abuse and network controls

- Redis-backed fixed-window limits protect chat, upload, and evaluation. Production fails closed if
  the rate-limit store is unavailable.
- CORS uses an explicit allowlist and does not allow credentials. Trusted host validation is enabled.
- API responses set no-store, MIME-sniffing, frame, referrer, and restrictive CSP headers.
- Compose binds ports to loopback. Production must place the services behind authenticated TLS
  ingress, WAF/DDoS protection, request/body limits, and network policies.
- `/metrics` uses a dedicated bearer token. Prefer private scrape networking in addition to the token.

## Secrets and supply chain

- Production-critical configuration is validated at startup. Do not store secrets in `.env`, source,
  image layers, frontend `NEXT_PUBLIC_*` settings, or CI logs.
- Use a secret manager with workload identity, rotation, narrow access, and audit logging.
- Python and npm dependencies are locked. CI runs lint, typing, tests, migrations, retrieval
  regression, dependency audits, and image builds; Dependabot proposes updates.
- Before release, protect `main`, require CI and review, enable secret scanning and push protection,
  and consider signed commits/images plus SBOM and provenance generation in the deployment system.

## Telemetry privacy

Structured logs contain request and operational metadata, not file contents or raw questions. Chat
audit events store a question hash. Prometheus route labels use route templates to avoid identifiers.
OTLP exporting is optional. Treat logs, traces, metrics, and audit events as sensitive operational
data and apply access control, encryption, regional requirements, and retention limits.

## Production review checklist

- Validate IdP claim issuance, group-to-role governance, token lifetime, key rotation, and offboarding.
- Verify no wildcard CORS/trusted-host rules and configure TLS for every service connection.
- Require malware scanning if dictated by the data classification.
- Run SAST, DAST, secret scanning, image scanning, and an independent penetration test.
- Prove tenant isolation with organization-specific negative tests.
- Complete provider privacy/DPA review and ensure prohibited data cannot be uploaded.
- Test restore, key/secret rotation, Redis failure, database failover, and provider outage.
- Export audit events to an immutable centralized destination and alert on suspicious operations.

Report vulnerabilities according to [SECURITY.md](../SECURITY.md). The structured risk analysis is in
[Threat model](threat-model.md).
