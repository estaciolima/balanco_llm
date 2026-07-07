import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_login_and_logout_flow(client, user):
    response = client.post(
        reverse("login"),
        {"username": user.username, "password": "password123"},
        follow=True,
    )

    assert response.status_code == 200
    assert response.wsgi_request.user.is_authenticated

    response = client.post(reverse("logout"), follow=True)

    assert response.status_code == 200
    assert not response.wsgi_request.user.is_authenticated
