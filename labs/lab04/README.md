# Лабораторна робота №4. Варіант 7

Консольна утиліта для отримання CVE з NVD API 2.0 та локального аналізу.
Працює незалежно від ЛР3 та її бази даних. Потрібен Python 3.12 або новіший.
Команди PowerShell виконуй із кореня `cybersecurity-python-lab`.

`main.py` керує запуском, `api_client.py` отримує дані, `analysis.py` перевіряє
їх і формує результат. Правила містяться в `config.py`: наш запис — `RULES[7]`.
Внутрішній запис — звичайний словник з описом, статусом, копією CVSS та джерелом.

## Встановлення

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Якщо середовища ще немає, спочатку створи його: `python -m venv .venv`.

## Запуск без мережі

```powershell
.\.venv\Scripts\python.exe -m labs.lab04.main --cve CVE-2099-10001 --input labs/lab04/data/nvd_sample.json
```

`CVE-2099-10001` є синтетичним прикладом. Шукати його в NVD не потрібно.
Очікувані поля результату: `variant: 7`, `score: 9.8`,
`observed: "HIGH"`, `decision: "review"`.

## Запуск із NVD

```powershell
.\.venv\Scripts\python.exe -m labs.lab04.main --cve CVE-2021-44228
```

Ключ необов'язковий. Якщо `NVD_API_KEY` задано в середовищі, він передається
через заголовок `apiKey`. Не зберігай справжній ключ у файлах проєкту.
Виконується один запит із таймаутом `(3.05, 10)`, без перенаправлень і повторів.
Перед ручним запитом переглянь [правила NVD](https://nvd.nist.gov/developers/start-here).

## Правило та результат

Варіант береться з `shared/student.py`. Для варіанта 7:
`score >= 7.0` і `availabilityImpact == "HIGH"` в одній вибраній оцінці CVSS v3.1.
Вибирається перша `Primary`, інакше перша оцінка v3.1.

У stdout виводиться один JSON-об'єкт із ключами `cve_id`, `variant`,
`description`, `vuln_status`, `cvss_version`, `score`, `score_source`, `vector`,
`rule`, `observed`, `decision`. Відсутні дані позначаються `null`.

Можливі рішення: `not_found`, `rejected`, `insufficient_data`, `review`, `other`.
`review` означає відповідність навчальному правилу. `other` та
`insufficient_data` не підтверджують безпечність вразливості.

Коди завершення: `0` - звіт сформовано; `1` - помилка отримання, читання
або структури даних; `2` - неправильні аргументи або номер варіанта.
Повідомлення про помилки виводяться у stderr.

## Перевірки

```powershell
.\.venv\Scripts\python.exe -m pytest labs/lab04/tests -q --basetemp=.pytest_cache/lab04-user-temp
.\.venv\Scripts\python.exe -m ruff check labs/lab04
.\.venv\Scripts\python.exe -m ruff format --check labs/lab04
```

Тести використовують синтетичні дані й підміни Requests. Автоматична фікстура
видаляє успадкований ключ і забороняє справжні запити. Тест порога окремо
перевіряє `6.9`, `7.0` та `7.1`; оцінка з вектора не перераховується.
