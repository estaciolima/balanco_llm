from audit.models import AuditEvent


def record_audit_event(
    *,
    event_type: str,
    target_type: str,
    target_id: str,
    actor_user=None,
    before: dict | None = None,
    after: dict | None = None,
    reason: str = "",
    ip_address: str | None = None,
    user_agent: str = "",
) -> AuditEvent:
    return AuditEvent.objects.create(
        actor_user=actor_user,
        event_type=event_type,
        target_type=target_type,
        target_id=str(target_id),
        before=before or {},
        after=after or {},
        reason=reason,
        ip_address=ip_address,
        user_agent=user_agent,
    )
