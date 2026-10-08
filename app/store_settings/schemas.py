from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


CurrencyUnit = Literal["toman", "rial"]

Palette = Literal[
    "blue", "emerald", "violet", "amber", "rose", "teal", "cyan",
    "indigo", "fuchsia", "lime", "orange",
]


class StoreSettingsUpdate(BaseModel):
    store_name: str = Field(min_length=1, max_length=60)
    palette: Palette
    currency_unit: CurrencyUnit = "toman"
    home_hero_badge: str = Field(min_length=1, max_length=80)
    home_hero_title: str = Field(min_length=1, max_length=160)
    home_hero_description: str = Field(min_length=1, max_length=500)
    home_hero_button_label: str = Field(min_length=1, max_length=50)

    @field_validator(
        "store_name",
        "home_hero_badge",
        "home_hero_title",
        "home_hero_description",
        "home_hero_button_label",
    )
    @classmethod
    def normalize_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("این مقدار نمی‌تواند خالی باشد.")
        return value


class StoreSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    store_name: str
    palette: Palette
    currency_unit: CurrencyUnit
    home_hero_badge: str
    home_hero_title: str
    home_hero_description: str
    home_hero_button_label: str
    updated_at: datetime
