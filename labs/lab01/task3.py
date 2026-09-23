"""Завдання 3: Безпечне хешування, CSV-база та JSON-логування з винятками."""

import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from functools import wraps

# Підключення до кореня проєкту
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import STUDENT_NAME, VARIANT_NUMBER


# Крок 1: Власний виняток для валідації
class ValidationError(Exception):
    """Помилка валідації введених даних."""


# Константи варіанту 7: sha384, довжина 15
MIN_PASSWORD_LENGTH = 15
PERSONAL_SALT = f"{VARIANT_NUMBER:05d}"  # рядок із 5 символів, доповнений нулями

# Шляхи до файлів
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CURRENT_DIR, "data")
USERS_CSV_PATH = os.path.join(DATA_DIR, "users.csv")
LOG_JSON_PATH = os.path.join(DATA_DIR, "log.json")


# Крок 1: Функція хешування
def generate_hash(password: str, salt: str = "00000") -> str:
    """Генерує sha384-хеш від конкатенації пароля та солі."""
    if password is None or salt is None or password == "" or salt == "":
        raise ValueError("Пароль або сіль не можуть бути порожніми.")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"Пароль занадто короткий ({len(password)} симв.). Мінімум: {MIN_PASSWORD_LENGTH}."
        )

    return hashlib.sha384((password + salt).encode("utf-8")).hexdigest()


# Крок 6: Декоратор логування спроб автентифікації
def log_event(func):
    """Записує кожну спробу входу у файл log.json за форматом з інструкції."""
    @wraps(func)
    def wrapper(username, password, *args, **kwargs):
        result_str = "failure"
        try:
            res_bool = func(username, password, *args, **kwargs)
            result_str = "success" if res_bool else "failure"
            return res_bool
        except Exception:
            result_str = "failure"
            raise
        finally:
            os.makedirs(DATA_DIR, exist_ok=True)
            log_entry = {
                "event": "login",
                "user": username,
                "result": result_str,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "args": list(args),
                "kwargs": kwargs,
            }

            logs = []
            if os.path.exists(LOG_JSON_PATH):
                try:
                    with open(LOG_JSON_PATH, "r", encoding="utf-8") as f:
                        logs = json.load(f)
                except json.JSONDecodeError:
                    logs = []

            logs.append(log_entry)
            with open(LOG_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=4, ensure_ascii=False)

    return wrapper


# Крок 3: Функції реєстрації користувачів
def create_user(username: str, password: str) -> tuple[str, str]:
    """Створює запис користувача з хешованим паролем."""
    return username, generate_hash(password, PERSONAL_SALT)


def create_users(users_list: tuple[tuple[str, str], ...]) -> None:
    """Записує валідних користувачів у файл users.csv."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USERS_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["username", "hash_password"])
        for u, p in users_list:
            try:
                rec = create_user(u, p)
                writer.writerow(rec)
            except (ValueError, ValidationError) as e:
                print(f"  [Пропущено запис '{u}']: {e}")


# Крок 4: Читання бази даних у список users_db та вивід таблиці
def load_and_display_users() -> list[dict]:
    """Зчитує CSV-файл у список словників users_db та виводить його на екран."""
    with open(USERS_CSV_PATH, "r", encoding="utf-8") as f:
        users_db = list(csv.DictReader(f))

    print(f"\n{'Користувач':<18} | {'Хеш пароля (sha384)':<96}")
    print("-" * 120)
    for u in users_db:
        print(f"{u['username']:<18} | {u['hash_password']}")

    return users_db


# Крок 5: Автентифікація
@log_event
def login(username: str, password: str, users_db: list[dict]) -> bool:
    """Перевіряє, чи існує користувач у users_db і чи збігається хеш."""
    if not username or not password:
        raise ValueError("Логін і пароль не можуть бути порожніми.")

    try:
        current_hash = generate_hash(password, PERSONAL_SALT)
    except ValidationError:
        return False

    for user_record in users_db:
        if user_record["username"] == username and user_record["hash_password"] == current_hash:
            return True
    return False


# Крок 8: Головна функція main() з повною обробкою винятків
def main() -> None:
    print(f"\n--- Завдання 3 (Студент: {STUDENT_NAME}, Варіант: {VARIANT_NUMBER}) ---")

    # Крок 3: Кортеж із 10 користувачів
    users_to_register = (
        ("admin", "SuperSecurePassword123!"),
        ("incident_lead", "IncidentResponse2026!"),
        ("analyst", "MalwareResearchLab2026!"),
        ("tech_support", "MonitoringDashboards1!"),
        ("auditor", "ComplianceCheck2026!"),
        ("short_user", "Short123!"),       # викликає помилку ValidationError (< 15 симв.)
        ("empty_pass", ""),                # викликає помилку ValueError
        ("dev_ops", "DockerComposeDeploy15!"),
        ("tester", "PenetrationTesting1!"),
        ("sysadmin", "RootAccessGranted99!"),
    )

    # Крок 7: Обробка винятків
    try:
        print("\n1. Реєстрація користувачів у CSV...")
        create_users(users_to_register)

        print("\n2. Зчитування бази даних CSV (Крок 4):")
        users_db = load_and_display_users()

        print("\n3. Тестування функції входу (login):")
        print(" - Вхід admin (вірний):", login("admin", "SuperSecurePassword123!", users_db))
        print(" - Вхід incident_lead (невірний):", login("incident_lead", "WrongPassword12345!", users_db))

        print("\n4. Спроба входу з порожніми полями (тест ValueError):")
        try:
            login("", "SomePassword12345!", users_db)
        except ValueError as err:
            print(f"  Перехоплено очікуваний виняток: {err}")

        print(f"\nУсі спроби входу успішно залоговано у файл: {LOG_JSON_PATH}")

    except (OSError, FileNotFoundError, PermissionError) as io_err:
        print(f"Помилка вводу/виводу файлів: {io_err}")
    except (ValidationError, ValueError) as val_err:
        print(f"Критична помилка валідації: {val_err}")


if __name__ == "__main__":
    main()