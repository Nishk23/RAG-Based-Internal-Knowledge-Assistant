# Threat model

## Method and assumptions

This is a repository-level STRIDE-style review. It assumes the identity provider, managed database,
Redis, secret manager, ingress, CI runners, administrators, and LLM provider can be configured
securely but are outside this codebase. It must be updated for each actual deployment and after any
new data source, model tool, identity flow, storage engine, or external integration.

## Assets

- Internal document content, filenames, metadata, and access rules
- Questions, generated answers, citations, and inferred organizational knowledge
- Tenant boundaries, identities, roles, access tokens, and service credentials
- Audit evidence, operational telemetry, and availability
- Source, dependency locks, container images, and deployment configuration

## Actors

- Authorized readers, editors, and administrators
- Malicious or compromised tenant users
- External unauthenticated attackers
- Malicious document authors attempting indirect prompt injection
- Compromised dependencies, CI jobs, administrators, infrastructure, or model providers

## Trust boundaries

1. Browser to identity provider
2. Browser to frontend/API
3. API to JWKS, PostgreSQL, Redis, ClamAV, and OTLP collector
4. API to the LLM provider, where authorized question/context data leaves the deployment
5. CI and image supply chain to the production runtime
6. Application audit storage to immutable security retention

## Threats and mitigations

| Threat | Primary mitigations | Residual risk / required owner action |
|---|---|---|
| Forged, expired, or wrong-service token | JWKS signature, issuer/audience/algorithm allowlists, required claims | IdP configuration, token lifetime, key rotation, replay controls |
| Privilege escalation | Recognized role allowlist, endpoint RBAC, server-side claims | Govern group-to-role mapping and admin assignment |
| Cross-tenant document access | Tenant predicates plus role ACL before retrieval | Test database changes and future indexes for isolation; consider DB RLS |
| ID enumeration | Tenant-scoped store operations and generic authorization behavior | Monitor repeated misses and rate-limit at ingress |
| Malicious/oversized upload | Stream limits, type/signature checks, strict parser, limits, optional ClamAV | Parser zero-days remain; isolate scanning/parsing for high-risk deployments |
| Stored prompt injection | Untrusted-context prompt, evidence-only instruction, confidence gate, citation validation | Model behavior is probabilistic; maintain adversarial evals and no privileged tools |
| Data exfiltration to model provider | Only authorized top-K context; no evaluator-model egress | Provider receives question/context; require policy, DPA, residency, and retention review |
| Resource exhaustion/cost abuse | Redis limits, upload/extraction/top-K bounds, LLM timeout/retries | Add ingress quotas, concurrency budgets, account spend alerts, and load tests |
| Audit tampering/repudiation | Request IDs and tenant audit rows | DB admins can alter rows; export to append-only/WORM SIEM |
| Sensitive logging | Structured metadata-only logs; query hashes | Verify collector transformations and exception paths; restrict telemetry access |
| Dependency/image compromise | Locks, audits, CI, non-root minimal images, Dependabot | Add trusted registry, signature verification, SBOM, provenance, continuous scanning |
| Database/Redis interception | Platform-provided connection security | Require TLS, private networks, credential rotation, and firewall rules |
| Secret disclosure | No client secrets; runtime secret injection guidance | Configure scanning, redact CI, rotate on exposure, avoid build arguments for secrets |
| Service outage | Liveness/readiness, timeouts, retries, health checks | Deploy HA data services/replicas, capacity plans, backups, failover drills |
| CSRF/browser token theft | Bearer API, no cookie auth, OIDC PKCE, restrictive headers | XSS in same origin can steal tokens; enforce CSP at frontend ingress and review UI deps |

## Abuse cases to test

- A tenant-A token cannot list, retrieve, cite, delete, or infer tenant-B content.
- A reader cannot upload/delete/evaluate or read audit events; an editor cannot delete/read audit.
- Expired, unsigned, wrong-audience, wrong-issuer, missing-tenant, and unknown-role tokens fail.
- A document instructing the model to ignore policy does not cause non-evidence actions or disclosure.
- Empty, irrelevant, malformed, polyglot, decompression-heavy, and maximum-size files are controlled.
- Redis/ClamAV/database/model outages produce bounded, non-sensitive errors and appropriate readiness.
- Invalid citation indexes are rejected or converted to a controlled abstention.

## Accepted design risks

- Sparse retrieval can miss semantically equivalent wording.
- LLM output remains nondeterministic and requires use-case-specific human oversight.
- Application-level tenant predicates are not database row-level security.
- Compose is not highly available, and its example credentials are not production secrets.
- Audit storage is mutable until exported to infrastructure controlled by the security organization.
