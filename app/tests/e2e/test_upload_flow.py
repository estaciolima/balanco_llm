import pytest
from django.contrib.auth import get_user_model


@pytest.mark.django_db(transaction=True)
def test_login_company_creation_and_pdf_upload_flow(live_server, page, sample_pdf):
    get_user_model().objects.create_user(username="reviewer", password="password123")

    page.goto(f"{live_server.url}/login/")
    page.get_by_label("Username").fill("reviewer")
    page.get_by_label("Password").fill("password123")
    page.get_by_role("button", name="Sign in").click()

    page.goto(f"{live_server.url}/companies/new/")
    page.get_by_label("Legal name").fill("ACME Holdings")
    page.get_by_label("Display name").fill("ACME")
    page.get_by_label("Tax identifier").fill("123456789")
    page.get_by_label("Country").fill("BR")
    page.get_by_role("button", name="Save").click()

    assert page.get_by_role("heading", name="ACME").is_visible()
    page.get_by_role("link", name="Upload balance PDF").click()
    page.get_by_label("File").set_input_files(str(sample_pdf))
    page.get_by_label("Balance year").select_option("2025")
    page.get_by_role("button", name="Upload").click()

    assert page.get_by_text("PDF uploaded and queued for processing.").is_visible()
    assert page.get_by_text("sample-balance.pdf").is_visible()
