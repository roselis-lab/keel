"""Typed failures, raised by the services and translated once at each edge.

Every service used to return `{"success": False, "error": "..."}` and every caller had to
work out what kind of failure it was by reading the sentence — the REST layer literally
branched on `if "already has" in result["error"]`. Rewording a message silently changed
an HTTP status code, and each new caller re-derived the same mapping.

So failures are exceptions with a kind, the way an ORM raises `DoesNotExist` rather than
returning a string. The kind carries the status code and the machine-readable `code`;
the adapters (`keel.main` for HTTP, `keel.mcp.registry` for tools) translate once, and
routes and tools contain no error branches at all.

`hint` is the part that matters for an agent: an error that only rejects makes the caller
guess again, while one that names the allowed values ends the loop in a single turn.
"""
from __future__ import annotations

from typing import Any


class KeelError(Exception):
    """Base for anything a caller did wrong. Never used directly."""

    status: int = 400
    code: str = "error"

    def __init__(
        self,
        message: str,
        *,
        entity_type: str | None = None,
        entity_id: str | None = None,
        field: str | None = None,
        hint: str | None = None,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.field = field
        self.hint = hint
        self.details = details or []

    def as_dict(self) -> dict[str, Any]:
        """The payload a tool returns. Empty keys are dropped so a simple failure stays
        a short answer."""
        out: dict[str, Any] = {"success": False, "code": self.code, "error": self.message}
        for key, value in (
            ("entity_type", self.entity_type),
            ("entity_id", self.entity_id),
            ("field", self.field),
            ("hint", self.hint),
            ("details", self.details),
        ):
            if value:
                out[key] = value
        return out


class NotFound(KeelError):
    """The entity does not exist."""

    status = 404
    code = "not_found"


class Conflict(KeelError):
    """It already exists, or the state does not allow this."""

    status = 409
    code = "conflict"


class Invalid(KeelError):
    """The payload itself is wrong: a bad value, a bad shape, a missing required field.

    `details` carries one entry per problem as `{field, message}`, because a caller
    fixing three fields should not need three round trips to find them.
    """

    status = 422
    code = "invalid"


class IntegrityError(KeelError):
    """The payload is fine on its own but wrong against the rest of the catalog: a link
    to something that is not there, a prerequisite cycle, a coverage claim naming a
    deleted entry.

    This is the class of error a single record cannot catch about itself, which is
    exactly why it lives at the service layer rather than in the schema.
    """

    status = 409
    code = "integrity"


class Forbidden(KeelError):
    """The path is not one this door opens."""

    status = 400
    code = "forbidden"


def invalid_from_pydantic(exc: Exception, *, hint: str | None = None) -> Invalid:
    """Turn a pydantic ValidationError into one `Invalid` listing every bad field.

    Pydantic already knows precisely what is wrong and where; flattening that to a single
    sentence throws away the field paths the caller needs to act."""
    details: list[dict[str, Any]] = []
    for err in getattr(exc, "errors", lambda: [])():
        loc = ".".join(str(x) for x in err.get("loc", ()) if x != "__root__")
        details.append({"field": loc or None, "message": err.get("msg", "")})
    if not details:
        details = [{"field": None, "message": str(exc)}]
    summary = details[0]["message"] if len(details) == 1 else f"{len(details)} fields are invalid"
    if len(details) == 1 and details[0]["field"]:
        summary = f"{details[0]['field']}: {summary}"
    return Invalid(summary, field=details[0]["field"], hint=hint, details=details)
