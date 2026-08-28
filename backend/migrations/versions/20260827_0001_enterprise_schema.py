"""Create tenant-isolated document, chunk, and audit tables."""

from alembic import op
import sqlalchemy as sa

revision = "20260827_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("document_id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("document_name", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("allowed_roles", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.UniqueConstraint("tenant_id", "checksum", name="uq_document_tenant_checksum"),
    )
    op.create_index("ix_documents_tenant_id", "documents", ["tenant_id"])
    op.create_index("ix_documents_tenant_created", "documents", ["tenant_id", "created_at"])

    op.create_table(
        "chunks",
        sa.Column("chunk_id", sa.String(length=96), primary_key=True),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("document_name", sa.String(length=512), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("allowed_roles", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.document_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_chunks_tenant_id", "chunks", ["tenant_id"])
    op.create_index("ix_chunks_tenant_document", "chunks", ["tenant_id", "document_id"])
    op.create_index("ix_chunks_tenant_created", "chunks", ["tenant_id", "created_at"])

    op.create_table(
        "audit_events",
        sa.Column("event_id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("resource_type", sa.String(length=128), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_events_tenant_id", "audit_events", ["tenant_id"])
    op.create_index("ix_audit_tenant_created", "audit_events", ["tenant_id", "created_at"])


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("chunks")
    op.drop_table("documents")
