from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from review.forms import ReviewCorrectionForm, ReviewRejectForm
from review.models import ReviewTask
from review.services import approve_review_task, correct_review_task, reject_review_task


@login_required
def review_queue(request):
    tasks = ReviewTask.objects.select_related("document", "extracted_line_item").order_by("created_at")
    return render(request, "review/review_queue.html", {"tasks": tasks})


@login_required
def review_detail(request, task_id):
    review_task = get_object_or_404(
        ReviewTask.objects.select_related("document", "extracted_line_item"), pk=task_id
    )
    correction_form = ReviewCorrectionForm(
        initial={
            "standard_line_item": getattr(
                review_task.extracted_line_item, "suggested_standard_line_item", None
            ),
            "value": getattr(review_task.extracted_line_item, "normalized_value", None),
            "currency": getattr(review_task.extracted_line_item, "currency", ""),
            "reporting_period": getattr(review_task.extracted_line_item, "reporting_period", None),
        }
    )
    reject_form = ReviewRejectForm()
    return render(
        request,
        "review/review_detail.html",
        {
            "review_task": review_task,
            "correction_form": correction_form,
            "reject_form": reject_form,
        },
    )


@login_required
def review_approve(request, task_id):
    review_task = get_object_or_404(ReviewTask, pk=task_id)
    if request.method == "POST":
        approve_review_task(review_task=review_task, actor_user=request.user)
        messages.success(request, "Review task approved.")
    return redirect("review-detail", task_id=review_task.pk)


@login_required
def review_correct(request, task_id):
    review_task = get_object_or_404(ReviewTask, pk=task_id)
    form = ReviewCorrectionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        correct_review_task(
            review_task=review_task,
            actor_user=request.user,
            standard_line_item=form.cleaned_data["standard_line_item"],
            value=form.cleaned_data["value"],
            currency=form.cleaned_data["currency"],
            reporting_period=form.cleaned_data["reporting_period"],
            reason=form.cleaned_data["reason"],
        )
        messages.success(request, "Review task corrected.")
        return redirect("review-detail", task_id=review_task.pk)
    return render(request, "review/review_correct.html", {"review_task": review_task, "form": form})


@login_required
def review_reject(request, task_id):
    review_task = get_object_or_404(ReviewTask, pk=task_id)
    form = ReviewRejectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        reject_review_task(
            review_task=review_task,
            actor_user=request.user,
            reason=form.cleaned_data["reason"],
        )
        messages.success(request, "Review task rejected.")
        return redirect("review-detail", task_id=review_task.pk)
    return render(request, "review/review_reject.html", {"review_task": review_task, "form": form})
