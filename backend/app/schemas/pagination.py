"""Generic pagination schema."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):  # noqa: UP046
    """A paginated slice of results."""

    items: list[T]
    total: int
    limit: int
    offset: int
