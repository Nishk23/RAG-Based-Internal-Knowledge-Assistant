from fastapi import APIRouter, Depends, Query

from app.dependencies import store
from app.schemas import AuditEvent, AuditEventListResponse
from app.security.auth import Principal, require_roles

router = APIRouter(prefix="/audit-events", tags=["audit"])
audit_admin = require_roles("admin")


@router.get("", response_model=AuditEventListResponse)
def list_audit_events(
    limit: int = Query(default=100, ge=1, le=1000),
    principal: Principal = Depends(audit_admin),
) -> AuditEventListResponse:
    events = [
        AuditEvent(**event) for event in store.get_audit_events(principal.tenant_id, limit=limit)
    ]
    return AuditEventListResponse(events=events)
