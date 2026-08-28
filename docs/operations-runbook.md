# Operations runbook

## Service objectives to define

Before launch, owners must set measurable SLOs for API availability, p95/p99 chat latency,
ingestion success, retrieval quality, and recovery objectives (RTO/RPO). This repository does not
invent business targets. Use the first load test and a controlled pilot to establish realistic
baselines, then create error-budget alerts rather than alerting on every transient failure.

## Dashboards and alerts

Monitor at least:

- request rate, status, and latency by route template from Prometheus
- API in-flight requests, replica restarts, readiness, CPU, memory, and file descriptors
- PostgreSQL connections, locks, transaction latency, storage, replication, and backup age
- Redis availability, memory, evictions, persistence/replication, and rejected connections
- LLM latency, timeout/provider error rate, token/cost budgets, and configured quota consumption
- upload rejection/malware findings, rate-limit events, admin actions, and authentication failures
- golden/production retrieval indicators, abstention rate, citation failures, and user feedback

Page on sustained user impact, security signals, exhaustion, or loss of redundancy. Ticket slower
capacity and quality trends.

## Correlation and privacy

Every response carries `X-Request-ID`. Search JSON logs and traces by that value. Never paste access
tokens, raw questions, document text, or secrets into incident tickets. Audit chat records use a
question hash; application logs are intentionally metadata-only.

## Common incidents

### Readiness returns 503

1. Inspect the readiness response to distinguish `database` from `rate_limit_store`.
2. Check managed-service status, DNS, network policy, TLS/certificate, secret rotation, pool limits,
   and saturation.
3. Keep the replica out of service until dependencies recover; do not bypass production fail-closed
   rate limiting.
4. If all replicas are affected, invoke the dependency incident/DR plan and communicate impact.

### LLM provider errors or high latency

1. Correlate provider failures, timeouts, rate limits, and spend/quota dashboards.
2. Confirm the configured endpoint/model and recent secret or network changes.
3. Reduce concurrency or apply an approved feature restriction if cost/availability is threatened.
4. Do not silently switch providers: that changes the data-processing boundary and requires approval.
5. After recovery, evaluate queued/retried user behavior and quality metrics.

### Suspected cross-tenant disclosure

1. Declare a security incident and preserve logs, traces, audit events, image digest, config version,
   database snapshots, and relevant request IDs.
2. Disable affected access paths or isolate the service. Revoke exposed tokens/secrets as indicated.
3. Determine whether the source was identity claims, document ACLs, store filtering, migration/data
   corruption, cache/index changes, logs, or the model provider.
4. Follow legal/privacy notification procedures. Do not alter evidence in place.
5. Add a regression test and update the threat model before restoring the affected capability.

### Malicious upload or scanner outage

1. When scanning is mandatory, keep ingestion disabled/failing closed until scanner health returns.
2. Quarantine metadata and preserve the original object only according to security handling policy.
3. Rotate parser/scanner images if vulnerable and rescan affected corpus material.
4. Search audit events for the actor, tenant, checksum, and related ingestion attempts.

### Retrieval quality regression

1. Compare abstention, citation validity, Recall@K/MRR, and recent corpus/config/model changes.
2. Re-run the golden dataset and a representative tenant-safe evaluation set.
3. Roll back threshold/chunking/prompt/model changes independently where possible.
4. Never lower authorization filters or confidence thresholds solely to hide a metric regression.

## Backup, restore, and deletion

- Use managed PostgreSQL encrypted backups plus point-in-time recovery. Monitor backup age and test a
  restore into an isolated environment on a scheduled basis.
- Define Redis recovery according to the desired rate-limit continuity; Redis is not the document
  system of record.
- Restore tests must verify schema revision, counts by tenant, ACL integrity, checksums, audit rows,
  application readiness, and sample authorized/unauthorized retrieval.
- A document deletion is a logical application deletion of the document and its chunks. Define how
  deletion propagates to backups, telemetry, audits, model-provider retention, and legal holds.

## Secret and key rotation

1. Create a new secret/version and grant the workload access.
2. Roll or reload workloads and validate readiness and representative requests.
3. Revoke the previous value only after all consumers have moved.
4. Record the change without recording the secret. Emergency exposure requires immediate incident
   handling and scope analysis.

JWKS signing-key rotation is IdP-managed. Exercise overlap and removal behavior before production.

## Rollback

Deploy immutable image digests. Application rollback is safe only while the old version remains
compatible with the current schema. Prefer forward-compatible expand/migrate/contract migrations.
Never improvise a destructive database downgrade during an incident; restore or run an explicitly
reviewed recovery migration.

## Evidence after an incident

Retain the timeline, request IDs, affected principals/tenants, image and dependency versions,
configuration revision, audit export, telemetry, provider incident references, decisions, customer
impact, remediation, and new regression tests. Apply the organization's evidence-retention and
access-control policy.
