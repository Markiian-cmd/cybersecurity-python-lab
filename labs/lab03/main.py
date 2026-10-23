"""FastAPI для обліку часу реагування на інциденти, варіант 7."""

import logging
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from labs.lab03.config import THRESHOLD, UNIT
from labs.lab03.database import initialize_database
from labs.lab03.routers import categories, records
from shared import student


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Створити відсутні таблиці один раз під час запуску."""
    initialize_database()
    yield


app = FastAPI(
    title="Облік часу реагування на інциденти",
    description=(
        "Варіант 7. Категорії: account, network, endpoint. "
        f"value - невід'ємний час у хвилинах ({UNIT}). "
        f"Поріг {THRESHOLD} хв не є верхньою межею. status - стан перевірки запису."
    ),
    lifespan=lifespan,
)
app.include_router(categories.router)
app.include_router(records.router)


@app.exception_handler(LookupError)
async def not_found(_request: Request, error: LookupError) -> JSONResponse:
    """Перетворити відсутній ресурс на 404."""
    return JSONResponse(status_code=404, content={"detail": str(error)})


@app.exception_handler(sqlite3.IntegrityError)
async def conflict(_request: Request, _error: sqlite3.IntegrityError) -> JSONResponse:
    """Унікальність або заборона видалення непорожньої категорії."""
    return JSONResponse(
        status_code=409,
        content={
            "detail": "Код або назва категорії вже існує, або категорія містить записи."
        },
    )


@app.exception_handler(sqlite3.Error)
async def database_error(_request: Request, error: sqlite3.Error) -> JSONResponse:
    """Записати технічні деталі в журнал, клієнту повернути загальну помилку."""
    logging.getLogger(__name__).error("Помилка SQLite", exc_info=error)
    return JSONResponse(
        status_code=500,
        content={"detail": "Не вдалося виконати операцію з базою даних."},
    )


@app.exception_handler(RequestValidationError)
async def invalid_data(
    _request: Request, error: RequestValidationError
) -> JSONResponse:
    """Повернути 422 без несеріалізованих NaN та Infinity у тілі помилки."""
    details = [
        {"loc": item["loc"], "msg": item["msg"], "type": item["type"]}
        for item in error.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": details})


@app.get("/ping", tags=["Сервіс"], summary="Перевірити доступність API")
def ping() -> dict[str, str]:
    """Перевірка доступності."""
    return {"status": "ok"}


@app.get("/student", tags=["Сервіс"], summary="Отримати дані студента")
def get_student() -> dict[str, str | int]:
    """Дані з shared/student.py."""
    return {
        "student_name": student.STUDENT_NAME,
        "group_name": student.GROUP_NAME,
        "variant_number": student.VARIANT_NUMBER,
    }
