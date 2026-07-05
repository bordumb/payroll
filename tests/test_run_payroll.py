"""Tests for run_payroll.py's reader-selection wiring."""

from __future__ import annotations

from types import SimpleNamespace

import run_payroll


def test_read_step_resolves_reader_and_delegates_to_it(monkeypatch, tmp_path):
    calls = []
    fake_reader = SimpleNamespace(
        read_all_timesheets=lambda folder, out_csv: calls.append((folder, out_csv)) or 3
    )
    monkeypatch.setattr(
        run_payroll.timesheets,
        "get_reader",
        lambda name: calls.append(("get_reader", name)) or fake_reader,
    )

    run_payroll.read_step(tmp_path, "local")

    assert ("get_reader", "local") in calls
    assert (tmp_path, tmp_path / run_payroll.HOURS_FILENAME) in calls


def test_build_parser_reader_flag_defaults_to_none():
    parser = run_payroll.build_parser()
    args = parser.parse_args(["read"])
    assert args.reader is None


def test_build_parser_reader_flag_accepts_cloud_and_local():
    parser = run_payroll.build_parser()
    assert parser.parse_args(["read", "--reader", "cloud"]).reader == "cloud"
    assert parser.parse_args(["read", "--reader", "local"]).reader == "local"


def test_build_parser_reader_flag_rejects_other_values():
    parser = run_payroll.build_parser()
    try:
        parser.parse_args(["read", "--reader", "bogus"])
        assert False, "expected SystemExit for an invalid --reader value"
    except SystemExit:
        pass
