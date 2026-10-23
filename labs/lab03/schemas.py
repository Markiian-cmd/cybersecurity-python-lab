"""Моделі перевірки даних та відповідей API."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from labs.lab03.config import MAX_SQLITE_ID, MIN_VALUE

RecordStatus = Literal["new", "in_progress", "done"]


class ApiModel(BaseModel):
    """Обрізати крайні пробіли та заборонити зайві поля."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class CategoryCreate(ApiModel):
    """Дані нової категорії."""

    name: str = Field(min_length=2, max_length=40)


class CategoryRead(CategoryCreate):
    """Категорія разом з id."""

    id: int = Field(gt=0, strict=True)


class RecordCreate(ApiModel):
    """Новий запис: час у хвилинах і стан перевірки."""

    code: str = Field(min_length=3, max_length=40)
    title: str = Field(min_length=3, max_length=120)
    category_id: int = Field(gt=0, strict=True)
    value: float = Field(ge=MIN_VALUE, allow_inf_nan=False, strict=True)
    status: RecordStatus


class RecordReplace(RecordCreate):
    """У PUT обов'язкові всі п'ять змінюваних полів."""


class RecordRead(RecordCreate):
    """Відповідь із назвою категорії, отриманою через JOIN."""

    id: int
    category_name: str


class SeedCategory(CategoryRead):
    """Початковий id повинен поміщатися в SQLite."""

    id: int = Field(gt=0, le=MAX_SQLITE_ID, strict=True)


class SeedRecord(RecordCreate):
    """Перевірки запису для початкового JSON."""

    category_id: int = Field(gt=0, le=MAX_SQLITE_ID, strict=True)


class SeedData(ApiModel):
    """Початковий набір: три категорії та вісім записів."""

    categories: list[SeedCategory] = Field(min_length=3, max_length=3)
    records: list[SeedRecord] = Field(min_length=8, max_length=8)
