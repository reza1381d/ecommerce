from pydantic import BaseModel, ConfigDict, Field


class AddressCreateRequest(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=100,
    )
    recipient_name: str = Field(
        min_length=1,
        max_length=100,
    )
    phone: str = Field(
        min_length=1,
        max_length=20,
    )
    province: str = Field(
        min_length=1,
        max_length=100,
    )
    city: str = Field(
        min_length=1,
        max_length=100,
    )
    address_line: str = Field(
        min_length=1,
        max_length=1000,
    )
    postal_code: str = Field(
        min_length=1,
        max_length=20,
    )


class AddressUpdateRequest(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    recipient_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    phone: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
    )
    province: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    city: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    address_line: str | None = Field(
        default=None,
        min_length=1,
        max_length=1000,
    )
    postal_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
    )


class AddressResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    user_id: int
    title: str
    recipient_name: str
    phone: str
    province: str
    city: str
    address_line: str
    postal_code: str
    is_default: bool