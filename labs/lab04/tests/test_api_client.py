"""Перевірка справжнього HTTP-клієнта з підміною Requests."""

from unittest.mock import Mock

import pytest
import requests

from labs.lab04 import api_client

CVE_ID = "CVE-2099-10001"


# Створення контрольованої HTTP-відповіді без мережі.
@pytest.fixture
def response(monkeypatch, sample_payload):
    result = Mock(spec=requests.Response, status_code=200)
    result.json.return_value = sample_payload
    monkeypatch.setattr(api_client.requests, "get", Mock(return_value=result))
    return result


# Відсутній або порожній ключ не передається серверу.
@pytest.mark.parametrize("api_key", [None, "", "   ", "\t\n"])
def test_headers_without_key(monkeypatch, api_key):
    if api_key is not None:
        monkeypatch.setenv("NVD_API_KEY", api_key)
    assert api_client.build_headers() == {"Accept": "application/json"}


# Ключ читається під час кожного виклику функції.
def test_headers_read_current_key(monkeypatch):
    assert api_client.build_headers() == {"Accept": "application/json"}
    monkeypatch.setenv("NVD_API_KEY", "  invented-test-key  ")
    assert api_client.build_headers() == {
        "Accept": "application/json",
        "apiKey": "invented-test-key",
    }


# Перевірка адреси, параметрів, заголовків, таймауту та перенаправлень.
@pytest.mark.parametrize("api_key", [None, "invented-test-key"])
def test_fetch_request_contract(monkeypatch, response, sample_payload, api_key):
    headers = {"Accept": "application/json"}
    if api_key is not None:
        monkeypatch.setenv("NVD_API_KEY", api_key)
        headers["apiKey"] = api_key
    fake_get = api_client.requests.get
    assert api_client.fetch_response(CVE_ID) == sample_payload
    fake_get.assert_called_once_with(
        "https://services.nvd.nist.gov/rest/json/cves/2.0",
        params={"cveId": CVE_ID},
        headers=headers,
        timeout=(3.05, 10),
        allow_redirects=False,
    )
    response.raise_for_status.assert_called_once_with()
    response.json.assert_called_once_with()


# Мережеві винятки перетворюються на безпечні зрозумілі повідомлення.
@pytest.mark.parametrize(
    "error, message",
    [
        (requests.Timeout("SECRET"), "час очікування"),
        (requests.ConnectionError("SECRET"), "з'єднання"),
        (requests.RequestException("SECRET"), "мережевий запит"),
    ],
)
def test_network_errors(monkeypatch, error, message):
    fake_get = Mock(side_effect=error)
    monkeypatch.setattr(api_client.requests, "get", fake_get)
    with pytest.raises(api_client.FetchError, match=message) as caught:
        api_client.fetch_response(CVE_ID)
    assert "SECRET" not in str(caught.value)
    fake_get.assert_called_once()


# HTTP 404 залишається помилкою отримання, а не порожнім пошуком.
@pytest.mark.parametrize("status", [400, 403, 404, 429, 500])
def test_http_errors(response, status):
    response.status_code = status
    response.raise_for_status.side_effect = requests.HTTPError(
        "SECRET", response=response
    )
    with pytest.raises(api_client.FetchError, match=str(status)) as caught:
        api_client.fetch_response(CVE_ID)
    assert "SECRET" not in str(caught.value)
    response.json.assert_not_called()


# Перенаправлення та інші неочікувані статуси не приймаються.
@pytest.mark.parametrize("status", [201, 204, 301, 302, 307, 308])
def test_unexpected_status(response, status):
    response.status_code = status
    with pytest.raises(api_client.FetchError, match=str(status)):
        api_client.fetch_response(CVE_ID)
    response.json.assert_not_called()


# Успішний HTTP-статус не приховує помилку декодування JSON.
def test_invalid_response_json(response):
    response.json.side_effect = requests.exceptions.JSONDecodeError("SECRET", "{", 1)
    with pytest.raises(api_client.FetchError, match="JSON") as caught:
        api_client.fetch_response(CVE_ID)
    assert "SECRET" not in str(caught.value)


# Клієнт передає декодовані дані окремому семантичному аналізатору.
def test_fetch_does_not_validate_structure(response):
    response.json.return_value = []
    assert api_client.fetch_response(CVE_ID) == []
