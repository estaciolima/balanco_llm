from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from audit.models import AuditEvent


@login_required
def audit_event_list(request):
    events = AuditEvent.objects.select_related("actor_user").all()
    if actor := request.GET.get("actor"):
        events = events.filter(actor_user__username__icontains=actor)
    if event_type := request.GET.get("event_type"):
        events = events.filter(event_type__icontains=event_type)
    if target_type := request.GET.get("target_type"):
        events = events.filter(target_type__icontains=target_type)
    if target_id := request.GET.get("target_id"):
        events = events.filter(target_id=str(target_id))
    return render(request, "audit/event_list.html", {"events": events})
