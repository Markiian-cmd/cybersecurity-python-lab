"""Командний інтерфейс лабораторної роботи №4, варіант 7."""

import argparse
import json
import re
import sys
from pathlib import Path

from labs.lab04 import api_client
from labs.lab04.analysis import build_report, extract_record, is_valid_variant
from shared.student import VARIANT_NUMBER


# Перевірка повного збігу ідентифікатора з шаблоном CVE.
def _cve_argument(value: str) -> str:
    """Перевірити регістр та цифрові частини ідентифікатора."""
    if re.fullmatch(r"CVE-[0-9]{4}-[0-9]{4,}", value) is None:
        raise argparse.ArgumentTypeError("Очікується ідентифікатор CVE-YYYY-NNNN.")
    return value


# Читання локального JSON без виконання мережевих запитів.
def load_response(path: str | Path) -> object:
    """Завантажити відповідь NVD з UTF-8 файла."""
    with Path(path).open(encoding="utf-8") as source:
        return json.load(source)


# Об'єднання аргументів, отримання даних та формування JSON.
def main(argv: list[str] | None = None) -> int:
    """Повернути код завершення: успіх 0, дані 1, аргументи 2."""
    if not is_valid_variant(VARIANT_NUMBER):
        print("Номер варіанта має бути цілим числом від 1 до 15.", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(
        description="Аналіз CVE за навчальним правилом варіанта."
    )
    parser.add_argument(
        "--cve", required=True, type=_cve_argument, help="Ідентифікатор CVE"
    )
    parser.add_argument(
        "--input", type=Path, help="Локальна відповідь NVD у UTF-8 JSON"
    )
    args = parser.parse_args(argv)
    try:
        if args.input is not None:
            payload = load_response(args.input)
        else:
            payload = api_client.fetch_response(args.cve)
        record = extract_record(payload, args.cve)
        report = build_report(record, args.cve, VARIANT_NUMBER)
    except api_client.FetchError as error:
        message = f"Помилка отримання даних: {error}"
    except json.JSONDecodeError:
        message = "Локальний файл містить некоректний JSON."
    except UnicodeError:
        message = "Локальний файл має бути закодований у UTF-8."
    except OSError:
        message = "Не вдалося прочитати локальний файл відповіді."
    except ValueError as error:
        message = f"Некоректні дані: {error}"
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    print(message, file=sys.stderr)
    return 1


# Запуск CLI лише при прямому виконанні модуля.
if __name__ == "__main__":
    raise SystemExit(main())
