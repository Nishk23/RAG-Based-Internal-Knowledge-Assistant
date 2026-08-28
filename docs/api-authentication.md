# API authentication and authorization

## OIDC access tokens

Production requires `AUTH_MODE=oidc`. Clients send an access token—not an ID token—in every protected
API request:

```http
Authorization: Bearer eyJ...
X-Request-ID: optional-client-correlation-id
```

The API verifies the signature using `OIDC_JWKS_URL`, then verifies `OIDC_ISSUER`, `OIDC_AUDIENCE`,
the configured algorithm allowlist, expiry, issued-at time, and subject. Symmetric shared-secret
algorithms should not be added to the allowlist.

Required logical claims:

```json
{
  "sub": "00u-user-id",
  "iss": "https://identity.example.com/",
  "aud": "knowledge-assistant-api",
  "iat": 1787850000,
  "exp": 1787853600,
  "tenant_id": "tenant-a",
  "roles": ["reader", "editor"]
}
```

The tenant and role claim keys are configurable through `OIDC_TENANT_CLAIM` and
`OIDC_ROLES_CLAIM`. Roles may be a list or a comma/space-delimited string. Unknown roles are ignored;
tokens with no recognized role or tenant are rejected.

## Roles

- `reader`: view authorized documents and ask questions.
- `editor`: reader permissions plus upload and sample ingestion.
- `admin`: all operations, including deletion, deterministic evaluation, and tenant audit access.

Document ACLs specify which of these roles may retrieve each document. Tenant filtering and ACL
intersection are enforced in database access, not in the browser.

## Browser configuration

Register the frontend as a public OIDC client using Authorization Code with PKCE and no client
secret. Configure exact sign-in and post-logout redirect URIs and narrow scopes:

```dotenv
NEXT_PUBLIC_OIDC_AUTHORITY=https://identity.example.com/
NEXT_PUBLIC_OIDC_CLIENT_ID=knowledge-assistant-web
NEXT_PUBLIC_OIDC_REDIRECT_URI=https://knowledge.example.com
NEXT_PUBLIC_OIDC_SCOPE=openid profile knowledge.read
```

The IdP must issue an access token whose audience matches the API. `NEXT_PUBLIC_*` values are
embedded in browser JavaScript and must never contain a secret.

## API examples

```bash
curl -H "Authorization: Bearer $ACCESS_TOKEN" https://api.example.com/me

curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the incident escalation policy?","top_k":5}' \
  https://api.example.com/chat

curl -H "Authorization: Bearer $EDITOR_TOKEN" \
  -F "file=@policy.pdf" \
  -F 'allowed_roles=["reader","editor","admin"]' \
  https://api.example.com/documents/upload
```

Use a separate bearer secret for `/metrics`; an OIDC access token does not grant metrics access.

## Development mode

`AUTH_MODE=disabled` creates the configured local principal only when the environment is not
production. It exists for local tests and must never be exposed to an untrusted network. Production
configuration rejects disabled authentication at startup.

## Identity-provider acceptance tests

- Valid access tokens work and ID tokens/wrong audiences fail.
- Expired tokens and tokens signed by an unknown/retired key fail.
- Missing tenant or recognized roles fails without disclosing content.
- Role removal and account disablement take effect within the approved token lifetime.
- Key rotation works through JWKS caching without accepting removed keys beyond policy.
- Frontend logout clears local OIDC session state and the provider session as configured.
