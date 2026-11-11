"""Ізольоване середовище та синтетичні дані для тестів."""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from labs.lab04 import api_client


# Заборона справжніх запитів і використання успадкованого ключа.
@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch):
    monkeypatch.delenv("NVD_API_KEY", raising=False)
    monkeypatch.delattr("requests.sessions.Session.request")


# Завантаження нового незалежного словника для кожного тесту.
@pytest.fixture
def sample_payload():
    path = Path(__file__).resolve().parents[1] / "data" / "nvd_sample.json"
    return json.loads(path.read_text(encoding="utf-8"))


# Надання доступу до CVE поточної тестової відповіді.
@pytest.fixture
def cve(sample_payload):
    return sample_payload["vulnerabilities"][0]["cve"]


# Надання доступу до вибраної синтетичної оцінки.
@pytest.fixture
def metric(cve):
    return cve["metrics"]["cvssMetricV31"][0]


# Підміна отримання даних для перевірок командного інтерфейсу.
@pytest.fixture
def fetch(monkeypatch, sample_payload):
    result = Mock(return_value=sample_payload)
    monkeypatch.setattr(api_client, "fetch_response", result)
    return result


# Створення тимчасового файла із синтетичною відповіддю.
@pytest.fixture
def input_path(tmp_path, sample_payload):
    path = tmp_path / "response.json"
    path.write_text(json.dumps(sample_payload, ensure_ascii=False), encoding="utf-8")
    return path
