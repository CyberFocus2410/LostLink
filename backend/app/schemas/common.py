"""
Common API response schemas conforming to LostLink specification:
{
  "data": ...,
  "error": null | { "code": "...", "message": "...", "fields": { ... } },
  "meta": { ... }
}
"""
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class APIError(BaseModel):
    code: str
    message: str
    fields: Optional[dict[str, str]] = None


class APIMeta(BaseModel):
    page: Optional[int] = None
    limit: Optional[int] = None
    total: Optional[int] = None
    extra: Optional[dict[str, Any]] = None


class APIResponse(BaseModel, Generic[T]):
    data: Optional[T] = None
    error: Optional[APIError] = None
    meta: Optional[APIMeta] = None

    @classmethod
    def success(cls, data: T, meta: Optional[APIMeta] = None) -> "APIResponse[T]":
        return cls(data=data, error=None, meta=meta)

    @classmethod
    def fail(cls, code: str, message: str, fields: Optional[dict[str, str]] = None) -> "APIResponse[None]":
        return cls(
            data=None,
            error=APIError(code=code, message=message, fields=fields),
            meta=None,
        )
