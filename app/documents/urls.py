from django.urls import path

from documents import views

urlpatterns = [
    path("<uuid:document_id>/", views.document_detail, name="document-detail"),
    path("<uuid:document_id>/reprocess/", views.document_reprocess, name="document-reprocess"),
    path("company/<uuid:company_id>/upload/", views.document_upload, name="document-upload"),
]
