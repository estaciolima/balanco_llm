from django.urls import path

from audit import views

urlpatterns = [
    path("", views.audit_event_list, name="audit-event-list"),
]
