"""
HTTP Controller for the Domains resource.

Uses flask-smorest Blueprint which provides:
  - Automatic OpenAPI 3 documentation (served at /api/docs).
  - Request body validation via marshmallow schemas.
  - Response serialisation via marshmallow schemas.
  - Typed abort helpers that map to documented HTTP error responses.

Responsibilities of this layer
-------------------------------
  ✓ Parse and validate HTTP input (delegated to @bp.arguments schema).
  ✓ Call the service layer with clean Python values.
  ✓ Map service-layer exceptions to appropriate HTTP status codes.
  ✗ No SQL.
  ✗ No business rules.
"""
from http import HTTPStatus

from flask_smorest import Blueprint, abort

from db import sync_connection
from domains import (
    DomainAlreadyExistsError,
    DomainRepository,
    DomainService,
    InvalidWebsiteURLError,
    ParentDomainNotFoundError,
)
from domains.schemas import CreateDomainRequest, DomainResponse

domains_bp = Blueprint(
    "domains",
    __name__,
    url_prefix="/domains",
    description=(
        "Manage registered domains. "
        "A domain record authorises the chat agent to serve visitors from that hostname."
    ),
)


# ---------------------------------------------------------------------------
# Dependency factory
# ---------------------------------------------------------------------------

def _get_domain_service() -> DomainService:
    """
    Construct a fully-wired ``DomainService`` using the shared DB connection.

    Extracted into a named function so tests can patch it with
    ``unittest.mock.patch("api.domains._get_domain_service")``.
    """
    return DomainService(DomainRepository(sync_connection))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@domains_bp.post("/")
@domains_bp.arguments(CreateDomainRequest, location="json")
@domains_bp.response(HTTPStatus.CREATED, DomainResponse)
@domains_bp.alt_response(HTTPStatus.CONFLICT, description="A domain with that address already exists.")
@domains_bp.alt_response(HTTPStatus.UNPROCESSABLE_ENTITY, description="The website URL cannot be parsed into a valid hostname.")
@domains_bp.alt_response(HTTPStatus.NOT_FOUND, description="The specified parent_id does not exist.")
def create_domain(body: dict):
    """
    Register a new domain.

    Accepts a website address, extracts the canonical hostname (stripping
    scheme, path, query-string and a leading ``www.``), auto-generates a domain
    key unless one is explicitly supplied, and persists the record.
    """
    service = _get_domain_service()
    try:
        domain = service.add_domain(
            website_url=body["website_url"],
            key=body.get("key"),
            parent_id=body.get("parent_id"),
        )
        return domain
    except DomainAlreadyExistsError as exc:
        abort(HTTPStatus.CONFLICT, message=str(exc))
    except InvalidWebsiteURLError as exc:
        abort(HTTPStatus.UNPROCESSABLE_ENTITY, message=str(exc))
    except ParentDomainNotFoundError as exc:
        abort(HTTPStatus.NOT_FOUND, message=str(exc))


@domains_bp.get("/")
@domains_bp.response(HTTPStatus.OK, DomainResponse(many=True))
def list_domains():
    """
    List all registered domains.

    Returns an array of domain records ordered by creation time (oldest first).
    """
    return _get_domain_service().list_domains()


@domains_bp.get("/<int:domain_id>")
@domains_bp.response(HTTPStatus.OK, DomainResponse)
@domains_bp.alt_response(HTTPStatus.NOT_FOUND, description="Domain not found.")
def get_domain(domain_id: int):
    """
    Retrieve a single domain by its ID.
    """
    domain = _get_domain_service().get_domain(domain_id)
    if domain is None:
        abort(HTTPStatus.NOT_FOUND, message=f"Domain with id={domain_id} not found.")
    return domain
