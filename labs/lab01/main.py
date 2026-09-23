"""Головний модуль запуску лабораторної роботи №1."""

import os
import sys

# Додавання кореня проекту до шляхів пошуку модулів
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Імпорти завдань та даних студента (всі в одному блоці нагорі)
from labs.lab01.task1 import analyze_passwords
from labs.lab01.task2 import check_access
from labs.lab01.task3 import main as run_task3
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER


def main():
    print("=" * 60)
    print(f"ЛАБОРАТОРНА РОБОТА №1 | {GROUP_NAME}")
    print(f"Студент: {STUDENT_NAME} | Варіант: {VARIANT_NUMBER}")
    print("=" * 60)

    # 1. Запуск Завдання 1
    analyze_passwords()

    # 2. Запуск Завдання 2
    check_access()

    # 3. Запуск Завдання 3
    run_task3()

    print("\nВсі завдання успішно виконані!")


if __name__ == "__main__":
    main()