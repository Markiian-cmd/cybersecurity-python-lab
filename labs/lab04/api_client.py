"""Отримання відповіді NVD CVE API 2.0."""

import os

import requests

API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
TIMEOUT = (3.05, 10)


# Передавання лише безпечного пояснення помилки отримання даних.
class FetchError(RuntimeError):
    """Помилка запиту без секретів і тіла відповіді."""


# Формування заголовків із поточним необов'язковим ключем.
def build_headers() -> dict[str, str]:
    """Прочитати ключ під час виклику та прибрати пробіли."""
    headers = {"Accept": "application/json"}
    api_key = os.getenv("NVD_API_KEY", "").strip()
    if api_key:
        headers["apiKey"] = api_key
    return headers


# Виконання одного запиту без повторів і перенаправлень.
def fetch_response(cve_id: str) -> object:
    """Отримати JSON; семантику перевіряє окремий аналізатор."""
    try:
        response = requests.get(
            API_URL,
            params={"cveId": cve_id},
            headers=build_headers(),
            timeout=TIMEOUT,
            allow_redirects=False,
        )
        response.raise_for_status()
    except requests.Timeout:
        raise FetchError("Перевищено час очікування відповіді NVD.") from None
    except requests.ConnectionError:
        raise FetchError("Не вдалося встановити з'єднання з NVD.") from None
    except requests.HTTPError as error:
        if error.response is None:
            status = "невідомий"
        else:
            status = error.response.status_code
        raise FetchError(f"HTTP-помилка NVD: статус {status}.") from None
    except requests.RequestException:
        raise FetchError("Не вдалося виконати мережевий запит до NVD.") from None

    if response.status_code != 200:
        raise FetchError(f"Неочікуваний HTTP-статус NVD: {response.status_code}.")
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        raise FetchError("Відповідь NVD містить некоректний JSON.") from None
