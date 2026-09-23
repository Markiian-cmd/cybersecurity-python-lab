"""Завдання 2: Багаторівнева система контролю доступу."""

import os
import sys

# Підключення модуля студента
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import STUDENT_NAME, VARIANT_NUMBER


def check_access() -> None:
    print(f"\n--- Завдання 2 (Виконавець: {STUDENT_NAME}, Варіант: {VARIANT_NUMBER}) ---")

    # Вхідні дані В - 7
    users = {
        "incident_commander": {"role": "incident_response", "clearance": 4, "department": "CSIRT", "active": True},
        "malware_analyst": {"role": "malware_researcher", "clearance": 3, "department": "Research", "active": True},
        "monitoring_tech": {"role": "monitoring", "clearance": 2, "department": "NOC", "active": True},
        "customer_rep": {"role": "customer_service", "clearance": 1, "department": "Customer", "active": True},
        "backup_service": {"role": "service_account", "clearance": 2, "department": "System", "active": False},
    }

    resources = [
        ("incident_playbook", 4),
        ("malware_lab", 3),
        ("monitoring_dashboards", 2),
        ("customer_portal", 1),
        ("emergency_procedures", 4),
        ("service_desk", 1),
        ("reverse_engineering", 3),
        ("alert_systems", 2),
        ("escalation_matrix", 3),
        ("knowledge_base", 1),
    ]

    security_levels = ("Public Access", "Authorized", "Privileged", "Critical")
    blocked_users = {"backup_service", "deactivated_svc", "policy_violation"}

    # Крок 2: Виведення списку ресурсів із текстовими рівнями доступу
    print("Список ресурсів системи:")
    for res_name, res_level in resources:
        print(f" - {res_name}: {security_levels[res_level - 1]}")

    print("\nРезультати перевірки доступу:")

    # Об'єднуємо користувачів системи та заблокованих для повної перевірки всіх статусів
    all_test_users = list(users.keys()) + [u for u in blocked_users if u not in users]

    # Крок 3 та 4: Перевірка матриці доступу та вивід
    for user in all_test_users:
        for res_name, res_level in resources:
            if user not in users:
                result = "DENY (User not found)"
            elif user in blocked_users:
                result = "DENY (User is blocked)"
            elif not users[user]["active"]:
                result = "DENY (Account inactive)"
            elif users[user]["clearance"] >= res_level:
                result = "ALLOW"
            else:
                result = "DENY (Insufficient clearance)"

            print(f"user={user:<20} resource={res_name:<24} -> {result}")


if __name__ == "__main__":
    check_access()