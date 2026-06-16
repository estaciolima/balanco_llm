from django.urls import path

from companies import views

urlpatterns = [
    path("", views.company_list, name="company-list"),
    path("new/", views.company_create, name="company-create"),
    path("<uuid:company_id>/", views.company_detail, name="company-detail"),
]
