# Public sample demo

The GitHub Pages deployment is a static portfolio demonstration of the user experience. It is
deliberately isolated from the production backend and contains no secrets, identity tokens, model
credentials, databases, or external API calls.

## Included behavior

- Three synthetic policy documents are packaged into the browser bundle.
- Supported sample questions return deterministic answers with source citations.
- Unsupported questions exercise the confidence gate and return a controlled abstention.
- The optional quality panel displays deterministic sample indicators.
- Upload interactions are simulated locally and do not read, transmit, or retain file contents.

## Excluded behavior

The static demo does not claim to exercise OIDC, tenant isolation, server-side RBAC, PostgreSQL,
Redis rate limits, malware scanning, OpenAI generation, audit persistence, or telemetry export.
Those controls remain implemented and tested in the deployable application and require the
organization-specific production configuration documented elsewhere in this repository.

## Build and deployment

GitHub Actions builds the frontend with `GITHUB_PAGES=true` and
`NEXT_PUBLIC_DEMO_MODE=true`. This switches Next.js from its hardened standalone container output
to a static export and activates only the synthetic in-browser data adapter. The ordinary Docker
and local builds continue to use the real FastAPI backend.

To reproduce the demo locally:

```bash
cd frontend
NEXT_PUBLIC_DEMO_MODE=true npm run dev
```

To verify the production frontend path, omit `NEXT_PUBLIC_DEMO_MODE` and use the Docker Compose or
local backend instructions in the main README.
