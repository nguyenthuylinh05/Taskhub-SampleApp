from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common validation configuration."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )
