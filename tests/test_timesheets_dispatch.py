"""Tests for the timesheets.py port: picking the cloud or local reader."""

from __future__ import annotations

import pytest

import timesheets


def test_get_reader_cloud_returns_api_module():
    reader = timesheets.get_reader("cloud")
    assert reader.__name__ == "timesheets_api"
    assert callable(reader.read_all_timesheets)


def test_get_reader_local_returns_ollama_module():
    reader = timesheets.get_reader("local")
    assert reader.__name__ == "timesheets_ollama"
    assert callable(reader.read_all_timesheets)


def test_get_reader_defaults_to_cloud_with_no_env_var(monkeypatch):
    monkeypatch.delenv("READER", raising=False)
    reader = timesheets.get_reader(None)
    assert reader.__name__ == "timesheets_api"


def test_get_reader_uses_env_var_when_name_not_given(monkeypatch):
    monkeypatch.setenv("READER", "local")
    reader = timesheets.get_reader(None)
    assert reader.__name__ == "timesheets_ollama"


def test_get_reader_explicit_name_overrides_env_var(monkeypatch):
    monkeypatch.setenv("READER", "local")
    reader = timesheets.get_reader("cloud")
    assert reader.__name__ == "timesheets_api"


def test_get_reader_rejects_unknown_name():
    with pytest.raises(ValueError, match="cloud.*local|local.*cloud"):
        timesheets.get_reader("bogus")
