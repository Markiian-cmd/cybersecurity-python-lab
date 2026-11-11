"""Локальні інтеграційні перевірки командного інтерфейсу."""

import importlib
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from labs.lab04 import analysis, api_client
from labs.lab04 import main as cli

CVE_ID = "CVE-2099-10001"


# Локальний режим формує один JSON і не викликає клієнт.
def test_local_run(fetch, capsys, input_path):
    fetch.side_effect = AssertionError("Мережевий клієнт викликати заборонено")
    assert cli.main(["--cve", CVE_ID, "--input", str(input_path)]) == 0
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["variant"] == 7
    assert report["decision"] == "review"
    assert report["observed"] == "HIGH"
    assert captured.err == ""
    fetch.assert_not_called()


# Без локального файла CLI передає ідентифікатор клієнту.
def test_online_mode_with_double(fetch, capsys):
    assert cli.main(["--cve", CVE_ID]) == 0
    assert json.loads(capsys.readouterr().out)["decision"] == "review"
    fetch.assert_called_once_with(CVE_ID)


# Порожній пошук завершується успіхом незалежно від року CVE.
def test_not_found_is_success(fetch, capsys):
    fetch.return_value = {"vulnerabilities": []}
    assert cli.main(["--cve", "CVE-0000-1234"]) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out)["decision"] == "not_found"
    assert captured.err == ""


# Відхилений запис і брак даних також дають успішний звіт.
@pytest.mark.parametrize(
    "status, decision", [("Rejected", "rejected"), (None, "insufficient_data")]
)
def test_special_decisions_are_success(fetch, capsys, cve, status, decision):
    if status is None:
        del cve["vulnStatus"]
    else:
        cve["vulnStatus"] = status
    assert cli.main(["--cve", CVE_ID]) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out)["decision"] == decision
    assert captured.err == ""


# Українські символи звіту виводяться без ASCII-екранування.
def test_unicode_output(fetch, capsys, cve):
    cve["descriptions"][0]["value"] = "Навчальний опис"
    assert cli.main(["--cve", CVE_ID]) == 0
    output = capsys.readouterr().out
    assert "Навчальний опис" in output
    assert "\\u" not in output


# Некоректні аргументи відхиляються до отримання даних.
@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--input", "sample.json"],
        ["--cve", "cve-2021-44228"],
        ["--cve", "CVE-2021-123"],
        ["--cve", "CVE-21-44228"],
        ["--cve", "CVE-2021-44228suffix"],
        ["--cve", "prefixCVE-2021-44228"],
        ["--cve", "CVE-2021-44228\n"],
        ["--cve", "CVE-２０２１-44228"],
        ["--cve", CVE_ID, "--variant", "1"],
        ["--cve", CVE_ID, "--url", "https://example.test"],
    ],
)
def test_invalid_arguments(fetch, capsys, argv):
    with pytest.raises(SystemExit) as caught:
        cli.main(argv)
    assert caught.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err
    fetch.assert_not_called()


# Невірний номер у спільному модулі повертає код два.
@pytest.mark.parametrize("variant", [True, False, 0, 16, "7", 7.0, None])
def test_invalid_student_variant(monkeypatch, fetch, capsys, variant):
    monkeypatch.setattr(cli, "VARIANT_NUMBER", variant)
    assert cli.main(["--cve", CVE_ID]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "варіанта" in captured.err
    fetch.assert_not_called()


# Помилки читання, кодування, JSON і структури повертають одиницю.
@pytest.mark.parametrize(
    "case, message",
    [
        ("missing", "прочитати"),
        ("directory", "прочитати"),
        ("invalid_json", "JSON"),
        ("invalid_utf8", "UTF-8"),
        ("invalid_structure", "Некоректні дані"),
    ],
)
def test_local_errors(tmp_path, capsys, case, message):
    path = tmp_path / "bad.json"
    if case == "directory":
        path.mkdir()
    elif case == "invalid_json":
        path.write_text("{", encoding="utf-8")
    elif case == "invalid_utf8":
        path.write_bytes(b"\xff\xfe")
    elif case == "invalid_structure":
        path.write_text("{}", encoding="utf-8")
    assert cli.main(["--cve", CVE_ID, "--input", str(path)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert message in captured.err
    assert "Traceback" not in captured.err


# Локальна відповідь повинна відповідати запитаному ідентифікатору.
def test_local_cve_mismatch(input_path, capsys):
    assert cli.main(["--cve", "CVE-2021-44228", "--input", str(input_path)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "cve.id" in captured.err


# Помилка клієнта спрямовується лише в стандартний потік помилок.
def test_fetch_error(fetch, capsys):
    fetch.side_effect = api_client.FetchError("HTTP-помилка NVD: статус 429.")
    assert cli.main(["--cve", CVE_ID]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "429" in captured.err
    assert "Traceback" not in captured.err


# Невідома програмна помилка не приховується загальним перехопленням.
def test_programming_error_is_not_hidden(fetch):
    fetch.side_effect = RuntimeError("bug")
    with pytest.raises(RuntimeError, match="bug"):
        cli.main(["--cve", CVE_ID])


# Імпорт модулів не читає даних і не виконує запитів.
def test_imports_have_no_side_effects(monkeypatch, capsys):
    read = Mock(side_effect=AssertionError("Читання файла під час імпорту"))
    fetch = Mock(side_effect=AssertionError("Запит під час імпорту"))
    getenv = Mock(side_effect=AssertionError("Читання середовища під час імпорту"))
    monkeypatch.setattr(Path, "open", read)
    monkeypatch.setattr(api_client.requests, "get", fetch)
    monkeypatch.setattr(api_client.os, "getenv", getenv)
    for module in (analysis, api_client, cli):
        importlib.reload(module)
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""
    read.assert_not_called()
    fetch.assert_not_called()
    getenv.assert_not_called()
