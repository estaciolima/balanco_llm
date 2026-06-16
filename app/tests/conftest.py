import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        username="reviewer", email="reviewer@example.com", password="password123"
    )
