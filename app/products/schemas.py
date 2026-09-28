from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, computed_field


class ProductCreateRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=200,
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
    )
    price: Decimal = Field(
        ge=0,
        decimal_places=2,
        max_digits=12,
    )
    stock: int = Field(
        default=0,
        ge=0,
    )
    category_id: int | None = Field(
        default=None,
        gt=0,
    )


class ProductUpdateRequest(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
    )
    price: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
        max_digits=12,
    )
    stock: int | None = Field(
        default=None,
        ge=0,
    )
    category_id: int | None = Field(
        default=None,
        gt=0,
    )
    is_active: bool | None = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    name: str
    description: str | None
    price: Decimal
    stock: int
    reserved_stock: int
    category_id: int | None
    is_active: bool

    @computed_field
    @property
    def available_stock(self) -> int:
        return self.stock - self.reserved_stock


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    page: int
    limit: int
    total: int