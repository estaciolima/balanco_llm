from django.urls import path

from dashboard import views

urlpatterns = [
    path("company/<uuid:company_id>/", views.company_dashboard, name="company-dashboard"),
]
