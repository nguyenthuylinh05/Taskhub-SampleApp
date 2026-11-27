"""Base Pydantic schemas."""

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator


class BaseSchema(BaseModel):
    """Base schema with common validation rules."""

    model_config = ConfigDict(from_attributes=True)

    @field_validator("*", mode="before")
    @classmethod
    def strip_and_validate_strings(
        cls,
        value: object,
        info: ValidationInfo,
    ) -> object:
        """Strip ordinary text fields while preserving passwords."""
        if not isinstance(value, str):
            return value

        if info.field_name in {
            "password",
            "current_password",
            "new_password",
        }:
            return value

        value = value.strip()

        if not value:
            raise ValueError("String must not be empty or whitespace only.")

        return value
