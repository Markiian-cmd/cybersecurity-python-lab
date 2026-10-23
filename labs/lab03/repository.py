"""SQL-операції. Вхідні дані перевіряють моделі schemas.py."""

import sqlite3
from contextlib import closing

from labs.lab03.config import MAX_SQLITE_ID
from labs.lab03.database import get_connection

RECORD_SELECT = """
    SELECT records.id, records.code, records.title, records.category_id,
           records.value, records.status, categories.name AS category_name
    FROM records JOIN categories ON categories.id = records.category_id
"""
RECORD_INSERT = """
    INSERT INTO records (code, title, category_id, value, status)
    VALUES (:code, :title, :category_id, :value, :status)
"""


def _require_category(connection: sqlite3.Connection, category_id: int) -> None:
    if (
        category_id > MAX_SQLITE_ID
        or connection.execute(
            "SELECT id FROM categories WHERE id = ?", (category_id,)
        ).fetchone()
        is None
    ):
        raise LookupError("Категорію не знайдено.")


def _read_record(connection: sqlite3.Connection, record_id: int) -> dict:
    if record_id > MAX_SQLITE_ID:
        raise LookupError("Запис не знайдено.")
    row = connection.execute(
        RECORD_SELECT + " WHERE records.id = ?", (record_id,)
    ).fetchone()
    if row is None:
        raise LookupError("Запис не знайдено.")
    return dict(row)


def _insert_record(connection: sqlite3.Connection, record: dict) -> dict:
    _require_category(connection, record["category_id"])
    cursor = connection.execute(RECORD_INSERT, record)
    return _read_record(connection, cursor.lastrowid)


def list_categories() -> list[dict]:
    """Отримати категорії за зростанням id."""
    with closing(get_connection()) as connection:
        return [
            dict(row)
            for row in connection.execute("SELECT id, name FROM categories ORDER BY id")
        ]


def create_category(name: str) -> dict:
    """Створити категорію з автоматичним id."""
    with closing(get_connection()) as connection, connection:
        cursor = connection.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        return {"id": cursor.lastrowid, "name": name}


def delete_category(category_id: int) -> None:
    """Видалити категорію; зовнішній ключ захищає непорожню."""
    if category_id > MAX_SQLITE_ID:
        raise LookupError("Категорію не знайдено.")
    with closing(get_connection()) as connection, connection:
        cursor = connection.execute(
            "DELETE FROM categories WHERE id = ?", (category_id,)
        )
        if cursor.rowcount == 0:
            raise LookupError("Категорію не знайдено.")


def get_record(record_id: int) -> dict:
    """Отримати запис і назву його категорії."""
    with closing(get_connection()) as connection:
        return _read_record(connection, record_id)


def create_record(record: dict) -> dict:
    """Додати одне вимірювання."""
    with closing(get_connection()) as connection, connection:
        return _insert_record(connection, record)


def list_records(
    *,
    category_id: int | None = None,
    status: str | None = None,
    min_value: float | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    """Поєднати перевірені API фільтри через AND і повернути сторінку."""
    if (
        category_id is not None and category_id > MAX_SQLITE_ID
    ) or offset > MAX_SQLITE_ID:
        return []
    conditions, parameters = [], []
    for condition, value in (
        ("records.category_id = ?", category_id),
        ("records.status = ?", status),
        ("records.value >= ?", min_value),
        ("instr(records.title, ?) > 0", q),
    ):
        if value is not None:
            conditions.append(condition)
            parameters.append(value)
    query = RECORD_SELECT
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY records.id LIMIT ? OFFSET ?"
    parameters.extend((limit, offset))
    with closing(get_connection()) as connection:
        return [dict(row) for row in connection.execute(query, parameters)]


def replace_record(record_id: int, record: dict) -> dict:
    """Замінити всі змінювані поля, зберігши id."""
    with closing(get_connection()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        _read_record(connection, record_id)
        _require_category(connection, record["category_id"])
        connection.execute(
            """UPDATE records
               SET code=:code, title=:title, category_id=:category_id,
                   value=:value, status=:status
               WHERE id=:id""",
            {**record, "id": record_id},
        )
        return _read_record(connection, record_id)


def delete_record(record_id: int) -> None:
    """Видалити запис або повідомити про відсутній id."""
    if record_id > MAX_SQLITE_ID:
        raise LookupError("Запис не знайдено.")
    with closing(get_connection()) as connection, connection:
        cursor = connection.execute("DELETE FROM records WHERE id = ?", (record_id,))
        if cursor.rowcount == 0:
            raise LookupError("Запис не знайдено.")


def bulk_create_records(records: list[dict]) -> list[dict]:
    """Вставити весь пакет однією транзакцією; помилка скасовує всі зміни."""
    with closing(get_connection()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        return [_insert_record(connection, record) for record in records]


def populate_empty_database(categories: list[dict], records: list[dict]) -> bool:
    """Заповнити порожню базу; повернути False, якщо дані вже є."""
    with closing(get_connection()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        occupied = connection.execute(
            "SELECT EXISTS(SELECT 1 FROM categories) OR EXISTS(SELECT 1 FROM records)"
        ).fetchone()[0]
        if occupied:
            return False
        connection.executemany(
            "INSERT INTO categories (id, name) VALUES (:id, :name)", categories
        )
        for record in records:
            _insert_record(connection, record)
        return True
