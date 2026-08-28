# Data governance guide

## Data inventory

| Data | Stored or processed in | Notes |
|---|---|---|
| Uploaded file text and metadata | PostgreSQL documents/chunks | Tenant and role ACL; checksum; file bytes are not retained by the application |
| User question and authorized context | API memory and configured LLM provider | Raw question is not stored in the application audit table |
| Answer and citations | Returned to browser; transient API memory | Persist only if a separately governed feature is added |
| Identity subject, tenant, roles | Access token and request memory | Subject appears in security audit rows |
| Audit events | PostgreSQL, then required central immutable export | Chat uses a SHA-256 question digest |
| Request/operational metadata | JSON logs, metrics, optional traces | No intentional document text or raw prompts |
| Secrets/tokens | Runtime secret system and process memory | Access tokens are sent by browser; never log them |

The LLM provider receives the question and selected authorized chunks. Treat this as external
processing even when using an enterprise endpoint. The provider's storage, training, abuse
monitoring, residency, subprocessors, and deletion terms must match the data classification.

## Required organizational decisions

Before ingestion, define:

- allowed and prohibited classifications, tenants, countries/regions, and source systems
- document owners, lawful basis/purpose, access groups, and review/expiry dates
- retention for documents, audit records, logs, traces, backups, and provider-side data
- legal hold, discovery, records management, data-subject, and deletion procedures
- whether malware scanning, DLP, OCR, encryption keys, or human approval are mandatory
- acceptable model providers, models, endpoints, and permitted use of customer data

The application does not infer classification or legal basis. Prevent prohibited data at the source
and ingress; labels alone are not a sufficient control.

## Tenant and role model

Every stored document and chunk belongs to one tenant. Allowed roles are an additional ACL within
that tenant. The IdP is authoritative for the caller's tenant and roles; the upload request cannot
choose another tenant. Administrators are tenant administrators, not global administrators.

For stricter defense in depth, deploy separate instances/databases or PostgreSQL row-level security
for high-risk tenants. Any global support function must be explicitly designed, audited, and tested.

## Data lifecycle

1. **Approve:** owner confirms classification, purpose, ACL, and provider eligibility.
2. **Ingest:** validate/scan, checksum, chunk, store transactionally, and audit.
3. **Use:** pre-filter by tenant/roles; disclose only top authorized context to the model provider.
4. **Review:** periodically revalidate ownership, access, freshness, and quality.
5. **Delete:** admin deletes document/chunks; propagate according to backup/provider/telemetry policy.
6. **Prove:** preserve required audit evidence and execute legal holds where applicable.

## Retention and deletion caveats

Application deletion cascades from a document to its chunks. It does not automatically remove data
from database backups, immutable audit exports, telemetry already emitted, browser screenshots,
provider retention, or downstream copies. Define and test each propagation path. Audit events may
need longer retention than content; minimize their metadata accordingly.

## Data quality and provenance

Use stable source identifiers and document owners. The current schema records filename, checksum,
timestamps, tenant, ACL, and chunk metadata, but it is not a full catalog. Regulated use may require
source URI, version/effective date, classification, owner, review date, jurisdiction, and approval
workflow. Extend the schema and migration before relying on those controls.

## Privacy and security review

- Complete a DPIA/privacy assessment where required.
- Confirm model-provider contract/DPA, training opt-out, residency, retention, and incident terms.
- Ensure support staff and telemetry operators have least-privilege, audited access.
- Test access removal, tenant transfer prohibition, deletion, and legal hold.
- Maintain representative evaluation data without copying production secrets or personal data into CI.
