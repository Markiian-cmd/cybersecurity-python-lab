"""Початкове заповнення бази навчальними даними варіанта 7."""

import logging
import sqlite3
from pathlib import Path

from pydantic import ValidationError

from labs.lab03.database import BASE_DIR, initialize_database
from labs.lab03.repository import populate_empty_database
from labs.lab03.schemas import SeedData

# Розташування навчальних даних для початкового заповнення бази.
SEED_PATH = BASE_DIR / "data" / "seed.json"


def load_seed_data(path: Path = SEED_PATH) -> tuple[list[dict], list[dict]]:
    """Прочитати й перевірити весь JSON до запису в базу."""
    # Перевірка всього JSON до будь-яких вставлень у базу.
    data = SeedData.model_validate_json(path.read_text(encoding="utf-8"))
    # Перетворення перевірених моделей на словники для SQL.
    return (
        [category.model_dump() for category in data.categories],
        [record.model_dump() for record in data.records],
    )


def seed_database(path: Path = SEED_PATH) -> bool:
    """Створити таблиці та заповнити порожню базу однією транзакцією."""
    categories, records = load_seed_data(path)
    # Створення відсутніх таблиць перед транзакцією початкового заповнення.
    initialize_database()
    # Додавання всіх категорій і вимірювань одним пакетом.
    return populate_empty_database(categories, records)


def main() -> int:
    """Вивести зрозумілий результат заповнення."""
    try:
        created = seed_database()
    # Повідомлення про некоректну структуру або значення JSON.
    except ValidationError:
        print("Некоректний seed.json: перевірте поля, кількість записів і значення.")
        return 1
    # Повідомлення про порушення обмежень зі скасуванням пакета.
    except (LookupError, sqlite3.IntegrityError):
        print("Категорія відсутня або дані порушують обмеження. Весь пакет скасовано.")
        return 1
    # Запис технічної причини помилки читання або доступу.
    except (OSError, sqlite3.Error):
        logging.getLogger(__name__).exception(
            "Не вдалося виконати початкове заповнення"
        )
        print("Помилка читання файлу або доступу до бази.")
        return 1
    # Виведення результату першого або повторного заповнення.
    print(
        "Базу заповнено: 3 категорії, 8 записів."
        if created
        else "База вже містить дані. Заповнення пропущено, дані не змінено."
    )
    return 0


# Запуск заповнення з поверненням коду завершення програми.
if __name__ == "__main__":
    raise SystemExit(main())
