"""Tests for the local (Ollama) timesheet reader's pure logic."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from create_dummy_timesheet_pdf import make_timesheet

import timesheets_ollama as ts_ollama


def _fake_response(content: str) -> SimpleNamespace:
    return SimpleNamespace(message=SimpleNamespace(content=content))


def test_find_timesheets_returns_only_images_and_pdfs(tmp_path):
    (tmp_path / "week1.jpg").write_bytes(b"fake-jpg")
    (tmp_path / "week2.pdf").write_bytes(b"fake-pdf")
    (tmp_path / "notes.txt").write_text("ignore me")
    (tmp_path / "hours_to_review.csv").write_text("name,hours\n")

    found = ts_ollama.find_timesheets(tmp_path)

    assert [p.name for p in found] == ["week1.jpg", "week2.pdf"]


def test_parse_rows_extracts_json_array_from_surrounding_prose():
    text = 'Sure, here you go:\n[{"name": "Jane Doe", "hours": 7.5}]\nHope that helps!'

    rows = ts_ollama._parse_rows(text)

    assert rows == [{"name": "Jane Doe", "hours": 7.5}]


def test_parse_rows_handles_bare_json_array():
    text = '[{"name": "John Smith", "hours": 8.0}]'

    rows = ts_ollama._parse_rows(text)

    assert rows == [{"name": "John Smith", "hours": 8.0}]


def test_file_to_images_returns_raw_bytes_for_an_image(tmp_path):
    image_path = tmp_path / "week1.jpg"
    image_path.write_bytes(b"\xff\xd8\xff-fake-jpeg-bytes")

    images = ts_ollama._file_to_images(image_path)

    assert images == [image_path.read_bytes()]


def test_file_to_images_rasterizes_each_pdf_page_to_png_bytes(tmp_path):
    pdf_path = tmp_path / "week2.pdf"
    make_timesheet(pdf_path, [("Jane Doe", 7.5)], "2026-06-01")

    images = ts_ollama._file_to_images(pdf_path)

    assert len(images) == 1
    assert images[0].startswith(b"\x89PNG\r\n\x1a\n")


def test_read_all_timesheets_writes_csv_from_mocked_model(monkeypatch, tmp_path):
    (tmp_path / "week1.jpg").write_bytes(b"\xff\xd8\xff-fake-jpeg-bytes")
    monkeypatch.setattr(ts_ollama.ollama, "list", lambda: None)
    monkeypatch.setattr(
        ts_ollama.ollama,
        "chat",
        lambda **kwargs: _fake_response('[{"name": "Jane Doe", "hours": 7.5}]'),
    )
    out_csv = tmp_path / "hours_to_review.csv"

    count = ts_ollama.read_all_timesheets(tmp_path, out_csv)

    assert count == 1
    assert out_csv.read_text() == "name,hours,source_file\nJane Doe,7.5,week1.jpg\n"


def test_read_all_timesheets_raises_friendly_error_when_ollama_unreachable(
    monkeypatch, tmp_path
):
    (tmp_path / "week1.jpg").write_bytes(b"\xff\xd8\xff-fake-jpeg-bytes")

    def _boom():
        raise ConnectionError("no server")

    monkeypatch.setattr(ts_ollama.ollama, "list", _boom)

    with pytest.raises(RuntimeError, match="Ollama"):
        ts_ollama.read_all_timesheets(tmp_path, tmp_path / "hours_to_review.csv")


def test_read_all_timesheets_raises_when_folder_has_no_files(monkeypatch, tmp_path):
    monkeypatch.setattr(ts_ollama.ollama, "list", lambda: None)

    with pytest.raises(FileNotFoundError):
        ts_ollama.read_all_timesheets(tmp_path, tmp_path / "hours_to_review.csv")
