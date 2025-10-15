from typing import Generic, Optional, TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")


class ErrorResponse(BaseModel):
    """Standard error response shape."""

    error_code: str
    message: str
    details: Optional[dict] = None


class SuccessResponse(GenericModel, Generic[T]):
    """Standard success response shape with a generic data field."""

    status: str
    data: T
