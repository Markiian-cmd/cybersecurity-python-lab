"""Маршрути вимірювань часу реагування."""

from typing import Annotated

from fastapi import APIRouter, Body, Path, Query, Response

from labs.lab03 import repository
from labs.lab03.config import MAX_BULK_SIZE, MIN_VALUE
from labs.lab03.schemas import RecordCreate, RecordRead, RecordReplace, RecordStatus

# Групування маршрутів вимірювань під спільним префіксом.
router = APIRouter(prefix="/records", tags=["Вимірювання"])
# Спільна перевірка додатного ідентифікатора в адресі запиту.
RecordId = Annotated[int, Path(gt=0, description="Id вимірювання")]
# Описи очікуваних помилок для документації Swagger.
NOT_FOUND = {404: {"description": "Запис або потрібну категорію не знайдено"}}
CONFLICT = {409: {"description": "Код вимірювання вже існує"}}


# Отримання сторінки вимірювань із перевіреними параметрами фільтрації.
@router.get("", response_model=list[RecordRead], summary="Отримати вимірювання")
def list_records(
    # Необов'язкові фільтри категорії та стану опрацювання.
    category_id: Annotated[int | None, Query(gt=0, description="Категорія")] = None,
    status: Annotated[RecordStatus | None, Query(description="Стан перевірки")] = None,
    # Мінімальна тривалість повинна бути невід'ємним скінченним числом.
    min_value: Annotated[
        float | None,
        Query(
            ge=MIN_VALUE, allow_inf_nan=False, description="Мінімальний час у хвилинах"
        ),
    ] = None,
    # Пошуковий текст обмежений довжиною від одного до 120 символів.
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=120,
            description="Підрядок у назві з урахуванням регістру",
        ),
    ] = None,
    # Обмеження розміру сторінки та невід'ємного зміщення.
    limit: Annotated[int, Query(ge=1, le=100, description="Розмір сторінки")] = 20,
    offset: Annotated[int, Query(ge=0, description="Кількість пропущених записів")] = 0,
) -> list[dict]:
    """Фільтри поєднуються через AND, порядок - за id."""
    return repository.list_records(
        category_id=category_id,
        status=status,
        min_value=min_value,
        q=q,
        limit=limit,
        offset=offset,
    )


# Створення одного вимірювання після перевірки полів моделлю.
@router.post(
    "",
    response_model=RecordRead,
    status_code=201,
    summary="Створити вимірювання",
    responses=NOT_FOUND | CONFLICT,
)
def create_record(record: RecordCreate) -> dict:
    """Додати вимірювання наявної категорії."""
    # Перетворення моделі запиту на словник для SQL-параметрів.
    return repository.create_record(record.model_dump())


# Приймання JSON-масиву для атомарного додавання вимірювань.
@router.post(
    "/bulk",
    response_model=list[RecordRead],
    status_code=201,
    summary="Створити пакет вимірювань",
    responses=NOT_FOUND | CONFLICT,
)
def bulk_create_records(
    records: Annotated[
        list[RecordCreate],
        # Відхилення порожнього пакета або понад 100 елементів.
        Body(
            min_length=1, max_length=MAX_BULK_SIZE, description="Масив із 1-100 записів"
        ),
    ],
) -> list[dict]:
    """Pydantic перевіряє весь масив до виклику SQL."""
    return repository.bulk_create_records([record.model_dump() for record in records])


# Отримання одного вимірювання разом із назвою категорії.
@router.get(
    "/{record_id}",
    response_model=RecordRead,
    summary="Отримати вимірювання за id",
    responses=NOT_FOUND,
)
def get_record(record_id: RecordId) -> dict:
    """Отримати запис разом із назвою категорії."""
    return repository.get_record(record_id)


# Повна заміна п'яти полів без зміни id.
@router.put(
    "/{record_id}",
    response_model=RecordRead,
    summary="Повністю замінити вимірювання",
    responses=NOT_FOUND | CONFLICT,
)
def replace_record(record_id: RecordId, record: RecordReplace) -> dict:
    """Замінити всі п'ять полів; id не змінюється."""
    return repository.replace_record(record_id, record.model_dump())


# Видалення вимірювання або відповідь 404 за відсутності запису.
@router.delete(
    "/{record_id}",
    status_code=204,
    response_class=Response,
    summary="Видалити вимірювання",
    responses=NOT_FOUND,
)
def delete_record(record_id: RecordId) -> Response:
    """Видалити запис і повернути відповідь без тіла."""
    repository.delete_record(record_id)
    # Успішне видалення повертає 204 без тіла відповіді.
    return Response(status_code=204)
