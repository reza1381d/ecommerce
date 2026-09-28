from pydantic import BaseModel, ConfigDict, EmailStr


class UserUpdateRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    email: EmailStr
    first_name: str
    last_name: str
    phone: str | None = None