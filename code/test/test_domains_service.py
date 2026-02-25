"""
Unit tests for the Domains service layer.

These tests have ZERO external dependencies:
  - No database connection required.
  - No Flask app started.
  - No network calls.

The ``DomainRepository`` is replaced by a ``MagicMock`` so every test is fast
and deterministic.
"""
import sys
import os
import pytest
from unittest.mock import MagicMock

# Ensure the project root is on the path when running pytest from outside /code.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from domains.service import (
    DomainService,
    DomainAlreadyExistsError,
    InvalidWebsiteURLError,
    ParentDomainNotFoundError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_repo():
    """A MagicMock that satisfies the DomainRepository interface."""
    repo = MagicMock()
    repo.find_by_address.return_value = None   # no duplicate by default
    repo.find_by_id.return_value = None        # no parent by default
    repo.create.return_value = {
        "id": 1,
        "key": "EXAMPLE_COM",
        "address": "example.com",
        "parent_id": None,
        "created_at": "2024-01-01T00:00:00+00:00",
    }
    return repo


@pytest.fixture
def service(mock_repo):
    return DomainService(mock_repo)


# ---------------------------------------------------------------------------
# DomainService.extract_address
# ---------------------------------------------------------------------------

class TestExtractAddress:
    def test_full_https_url_strips_scheme_path_and_www(self):
        assert DomainService.extract_address("https://www.example.com/about?q=1") == "example.com"

    def test_http_scheme(self):
        assert DomainService.extract_address("http://example.com") == "example.com"

    def test_bare_hostname_no_scheme(self):
        assert DomainService.extract_address("example.com") == "example.com"

    def test_bare_hostname_with_path_no_scheme(self):
        assert DomainService.extract_address("www.example.com/page") == "example.com"

    def test_subdomain_other_than_www_is_preserved(self):
        assert DomainService.extract_address("https://api.example.com") == "api.example.com"

    def test_multi_part_tld(self):
        assert DomainService.extract_address("https://www.example.co.uk") == "example.co.uk"

    def test_uppercase_url_is_lowercased(self):
        assert DomainService.extract_address("HTTPS://WWW.EXAMPLE.COM") == "example.com"

    def test_url_with_port_strips_port(self):
        assert DomainService.extract_address("http://example.com:8080/path") == "example.com"

    def test_invalid_url_with_no_tld_raises(self):
        with pytest.raises(InvalidWebsiteURLError):
            DomainService.extract_address("https://localhost")

    def test_blank_string_raises(self):
        with pytest.raises(InvalidWebsiteURLError):
            DomainService.extract_address("   ")


# ---------------------------------------------------------------------------
# DomainService.generate_key
# ---------------------------------------------------------------------------

class TestGenerateKey:
    def test_simple_dotcom(self):
        assert DomainService.generate_key("example.com") == "EXAMPLE_COM"

    def test_multi_part_tld(self):
        assert DomainService.generate_key("example.co.uk") == "EXAMPLE_CO_UK"

    def test_subdomain(self):
        assert DomainService.generate_key("api.example.com") == "API_EXAMPLE_COM"

    def test_hyphens_become_underscores(self):
        assert DomainService.generate_key("my-company.com") == "MY_COMPANY_COM"

    def test_no_leading_or_trailing_underscores(self):
        key = DomainService.generate_key("example.com")
        assert not key.startswith("_")
        assert not key.endswith("_")

    def test_consecutive_special_chars_collapsed(self):
        # e.g. "a..b" → "A__B" collapsed → "A_B"
        assert DomainService.generate_key("a..b.com") == "A_B_COM"


# ---------------------------------------------------------------------------
# DomainService.add_domain – success paths
# ---------------------------------------------------------------------------

class TestAddDomain:
    def test_success_returns_repository_record(self, service, mock_repo):
        result = service.add_domain("https://example.com")
        assert result["address"] == "example.com"
        assert result["key"] == "EXAMPLE_COM"

    def test_key_is_auto_generated_when_omitted(self, service, mock_repo):
        service.add_domain("https://example.com")
        _, kwargs = mock_repo.create.call_args_list[0]
        assert kwargs["key"] == "EXAMPLE_COM"

    def test_explicit_key_is_normalised_to_uppercase(self, service, mock_repo):
        service.add_domain("https://example.com", key="acme_corp")
        _, kwargs = mock_repo.create.call_args_list[0]
        assert kwargs["key"] == "ACME_CORP"

    def test_parent_id_is_passed_to_repository(self, service, mock_repo):
        mock_repo.find_by_id.return_value = {"id": 5}  # parent exists
        service.add_domain("https://example.com", parent_id=5)
        _, kwargs = mock_repo.create.call_args
        assert kwargs["parent_id"] == 5

    def test_repository_create_called_with_extracted_address(self, service, mock_repo):
        service.add_domain("https://www.example.com/page")
        _, kwargs = mock_repo.create.call_args_list[0]
        assert kwargs["address"] == "example.com"


# ---------------------------------------------------------------------------
# DomainService.add_domain – error paths
# ---------------------------------------------------------------------------

class TestAddDomainErrors:
    def test_duplicate_address_raises_domain_already_exists(self, service, mock_repo):
        mock_repo.find_by_address.return_value = {"id": 99}  # already exists
        with pytest.raises(DomainAlreadyExistsError):
            service.add_domain("https://example.com")

    def test_invalid_url_raises_invalid_website_url_error(self, service):
        with pytest.raises(InvalidWebsiteURLError):
            service.add_domain("not-a-domain")

    def test_missing_parent_raises_parent_domain_not_found(self, service, mock_repo):
        mock_repo.find_by_id.return_value = None  # parent not found
        with pytest.raises(ParentDomainNotFoundError):
            service.add_domain("https://example.com", parent_id=999)

    def test_repository_not_called_when_duplicate_detected(self, service, mock_repo):
        mock_repo.find_by_address.return_value = {"id": 1}
        with pytest.raises(DomainAlreadyExistsError):
            service.add_domain("https://example.com")
        mock_repo.create.assert_not_called()
