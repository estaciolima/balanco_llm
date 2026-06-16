from audit.services import record_audit_event


def test_record_audit_event_creates_row(db, user):
    event = record_audit_event(
        event_type="document.uploaded",
        target_type="BalanceDocument",
        target_id="123",
        actor_user=user,
        after={"status": "queued"},
    )

    assert event.actor_user == user
    assert event.event_type == "document.uploaded"
    assert event.after["status"] == "queued"
