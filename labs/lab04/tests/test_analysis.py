"""Перевірка контракту NVD і правила варіанта 7."""

from copy import deepcopy

import pytest

from labs.lab04.analysis import build_report, extract_record

CVE_ID = "CVE-2099-10001"


# Отримання звіту сьомого варіанта з тестової відповіді.
def _report(payload):
    return build_report(extract_record(payload, CVE_ID), CVE_ID, 7)


# Порівняння повного звіту з явно заданим результатом.
def test_sample_report(sample_payload):
    record = extract_record(sample_payload, CVE_ID)
    assert build_report(record, CVE_ID, 7) == {
        "cve_id": CVE_ID,
        "variant": 7,
        "description": "Synthetic vulnerability for offline API testing.",
        "vuln_status": "Analyzed",
        "cvss_version": "3.1",
        "score": 9.8,
        "score_source": "nvd@nist.gov",
        "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
        "rule": {"threshold": 7.0, "field": "availabilityImpact", "expected": "HIGH"},
        "observed": "HIGH",
        "decision": "review",
    }


# Перевірка порога та незалежної умови впливу на доступність.
@pytest.mark.parametrize(
    "score, impact, decision",
    [
        (0, "HIGH", "other"),
        (6.9, "HIGH", "other"),
        (7.0, "HIGH", "review"),
        (7.1, "HIGH", "review"),
        (10, "HIGH", "review"),
        (9.8, "LOW", "other"),
        (9.8, "NONE", "other"),
    ],
)
def test_variant_seven_boundary(sample_payload, metric, score, impact, decision):
    metric["cvssData"].update(baseScore=score, availabilityImpact=impact)
    report = _report(sample_payload)
    assert report["decision"] == decision


# Перевірка порожнього пошуку зі збереженням структури звіту.
def test_not_found():
    record = extract_record({"vulnerabilities": []}, CVE_ID)
    assert record is None
    report = build_report(record, CVE_ID, 7)
    assert report == {
        "cve_id": CVE_ID,
        "variant": 7,
        "description": None,
        "vuln_status": None,
        "cvss_version": None,
        "score": None,
        "score_source": None,
        "vector": None,
        "rule": {"threshold": 7.0, "field": "availabilityImpact", "expected": "HIGH"},
        "observed": None,
        "decision": "not_found",
    }


# Відхилення некоректної обгортки без підміни порожнім результатом.
@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {},
        {"vulnerabilities": None},
        {"vulnerabilities": {}},
        {"vulnerabilities": [{}, {}]},
        {"vulnerabilities": [None]},
        {"vulnerabilities": [{}]},
        {"vulnerabilities": [{"cve": []}]},
        {"vulnerabilities": [{"cve": {}}]},
    ],
)
def test_invalid_envelope(payload):
    with pytest.raises(ValueError):
        extract_record(payload, CVE_ID)


# Відхилення відповіді для іншого ідентифікатора CVE.
def test_mismatching_cve(sample_payload):
    with pytest.raises(ValueError, match="cve.id"):
        extract_record(sample_payload, "CVE-2021-44228")


# Збереження статусу й опису без аналізу непридатних оцінок.
@pytest.mark.parametrize(
    "status, decision", [("Rejected", "rejected"), (None, "insufficient_data")]
)
def test_status_precedes_metrics(sample_payload, cve, status, decision):
    if status is None:
        del cve["vulnStatus"]
    else:
        cve["vulnStatus"] = status
    cve["metrics"] = "навмисно некоректна оцінка"
    report = _report(sample_payload)
    assert report["decision"] == decision
    assert report["vuln_status"] == status
    assert report["description"] == "Synthetic vulnerability for offline API testing."
    for field in ("cvss_version", "score", "score_source", "vector", "observed"):
        assert report[field] is None


