"""Маршрути категорій інцидентів."""

from typing import Annotated

from fastapi import APIRouter, Path, Response

from labs.lab03 import repository
from labs.lab03.schemas import CategoryCreate, CategoryRead

# Групування маршрутів категорій під спільним префіксом.
router = APIRouter(prefix="/categories", tags=["Категорії"])


# Отримання списку категорій із перевіркою моделі відповіді.
@router.get("", response_model=list[CategoryRead], summary="Отримати категорії")
def list_categories() -> list[dict]:
    """Категорії за зростанням id."""
    return repository.list_categories()


# Створення категорії з відповіддю 201 або конфліктом 409.
@router.post(
    "",
    response_model=CategoryRead,
    status_code=201,
    summary="Створити категорію",
    responses={409: {"description": "Назва категорії вже існує"}},
)
def create_category(category: CategoryCreate) -> dict:
    """Створити категорію; id визначає SQLite."""
    return repository.create_category(category.name)


# Видалення порожньої категорії за додатним ідентифікатором.
@router.delete(
    "/{category_id}",
    status_code=204,
    response_class=Response,
    summary="Видалити порожню категорію",
    responses={
        404: {"description": "Категорію не знайдено"},
        409: {"description": "Категорія містить записи"},
    },
)
def delete_category(
    category_id: Annotated[int, Path(gt=0, description="Id категорії")],
) -> Response:
    """Непорожню категорію захищає зовнішній ключ."""
    repository.delete_category(category_id)
    # Успішне видалення повертає 204 без тіла відповіді.
    return Response(status_code=204)
