"""
Controller-level tests for the Domains API (POST/GET /domains).

Isolation strategy
------------------
These tests import ``app`` (which requires a live database connection for the
initial ``db.py`` setup – same requirement as all other tests in this project).
Once the app is instantiated, every call to the route functions is intercepted
at the service boundary by patching ``api.domains._get_domain_service``.
This means **no SQL is executed during the test run itself**.

Complementary pure-unit tests (no DB required at all) live in
``test_domains_service.py``.
"""
import sys
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app as flask_app
from domains.service import (
    DomainAlreadyExistsError,
    DomainService,
    InvalidWebsiteURLError,
    ParentDomainNotFoundError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_DOMAIN = {
    "id": 1,
    "key": "EXAMPLE_COM",
    "address": "example.com",
    "parent_id": None,
    "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
}


@pytest.fixture(scope="module")
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


@pytest.fixture
def mock_service():
    """
    Patch the service factory so that no database queries reach the DB.
    Yields a MagicMock pre-configured with sensible defaults.
    """
    with patch("api.domains._get_domain_service") as factory:
        svc = MagicMock(spec=DomainService)
        svc.add_domain.return_value = SAMPLE_DOMAIN
        svc.get_domain.return_value = SAMPLE_DOMAIN
        svc.list_domains.return_value = [SAMPLE_DOMAIN]
        factory.return_value = svc
        yield svc


# ---------------------------------------------------------------------------
# POST /domains/ – success
# ---------------------------------------------------------------------------

class TestCreateDomain:
    def test_returns_201_on_success(self, client, mock_service):
        response = client.post(
            "/domains/",
            json={"website_url": "https://www.example.com/about"},
        )
        assert response.status_code == 201

    def test_response_contains_expected_fields(self, client, mock_service):
        response = client.post(
            "/domains/",
            json={"website_url": "https://www.example.com/about"},
        )
        data = response.get_json()
        assert data["address"] == "example.com"
        assert data["key"] == "EXAMPLE_COM"
        assert data["id"] == 1
        assert data["parent_id"] is None

    def test_service_receives_correct_arguments(self, client, mock_service):
        client.post(
            "/domains/",
            json={
                "website_url": "https://example.com",
                "key": "MY_KEY",
                "parent_id": 5,
            },
        )
        mock_service.add_domain.assert_called_once_with(
            website_url="https://example.com",
            key="MY_KEY",
            parent_id=5,
        )

    def test_optional_fields_default_to_none(self, client, mock_service):
        client.post("/domains/", json={"website_url": "https://example.com"})
        _, kwargs = mock_service.add_domain.call_args
        assert kwargs.get("key") is None
        assert kwargs.get("parent_id") is None


# ---------------------------------------------------------------------------
# POST /domains/ – validation errors (handled by marshmallow schema, no DB)
# ---------------------------------------------------------------------------

class TestCreateDomainValidation:
    def test_missing_website_url_returns_422(self, client, mock_service):
        response = client.post("/domains/", json={})
        assert response.status_code == 422

    def test_blank_website_url_returns_422(self, client, mock_service):
        response = client.post("/domains/", json={"website_url": "  "})
        assert response.status_code == 422

    def test_url_without_tld_returns_422(self, client, mock_service):
        response = client.post("/domains/", json={"website_url": "https://nodomain"})
        assert response.status_code == 422

    def test_invalid_key_characters_returns_422(self, client, mock_service):
        response = client.post(
            "/domains/",
            json={"website_url": "https://example.com", "key": "has spaces!"},
        )
        assert response.status_code == 422

    def test_no_json_body_returns_422(self, client, mock_service):
        response = client.post("/domains/", content_type="application/json", data="")
        assert response.status_code in (400, 422)


# ---------------------------------------------------------------------------
# POST /domains/ – service-layer errors
# ---------------------------------------------------------------------------

class TestCreateDomainServiceErrors:
    def test_duplicate_domain_returns_409(self, client, mock_service):
        mock_service.add_domain.side_effect = DomainAlreadyExistsError(
            "A domain for 'example.com' already exists."
        )
        response = client.post(
            "/domains/", json={"website_url": "https://example.com"}
        )
        assert response.status_code == 409

    def test_invalid_url_from_service_returns_422(self, client, mock_service):
        mock_service.add_domain.side_effect = InvalidWebsiteURLError("Bad URL.")
        response = client.post(
            "/domains/", json={"website_url": "example.com"}
        )
        assert response.status_code == 422

    def test_unknown_parent_returns_404(self, client, mock_service):
        mock_service.add_domain.side_effect = ParentDomainNotFoundError(
            "Parent domain with id=999 does not exist."
        )
        response = client.post(
            "/domains/",
            json={"website_url": "https://example.com", "parent_id": 999},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /domains/
# ---------------------------------------------------------------------------

class TestListDomains:
    def test_returns_200(self, client, mock_service):
        response = client.get("/domains/")
        assert response.status_code == 200

    def test_returns_list(self, client, mock_service):
        response = client.get("/domains/")
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["address"] == "example.com"

    def test_empty_list_when_no_domains(self, client, mock_service):
        mock_service.list_domains.return_value = []
        response = client.get("/domains/")
        assert response.get_json() == []


# ---------------------------------------------------------------------------
# GET /domains/<int:domain_id>
# ---------------------------------------------------------------------------

class TestGetDomain:
    def test_returns_200_when_found(self, client, mock_service):
        response = client.get("/domains/1")
        assert response.status_code == 200

    def test_response_matches_domain(self, client, mock_service):
        response = client.get("/domains/1")
        data = response.get_json()
        assert data["id"] == 1
        assert data["address"] == "example.com"

    def test_returns_404_when_not_found(self, client, mock_service):
        mock_service.get_domain.return_value = None
        response = client.get("/domains/999")
        assert response.status_code == 404
