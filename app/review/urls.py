from django.urls import path

from review import views

urlpatterns = [
    path("", views.review_queue, name="review-queue"),
    path("<uuid:task_id>/", views.review_detail, name="review-detail"),
    path("<uuid:task_id>/approve/", views.review_approve, name="review-approve"),
    path("<uuid:task_id>/correct/", views.review_correct, name="review-correct"),
    path("<uuid:task_id>/reject/", views.review_reject, name="review-reject"),
]
