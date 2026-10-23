"""Моделі перевірки даних та відповідей API."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from labs.lab03.config import MAX_SQLITE_ID, MIN_VALUE

# Перелік дозволених станів опрацювання запису.
RecordStatus = Literal["new", "in_progress", "done"]


class ApiModel(BaseModel):
    """Обрізати крайні пробіли та заборонити зайві поля."""

    # Видалення крайніх пробілів і відхилення невідомих полів.
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class CategoryCreate(ApiModel):
    """Дані нової категорії."""

    # Обмеження довжини назви після обрізання пробілів.
    name: str = Field(min_length=2, max_length=40)


class CategoryRead(CategoryCreate):
    """Категорія разом з id."""

    # Повернення додатного цілого ідентифікатора створеної категорії.
    id: int = Field(gt=0, strict=True)


class RecordCreate(ApiModel):
    """Новий запис: час у хвилинах і стан перевірки."""

    # Перевірка довжин коду та назви вимірювання.
    code: str = Field(min_length=3, max_length=40)
    title: str = Field(min_length=3, max_length=120)
    # Дозволений лише додатний цілий ідентифікатор категорії.
    category_id: int = Field(gt=0, strict=True)
    # Тривалість невід'ємна; текст, нескінченність і NaN заборонені.
    value: float = Field(ge=MIN_VALUE, allow_inf_nan=False, strict=True)
    status: RecordStatus


class RecordReplace(RecordCreate):
    """У PUT обов'язкові всі п'ять змінюваних полів."""

    # Успадкування обов'язкових полів без приймання id від клієнта.


class RecordRead(RecordCreate):
    """Відповідь із назвою категорії, отриманою через JOIN."""

    # Доповнення відповіді ідентифікатором і назвою категорії.
    id: int
    category_name: str


class SeedCategory(CategoryRead):
    """Початковий id повинен поміщатися в SQLite."""

    # Перевірка початкових ідентифікаторів категорій із JSON.
    id: int = Field(gt=0, le=MAX_SQLITE_ID, strict=True)


class SeedRecord(RecordCreate):
    """Перевірки запису для початкового JSON."""

    # Перевірка діапазону посилання на категорію перед заповненням.
    category_id: int = Field(gt=0, le=MAX_SQLITE_ID, strict=True)


class SeedData(ApiModel):
    """Початковий набір: три категорії та вісім записів."""

    # Початковий JSON повинен містити рівно три категорії.
    categories: list[SeedCategory] = Field(min_length=3, max_length=3)
    # Початковий JSON повинен містити рівно вісім вимірювань.
    records: list[SeedRecord] = Field(min_length=8, max_length=8)
