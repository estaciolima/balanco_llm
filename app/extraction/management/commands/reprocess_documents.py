from django.core.management.base import BaseCommand

from documents.models import BalanceDocument
from documents.services import requeue_processing


class Command(BaseCommand):
    help = "Requeue document processing for one or more document ids"

    def add_arguments(self, parser):
        parser.add_argument("document_ids", nargs="+")

    def handle(self, *args, **options):
        for document_id in options["document_ids"]:
            document = BalanceDocument.objects.get(pk=document_id)
            requeue_processing(document, document.uploaded_by)
            self.stdout.write(self.style.SUCCESS(f"Queued reprocessing for {document_id}"))
