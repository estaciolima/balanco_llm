from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from companies.models import Company
from documents.forms import DocumentUploadForm
from documents.models import BalanceDocument
from documents.services import (
    DuplicateDocumentError,
    UnsupportedDocumentError,
    create_balance_document,
    requeue_processing,
)


@login_required
def document_upload(request, company_id):
    company = get_object_or_404(Company, pk=company_id)
    form = DocumentUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            document = create_balance_document(
                company=company,
                uploaded_file=form.cleaned_data["file"],
                actor_user=request.user,
                fiscal_year=form.cleaned_data["fiscal_year"],
            )
        except UnsupportedDocumentError as exc:
            form.add_error("file", str(exc))
        except DuplicateDocumentError as exc:
            messages.warning(request, "This PDF already exists for processing.")
            return redirect("document-detail", document_id=exc.document.pk)
        else:
            messages.success(request, "PDF uploaded and queued for processing.")
            return redirect("document-detail", document_id=document.pk)

    return render(
        request,
        "documents/document_upload.html",
        {"company": company, "form": form},
    )


@login_required
def document_detail(request, document_id):
    document = get_object_or_404(
        BalanceDocument.objects.select_related("company", "reporting_period").prefetch_related(
            "processing_runs",
            "extracted_line_items",
        ),
        pk=document_id,
    )
    line_items = document.extracted_line_items.order_by(
        "source_account_code",
        "source_hierarchy_level",
        "source_label",
    )
    return render(
        request,
        "documents/document_detail.html",
        {"document": document, "line_items": line_items},
    )


@login_required
def document_reprocess(request, document_id):
    document = get_object_or_404(BalanceDocument, pk=document_id)
    if request.method == "POST":
        requeue_processing(document, request.user)
        messages.success(request, "Document queued for reprocessing.")
    return redirect("document-detail", document_id=document.pk)
