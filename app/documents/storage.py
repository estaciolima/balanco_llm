from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class LocalDocumentStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(location=Path(settings.MEDIA_ROOT), base_url=settings.MEDIA_URL)


def get_document_storage():
    return LocalDocumentStorage()
