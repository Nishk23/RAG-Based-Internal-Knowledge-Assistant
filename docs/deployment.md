# Production deployment guide

## Reference topology

Deploy the frontend and API behind TLS ingress/WAF. Run the API as multiple stateless replicas and
use managed, private PostgreSQL and Redis services. Run migrations as a single release job. Connect
to an enterprise OIDC provider, secret manager, approved LLM endpoint, centralized telemetry, and—if
required—ClamAV. Do not expose PostgreSQL, Redis, ClamAV, or the OTLP collector publicly.

The checked-in Compose stack is a local reference. It is not an HA production topology.

## Prerequisites

- Python 3.12-compatible backend image and Node.js 22-compatible frontend image
- PostgreSQL with encrypted connections, backups, point-in-time recovery, and least-privilege users
- Redis with encrypted/private transport, authentication, persistence policy, and HA as required
- OIDC public client for the browser and an API resource/audience
- Runtime secret injection and rotation
- TLS ingress, explicit hostname/origin allowlists, WAF/body limits, and network policies
- Central JSON log, Prometheus, optional OTLP, alerting, and immutable audit destinations
- Approved LLM provider configuration and data-processing controls

## Build

Build images from a reviewed commit. The frontend OIDC values are public build-time metadata:

```bash
docker build -t knowledge-backend:<commit> backend
docker build \
  --build-arg NEXT_PUBLIC_BACKEND_URL=https://api.knowledge.example.com \
  --build-arg NEXT_PUBLIC_OIDC_AUTHORITY=https://identity.example.com/ \
  --build-arg NEXT_PUBLIC_OIDC_CLIENT_ID=knowledge-assistant-web \
  --build-arg NEXT_PUBLIC_OIDC_REDIRECT_URI=https://knowledge.example.com \
  --build-arg NEXT_PUBLIC_OIDC_SCOPE='openid profile knowledge.read' \
  -t knowledge-frontend:<commit> frontend
```

Scan images, generate/store an SBOM, sign the immutable digest, and admit only verified images from
the trusted registry. Never pass server-side secrets as Docker build arguments.

## Required backend configuration

`ENVIRONMENT=production` activates fail-closed validation. At minimum configure:

```dotenv
ENVIRONMENT=production
AUTH_MODE=oidc
OIDC_ISSUER=https://identity.example.com/
OIDC_AUDIENCE=knowledge-assistant-api
OIDC_JWKS_URL=https://identity.example.com/.well-known/jwks.json
OIDC_ALGORITHMS=RS256
OIDC_TENANT_CLAIM=tenant_id
OIDC_ROLES_CLAIM=roles
DATABASE_URL=postgresql+psycopg://...
REDIS_URL=rediss://...
CORS_ORIGINS=https://knowledge.example.com
TRUSTED_HOSTS=api.knowledge.example.com
METRICS_BEARER_TOKEN=<secret-manager-reference>
OPENAI_API_KEY=<secret-manager-reference>
```

Review all limits in `.env.example`. If uploads require malware scanning, set
`REQUIRE_MALWARE_SCAN=true` and `CLAMAV_HOST`. Use an approved `OPENAI_BASE_URL` when traffic must go
through an enterprise gateway. Secrets must be resolved into the workload at runtime.

## Database release process

1. Back up the database and verify the recovery point.
2. Test the migration against a production-sized staging copy.
3. Stop if the migration introduces an incompatible change requiring a coordinated release.
4. Run exactly one migration job:

   ```bash
   alembic upgrade head
   ```

5. Confirm the revision and database health, then roll out API replicas gradually.
6. Roll out the frontend after the API is compatible.

Application startup checks database connectivity in production but deliberately does not create or
migrate tables. This avoids concurrent workers racing schema changes.

## Runtime hardening

- Run as the image's non-root user with a read-only root filesystem, writable `/tmp` only, all
  capabilities dropped, no privilege escalation, and a default seccomp profile.
- Set CPU/memory/ephemeral-storage requests and limits. Restrict egress to JWKS, data services,
  telemetry, malware scanner, DNS, and the approved model endpoint.
- Terminate TLS at a trusted ingress and use TLS/mTLS for internal connections as policy requires.
- Configure request-size, header-size, timeout, concurrency, and per-identity/tenant gateway quotas.
- Keep API documentation disabled in production (automatic with `ENVIRONMENT=production`).
- Scrape `/metrics` over a private network with its dedicated bearer token.

## Health and rollout

- Liveness: `GET /health/live`
- Readiness: `GET /health/ready` (database and rate-limit store)

Use readiness for traffic admission and liveness only for process recovery. Choose probe intervals
that avoid restarts during short dependency interruptions. Use canary or rolling deployment,
monitoring 5xx rate, latency, readiness, LLM failures, rate limiting, and database saturation.

## Acceptance before production

- All repository CI checks pass from the exact commit/image digest.
- OIDC negative tests and tenant-isolation tests pass in the target environment.
- Dependency, container, SAST, DAST, secret, and IaC scans meet policy.
- Backup restore and documented rollback have been exercised.
- Load/cost tests cover expected and peak document/query volume.
- Threat model, privacy/DPA, data classification, retention, and model-provider reviews are approved.
- Alerts and on-call routing have been tested; the operations runbook has named owners.

See [Operations runbook](operations-runbook.md) for steady-state and incident procedures.
