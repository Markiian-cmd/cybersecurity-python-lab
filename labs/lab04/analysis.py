"""Чиста перевірка відповіді NVD та застосування навчального правила."""

from labs.lab04.config import FIELD_VALUES, RULES


# Позначення порушення контракту даних як різновиду ValueError.
class DataValidationError(ValueError):
    """Некоректна структура або значення даних NVD."""


# Спільна перевірка номера для аналізатора та CLI.
def is_valid_variant(value: object) -> bool:
    """Перевірити цілий номер від 1 до 15."""
    return isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 15


# Відокремлення відсутнього рядка від некоректного наявного значення.
def _optional_text(data: dict, field: str) -> str | None:
    """Повернути непорожній рядок або None для відсутнього поля."""
    if field not in data:
        return None
    value = data[field]
    if not isinstance(value, str) or not value.strip():
        raise DataValidationError(f"Поле {field} має бути непорожнім рядком.")
    return value


# Перевірка всіх описів і вибір першого англійського.
def _extract_description(cve: dict) -> str | None:
    """Зберегти перший непорожній англійський опис."""
    descriptions = cve.get("descriptions", [])
    if not isinstance(descriptions, list):
        raise DataValidationError("Поле descriptions має бути списком.")
    selected = None
    for description in descriptions:
        if not isinstance(description, dict):
            raise DataValidationError("Кожен опис має містити рядки lang і value.")
        language = description.get("lang")
        text = description.get("value")
        if not isinstance(language, str) or not isinstance(text, str):
            raise DataValidationError("Кожен опис має містити рядки lang і value.")
        if selected is None and language == "en" and text.strip():
            selected = text
    return selected


# Вибір першої Primary після перевірки елементів списку.
def _select_metric(cve: dict) -> dict | None:
    """Вибрати одну оцінку v3.1 або повернути None."""
    metrics = cve.get("metrics", {})
    if not isinstance(metrics, dict):
        raise DataValidationError("Поле metrics має бути об'єктом.")
    candidates = metrics.get("cvssMetricV31", [])
    if not isinstance(candidates, list):
        raise DataValidationError("Поле cvssMetricV31 має бути списком.")
    if not candidates:
        return None

    selected = None
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise DataValidationError("Кожна оцінка cvssMetricV31 має бути об'єктом.")
        if selected is None and candidate.get("type") == "Primary":
            selected = candidate
    if selected is None:
        return candidates[0]
    return selected


# Перетворення відповіді NVD на перевірений внутрішній запис.
def extract_record(payload: object, cve_id: str) -> dict | None:
    """Повернути словник description, vuln_status, cvss, source або None.

    cvss містить копію вибраного cvssData або None без оцінки.
    """
    if not isinstance(payload, dict):
        raise DataValidationError("Відповідь має містити список vulnerabilities.")
    vulnerabilities = payload.get("vulnerabilities")
    if not isinstance(vulnerabilities, list):
        raise DataValidationError("Відповідь має містити список vulnerabilities.")
    if len(vulnerabilities) > 1:
        raise DataValidationError("Точний пошук має повертати не більше одного запису.")
    if not vulnerabilities:
        return None

    item = vulnerabilities[0]
    if not isinstance(item, dict) or not isinstance(item.get("cve"), dict):
        raise DataValidationError("Запис має містити об'єкт cve.")
    cve = item["cve"]
    if cve.get("id") != cve_id:
        raise DataValidationError("Ідентифікатор cve.id не збігається із запитаним.")

    status = _optional_text(cve, "vulnStatus")
    record = {
        "description": _extract_description(cve),
        "vuln_status": status,
        "cvss": None,
        "source": None,
    }
    if status is None or status == "Rejected":
        return record
    selected = _select_metric(cve)
    if selected is None:
        return record

    cvss = selected.get("cvssData")
    if not isinstance(cvss, dict):
        raise DataValidationError("Вибрана оцінка має містити об'єкт cvssData.")
    score = cvss.get("baseScore")
    if (
        isinstance(score, bool)
        or not isinstance(score, (int, float))
        or not 0 <= score <= 10
    ):
        raise DataValidationError(
            "Поле baseScore має бути скінченним числом від 0 до 10."
        )
    version = _optional_text(cvss, "version")
    if version is not None and version != "3.1":
        raise DataValidationError("Версія вибраної оцінки має дорівнювати 3.1.")
    record["source"] = _optional_text(selected, "source")
    _optional_text(cvss, "vectorString")
    record["cvss"] = cvss.copy()
    return record


# Формування висновку лише з даних однієї вибраної оцінки.
def build_report(record: dict | None, cve_id: str, variant: int) -> dict[str, object]:
    """Застосувати правило до словника з extract_record без зміни даних."""
    if not is_valid_variant(variant):
        raise ValueError("Номер варіанта має бути цілим числом від 1 до 15.")
    threshold, field, expected = RULES[variant]
    report: dict[str, object] = {
        "cve_id": cve_id,
        "variant": variant,
        "description": None,
        "vuln_status": None,
        "cvss_version": None,
        "score": None,
        "score_source": None,
        "vector": None,
        "rule": {"threshold": threshold, "field": field, "expected": expected},
        "observed": None,
        "decision": "not_found",
    }
    if record is None:
        return report
    report["description"] = record["description"]
    report["vuln_status"] = record["vuln_status"]
    if record["vuln_status"] == "Rejected":
        report["decision"] = "rejected"
        return report
    report["decision"] = "insufficient_data"
    cvss = record["cvss"]
    if record["vuln_status"] is None or cvss is None:
        return report

    report["cvss_version"] = cvss.get("version")
    report["score"] = cvss["baseScore"]
    report["score_source"] = record["source"]
    report["vector"] = cvss.get("vectorString")
    if field not in cvss:
        return report
    observed = cvss[field]
    if not isinstance(observed, str) or observed not in FIELD_VALUES[field]:
        raise DataValidationError(f"Поле {field} містить недопустиме значення.")
    report["observed"] = observed
    if cvss["baseScore"] >= threshold and observed == expected:
        report["decision"] = "review"
    else:
        report["decision"] = "other"
    return report
