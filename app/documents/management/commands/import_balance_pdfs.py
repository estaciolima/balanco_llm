from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.base import File
from django.core.management.base import BaseCommand, CommandError

from companies.models import Company
from documents.services import create_balance_document


class Command(BaseCommand):
    help = "Import PDF files from a directory into a company"

    def add_arguments(self, parser):
        parser.add_argument("company_id")
        parser.add_argument("directory")
        parser.add_argument("--username", required=True)
        parser.add_argument("--fiscal-year", required=True, type=int)

    def handle(self, *args, **options):
        company = Company.objects.get(pk=options["company_id"])
        user = get_user_model().objects.get(username=options["username"])
        directory = Path(options["directory"])
        if not directory.exists():
            raise CommandError(f"Directory does not exist: {directory}")

        for pdf_path in directory.glob("*.pdf"):
            with pdf_path.open("rb") as stream:
                django_file = File(stream, name=pdf_path.name)
                create_balance_document(
                    company=company,
                    uploaded_file=django_file,
                    actor_user=user,
                    fiscal_year=options["fiscal_year"],
                )
                self.stdout.write(self.style.SUCCESS(f"Imported {pdf_path.name}"))
