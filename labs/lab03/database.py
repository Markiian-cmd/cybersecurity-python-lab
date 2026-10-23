"""Створення SQLite-бази за готовою схемою лабораторної роботи."""

import sqlite3
from contextlib import closing
from pathlib import Path

# Визначення шляхів незалежно від поточної робочої директорії.
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "data" / "lab3.sqlite3"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def get_connection() -> sqlite3.Connection:
    """Відкрити з'єднання з перевіркою зовнішніх ключів."""
    # Створення папки даних і відкриття файлу бази.
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    # Доступ до полів результату за назвами стовпців.
    connection.row_factory = sqlite3.Row
    try:
        # Увімкнення перевірки зв'язків для кожного нового з'єднання.
        connection.execute("PRAGMA foreign_keys = ON")
        return connection
    except sqlite3.Error:
        # Закриття з'єднання, якщо його налаштування завершилося помилкою.
        connection.close()
        raise


def initialize_database() -> None:
    """Створити таблиці за готовим SQL-скриптом."""
    # Читання готової схеми таблиць із файлу.
    script = SCHEMA_PATH.read_text(encoding="utf-8")
    # Автоматичне закриття з'єднання після виконання скрипту.
    with closing(get_connection()) as connection:
        try:
            connection.executescript(script)
        except sqlite3.Error:
            # Скасування незавершених змін при помилці SQL.
            connection.rollback()
            raise


# Ініціалізація бази при окремому запуску цього модуля.
if __name__ == "__main__":
    initialize_database()
