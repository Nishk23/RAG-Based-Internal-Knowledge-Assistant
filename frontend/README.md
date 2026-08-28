# Frontend

Next.js 16 and React 19 browser client using OIDC Authorization Code with PKCE. It sends access
tokens to the FastAPI security boundary and uses SWR for authenticated document state.

## Development

```bash
npm ci
npm run dev
```

Configure `NEXT_PUBLIC_BACKEND_URL` and the public `NEXT_PUBLIC_OIDC_*` settings from
`.env.example`. These values are embedded into browser JavaScript and must never contain a client
secret. The backend's disabled-auth mode can be used only in a non-production local environment.

## Quality gates

```bash
npm ci
npm run lint
npm run typecheck
npm run build
npm audit --audit-level=high
```

The production image uses Next.js standalone output and runs as a non-root user. See the repository
[README](../README.md) and [Deployment guide](../docs/deployment.md).
