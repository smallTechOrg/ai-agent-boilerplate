"""
Data Access Layer for the Domains resource.

All SQL lives here.  Nothing outside this module touches the database directly.
The class accepts a connection as a constructor argument, which makes it trivial
to swap in a test double without patching globals.
"""
from __future__ import annotations

from typing import Optional

import psycopg


class DomainRepository:
    """CRUD operations for the ``domains`` table."""

    # Column order returned by every SELECT / RETURNING clause.
    _COLUMNS = ("id", "key", "address", "parent_id", "created_at")

    def __init__(self, connection: psycopg.Connection) -> None:
        self._conn = connection

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def find_by_address(self, address: str) -> Optional[dict]:
        """Return the domain record matching *address*, or ``None``."""
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT id, key, address, parent, created_at "
                "FROM domains WHERE address = %s;",
                (address,),
            )
            row = cur.fetchone()
        return self._to_dict(row) if row else None

    def find_by_id(self, domain_id: int) -> Optional[dict]:
        """Return the domain record with the given primary key, or ``None``."""
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT id, key, address, parent, created_at "
                "FROM domains WHERE id = %s;",
                (domain_id,),
            )
            row = cur.fetchone()
        return self._to_dict(row) if row else None

    def list_all(self) -> list[dict]:
        """Return all domain records ordered by creation time."""
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT id, key, address, parent, created_at "
                "FROM domains ORDER BY created_at ASC;"
            )
            rows = cur.fetchall()
        return [self._to_dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def create(
        self,
        key: str,
        address: str,
        parent_id: Optional[int] = None,
    ) -> dict:
        """
        Insert a new domain row and return the persisted record.

        Raises ``psycopg.errors.UniqueViolation`` if *address* already exists
        (the caller is responsible for handling or re-raising this).
        """
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO domains (key, address, parent) "
                    "VALUES (%s, %s, %s) "
                    "RETURNING id, key, address, parent, created_at;",
                    (key, address, parent_id),
                )
                row = cur.fetchone()
            self._conn.commit()
            return self._to_dict(row)
        except Exception:
            self._conn.rollback()
            raise

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_dict(row: tuple) -> dict:
        """Map a DB row tuple to a plain dict using canonical field names."""
        id_, key, address, parent, created_at = row
        return {
            "id": id_,
            "key": key,
            "address": address,
            "parent_id": parent,    # alias: DB column is "parent"
            "created_at": created_at,
        }