# Відхилення некоректних статусу, описів і контейнера метрик.
@pytest.mark.parametrize(
    "field, value, match",
    [
        ("vulnStatus", None, "vulnStatus"),
        ("vulnStatus", "", "vulnStatus"),
        ("vulnStatus", "   ", "vulnStatus"),
        ("vulnStatus", 1, "vulnStatus"),
        ("vulnStatus", True, "vulnStatus"),
        ("vulnStatus", [], "vulnStatus"),
        ("descriptions", None, None),
        ("descriptions", {}, None),
        ("descriptions", [None], None),
        ("descriptions", [{}], None),
        ("descriptions", [{"lang": "en", "value": None}], None),
        ("descriptions", [{"lang": 1, "value": "text"}], None),
        ("descriptions", [{"lang": "en", "value": "ok"}, {}], None),
        ("metrics", None, None),
        ("metrics", [], None),
        ("metrics", {"cvssMetricV31": None}, None),
        ("metrics", {"cvssMetricV31": {}}, None),
        ("metrics", {"cvssMetricV31": [None]}, None),
        ("metrics", {"cvssMetricV31": [{}]}, None),
    ],
)
def test_invalid_cve_fields(sample_payload, cve, field, value, match):
    cve[field] = value
    with pytest.raises(ValueError, match=match):
        extract_record(sample_payload, CVE_ID)


# Вибір першого непорожнього англійського опису.
def test_description_selection(sample_payload, cve):
    cve["descriptions"] = [
        {"lang": "uk", "value": "Український опис"},
        {"lang": "en", "value": " "},
        {"lang": "en", "value": "First English description"},
        {"lang": "en", "value": "Second English description"},
    ]
    assert (
        extract_record(sample_payload, CVE_ID)["description"]
        == "First English description"
    )


# Відсутність англійського опису допускає продовження аналізу.
@pytest.mark.parametrize("descriptions", [[], [{"lang": "uk", "value": "Опис"}]])
def test_no_english_description(sample_payload, cve, descriptions):
    cve["descriptions"] = descriptions
    assert extract_record(sample_payload, CVE_ID)["description"] is None


# Відсутнє необов'язкове поле описів дає порожнє значення.
def test_missing_descriptions(sample_payload, cve):
    del cve["descriptions"]
    assert extract_record(sample_payload, CVE_ID)["description"] is None


# Відсутність оцінки v3.1 відрізняється від пошкодженої структури.
@pytest.mark.parametrize("metrics", [{}, {"cvssMetricV31": []}, {"cvssMetricV30": []}])
def test_missing_v31(sample_payload, cve, metrics):
    cve["metrics"] = metrics
    report = _report(sample_payload)
    assert report["decision"] == "insufficient_data"
    assert report["score"] is None


# Повністю відсутнє поле метрик означає недостатність даних.
def test_missing_metrics(sample_payload, cve):
    del cve["metrics"]
    report = _report(sample_payload)
    assert report["decision"] == "insufficient_data"


# Відхилення пошкоджених даних CVSS і недопустимих оцінок.
@pytest.mark.parametrize(
    "field, value",
    [
        ("cvssData", None),
        ("cvssData", []),
        ("cvssData", "9.8"),
        ("baseScore", None),
        ("baseScore", "9.8"),
        ("baseScore", True),
        ("baseScore", False),
        ("baseScore", -0.1),
        ("baseScore", 10.1),
        ("baseScore", float("nan")),
        ("baseScore", float("inf")),
        ("baseScore", float("-inf")),
        ("baseScore", []),
        ("baseScore", 10**400),
    ],
)
def test_invalid_metric_fields(sample_payload, metric, field, value):
    target = metric
    if field == "baseScore":
        target = metric["cvssData"]
    target[field] = value
    with pytest.raises(ValueError, match=field):
        extract_record(sample_payload, CVE_ID)


# Відсутня базова оцінка є помилкою вибраного запису.
def test_missing_base_score(sample_payload, metric):
    del metric["cvssData"]["baseScore"]
    with pytest.raises(ValueError, match="baseScore"):
        extract_record(sample_payload, CVE_ID)


# Відсутня ознака варіанта зберігає доступну числову оцінку.
def test_missing_variant_field(sample_payload, metric):
    del metric["cvssData"]["availabilityImpact"]
    report = _report(sample_payload)
    assert report["decision"] == "insufficient_data"
    assert report["observed"] is None
    assert report["score"] == 9.8


