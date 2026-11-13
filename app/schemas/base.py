from pydantic import BaseModel, ConfigDict, field_validator


class BaseSchema(BaseModel):
    """Base schema with common validation rules."""

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("*", mode="before")
    @classmethod
    def reject_whitespace_only_strings(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            raise ValueError("String must not be empty or whitespace only.")
        return value
