"""
Marshmallow schemas for the Domains resource.

These schemas serve three purposes simultaneously:
  1. Input validation  – marshmallow enforces types, required fields, and custom rules.
  2. Output serialisation – flask-smorest calls Schema.dump() on every response.
  3. OpenAPI documentation – flask-smorest reflects the schema into the generated spec.
"""
import re
from marshmallow import Schema, fields, validates, ValidationError


class CreateDomainRequest(Schema):
    """Request body for POST /domains/."""

    website_url = fields.Str(
        required=True,
        metadata={
            "description": (
                "Full or partial website address to register. "
                "The canonical hostname is extracted automatically – scheme, path, "
                "query-string and a leading 'www.' are all stripped."
            ),
            "example": "https://www.example.com/about",
        },
    )
    key = fields.Str(
        load_default=None,
        allow_none=True,
        metadata={
            "description": (
                "Optional human-readable domain key (uppercase letters, digits and "
                "underscores only, e.g. ACME_CORP). "
                "Auto-generated from the extracted hostname when omitted."
            ),
            "example": "ACME_CORP",
        },
    )
    parent_id = fields.Int(
        load_default=None,
        allow_none=True,
        metadata={
            "description": "Optional ID of an existing parent domain for hierarchical grouping.",
            "example": 1,
        },
    )

    @validates("website_url")
    def validate_website_url(self, value: str) -> None:
        """Reject blank or obviously non-URL values early."""
        stripped = value.strip()
        if not stripped:
            raise ValidationError("website_url must not be blank.")
        # A naive guard – detailed parsing happens in the service layer.
        candidate = re.sub(r"^https?://", "", stripped, flags=re.IGNORECASE)
        host_part = candidate.split("/")[0].split("?")[0]
        if "." not in host_part:
            raise ValidationError(
                "website_url does not appear to contain a valid hostname."
            )

    @validates("key")
    def validate_key(self, value: str) -> None:
        if value is None:
            return
        if not re.match(r"^[A-Za-z0-9_]+$", value.strip()):
            raise ValidationError(
                "key may only contain letters, digits and underscores."
            )


class DomainResponse(Schema):
    """Serialisation schema for a Domain record."""

    id = fields.Int(
        dump_only=True,
        metadata={"description": "Auto-assigned primary key.", "example": 42},
    )
    key = fields.Str(
        dump_only=True,
        metadata={"description": "Domain key identifier.", "example": "EXAMPLE_COM"},
    )
    address = fields.Str(
        dump_only=True,
        metadata={
            "description": "Canonical hostname extracted from the submitted URL.",
            "example": "example.com",
        },
    )
    parent_id = fields.Int(
        dump_only=True,
        allow_none=True,
        metadata={"description": "ID of the parent domain; null for root domains.", "example": None},
    )
    created_at = fields.DateTime(
        dump_only=True,
        metadata={"description": "ISO-8601 timestamp of when the domain was created."},
    )