# Перевірка ознаки варіанта виконується саме під час звітування.
@pytest.mark.parametrize("impact", [None, "high", "INVALID", 1, True, [], {}])
def test_invalid_variant_field(sample_payload, metric, impact):
    metric["cvssData"]["availabilityImpact"] = impact
    record = extract_record(sample_payload, CVE_ID)
    with pytest.raises(ValueError, match="availabilityImpact"):
        build_report(record, CVE_ID, 7)


# Відсутні необов'язкові метадані оцінки зберігаються як null.
def test_missing_score_metadata(sample_payload, metric):
    del metric["source"]
    del metric["cvssData"]["version"]
    del metric["cvssData"]["vectorString"]
    report = _report(sample_payload)
    assert report["decision"] == "review"
    for field in ("cvss_version", "score_source", "vector"):
        assert report[field] is None


# Наявні метадані не можуть містити порожні чи некоректні значення.
@pytest.mark.parametrize("field", ["source", "version", "vectorString"])
@pytest.mark.parametrize("value", [None, "", " ", 1, []])
def test_invalid_score_metadata(sample_payload, metric, field, value):
    target = metric if field == "source" else metric["cvssData"]
    target[field] = value
    with pytest.raises(ValueError, match=field):
        extract_record(sample_payload, CVE_ID)


# Заборона використання іншої версії в контейнері v3.1.
def test_wrong_version(sample_payload, metric):
    metric["cvssData"]["version"] = "3.0"
    with pytest.raises(ValueError, match="3.1"):
        extract_record(sample_payload, CVE_ID)


# Перша Primary має пріоритет і не змішується з Secondary.
def test_first_primary_selection(sample_payload, cve, metric):
    secondary = deepcopy(metric)
    secondary["type"] = "Secondary"
    secondary["cvssData"]["baseScore"] = 1.0
    primary = deepcopy(metric)
    primary["source"] = "primary@example.test"
    primary["cvssData"].update(baseScore=7.0, availabilityImpact="LOW")
    cve["metrics"]["cvssMetricV31"] = [secondary, primary, deepcopy(metric)]
    report = _report(sample_payload)
    assert report["score"] == 7.0
    assert report["observed"] == "LOW"
    assert report["score_source"] == "primary@example.test"
    assert report["decision"] == "other"


# За відсутності Primary використовується перша доступна оцінка.
def test_first_metric_fallback(sample_payload, cve, metric):
    first = deepcopy(metric)
    first["type"] = "Secondary"
    first["cvssData"]["baseScore"] = 6.0
    second = deepcopy(metric)
    second["type"] = "Secondary"
    cve["metrics"]["cvssMetricV31"] = [first, second]
    report = _report(sample_payload)
    assert report["score"] == 6.0
    assert report["decision"] == "other"


# Невибрані оцінки не проходять семантичний аналіз.
def test_unselected_metric_ignored(sample_payload, cve, metric):
    cve["metrics"]["cvssMetricV31"] = [{"type": "Secondary", "cvssData": None}, metric]
    assert _report(sample_payload)["decision"] == "review"


# Усі елементи списку повинні залишатися об'єктами.
def test_non_object_unselected_metric(sample_payload, cve):
    cve["metrics"]["cvssMetricV31"].append(None)
    with pytest.raises(ValueError):
        extract_record(sample_payload, CVE_ID)


# Аналізатор не змінює передану відповідь.
def test_payload_remains_unchanged(sample_payload):
    original = deepcopy(sample_payload)
    _report(sample_payload)
    assert sample_payload == original


# Внутрішній запис зберігає власну копію вибраних полів.
def test_record_copies_cvss_data(sample_payload, metric):
    record = extract_record(sample_payload, CVE_ID)
    metric["cvssData"]["availabilityImpact"] = "LOW"
    assert build_report(record, CVE_ID, 7)["decision"] == "review"


# Відхилення номера варіанта поза дозволеним контрактом.
@pytest.mark.parametrize("variant", [True, False, 0, 16, 7.0, "7", None])
def test_invalid_variant(variant):
    with pytest.raises(ValueError, match="варіанта"):
        build_report(None, CVE_ID, variant)
