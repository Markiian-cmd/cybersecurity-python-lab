import os
import random
import string
import sys

# Крок 1: Імпорт персональних даних студента
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import STUDENT_NAME, VARIANT_NUMBER


def analyze_passwords() -> None:
    # Виведення даних студента та номера варіанту
    print(f"\nЛабораторна робота | Студент: {STUDENT_NAME} | Варіант: {VARIANT_NUMBER}")

    # Крок 2: Завантаження початкових даних В-7
    passwords = [
        "NetworkS3c!", "easy", "Firewa11@Pass", "anonymous",
        "Intrus10n#Detect", "sample", "Malwar3@Scan", "qwerty",
        "Vulnerab1l!ty", "common"
    ]
    criteria = {
        "min_length": 9,
        "require_digits": True,
        "require_upper": True,
        "require_special": True,
    }
    forbidden_passwords = {
        "easy", "anonymous", "sample", "qwerty", "common", "password"
    }

    # Крок 3: Генерація 3 випадкових індексів та додавання дублікатів у кінець
    random_indices = random.sample(range(len(passwords)), 3)
    for idx in random_indices:
        passwords.append(passwords[idx])

    # Крок 5: Виведення заголовка таблиці
    print(f"\n{'Пароль':<20} | {'Статус надійності'}")
    print("-" * 45)

    # Крок 4: Оцінка надійності кожного пароля
    for pwd in passwords:
        # Перевірка наявності категорій символів
        has_digit = any(c.isdigit() for c in pwd)
        has_upper = any(c.isupper() for c in pwd)
        has_lower = any(c.islower() for c in pwd)
        has_special = any(c in string.punctuation for c in pwd)

        # кількість задоволених груп (від 1 до 4)
        criteria_met_count = sum([has_digit, has_upper, has_lower, has_special])

        # Перевірка обовязкових вимог безпеки : цифра + велика літера + спецсимвол
        meets_all_security = has_digit and has_upper and has_special

        # Перевірка унікальності в оновленому списку
        is_unique = passwords.count(pwd) == 1

        # Класифікація згідно з правилами завдання:
        if pwd in forbidden_passwords or len(pwd) < criteria["min_length"]:
            status = "Заборонений"
        elif (
            meets_all_security
            and len(pwd) >= criteria["min_length"] + 4
            and is_unique
        ):
            status = "Дуже сильний"
        elif meets_all_security:
            status = "Сильний"
        elif criteria_met_count > 1:
            status = "Середній"
        else:
            status = "Слабкий"

        print(f"{pwd:<20} | {status}")


if __name__ == "__main__":
    analyze_passwords()