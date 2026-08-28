# Security policy

## Reporting a vulnerability

Please do not open a public GitHub issue for a suspected vulnerability or include secrets,
tokens, private documents, personal data, exploit details, or tenant information in public channels.

Use GitHub's **Security** tab and **Report a vulnerability** private-reporting flow for this
repository. Include the affected version/commit, component, impact, minimal reproduction, relevant
configuration with all secrets removed, and suggested mitigation if known.

If private vulnerability reporting is unavailable, contact the repository owner through a private,
verified channel and ask for a secure reporting method before sending details.

## Response expectations

This open-source repository does not promise a contractual response SLA. Maintainers should
acknowledge a valid private report, assess severity and affected versions, coordinate remediation
and disclosure, publish a security advisory where appropriate, and credit the reporter if requested.
Do not test against systems or data you do not own or have explicit authorization to assess.

## Supported versions

Security fixes target the latest commit on `main` until formal releases and a support matrix are
published. Deployments should use a reviewed immutable commit/image digest and keep dependencies
current. Organization-specific production environments remain the operator's responsibility.

## Deployment security

See [Security controls](docs/security.md), [Threat model](docs/threat-model.md), and
[Production deployment](docs/deployment.md). A green repository CI run alone is not production
authorization; each deployment needs identity, privacy, infrastructure, threat-model, penetration,
backup/restore, and incident-response approval.
