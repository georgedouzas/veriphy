"""Test the graph steps: `validate`, `reason` and `report` record what the graph commands report, and replay."""

import json
from collections.abc import Callable
from pathlib import Path

import pytest

from veriphy.__main__ import main
from veriphy.claims import REASON, REPORT, VALIDATE, load_graph, reason, validate_shapes
from veriphy.steps import run_step


def _run_dirs(workspace: Path) -> set[Path]:
    """Return the graph's certificate directories."""
    runs = workspace / '.veriphy' / 'graph' / 'runs'
    return set(runs.iterdir()) if runs.is_dir() else set()


def test_validate_matches_the_shapes(workspace: Path) -> None:
    """Record the same violations as the validator, as evidence with no level."""
    result = run_step(VALIDATE, workspace)
    report = validate_shapes(load_graph(workspace))
    assert result.record.status == ('conforms' if report.conforms else 'violations')
    violations = result.record.outputs['violations']
    assert isinstance(violations, list)
    assert len(violations) == len(report.violations)
    assert (result.record.kind, result.record.level) == ('evidence', None)


def test_reason_records_the_verdict_and_replays(
    workspace: Path,
    fake_checker: Callable[[str], Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Record the checker's verdict and the certificate directory, and replay without a new run."""
    monkeypatch.setenv('VERIPHY_OO_HORN', str(fake_checker('accepted')))
    first = run_step(REASON, workspace)
    expected = reason(load_graph(workspace), fake_checker('accepted'))
    assert first.record.status == expected.label
    assert (workspace / str(first.record.outputs['directory'])).is_dir()
    before = _run_dirs(workspace)
    second = run_step(REASON, workspace)
    assert second.replayed
    assert _run_dirs(workspace) == before


def test_reason_runs_again_once_the_checker_exists(
    workspace: Path,
    fake_checker: Callable[[str], Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep an unchecked record but reason again when a checker appears."""
    monkeypatch.setenv('VERIPHY_OO_HORN', str(workspace / 'missing-oo-horn'))
    assert run_step(REASON, workspace).record.status == 'unchecked'
    monkeypatch.setenv('VERIPHY_OO_HORN', str(fake_checker('accepted')))
    second = run_step(REASON, workspace)
    assert not second.replayed
    assert second.record.status != 'unchecked'


def test_report_writes_the_appendix(
    workspace: Path,
    fake_checker: Callable[[str], Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Write the appendix over the recorded run, and name it in the record."""
    monkeypatch.setenv('VERIPHY_OO_HORN', str(fake_checker('accepted')))
    result = run_step(REPORT, workspace, {'source': 'chapter9', 'format': 'latex'})
    assert result.record.status == 'written'
    assert (workspace / str(result.record.outputs['path'])).read_text().startswith('\\')


def test_command_prints_only_the_record(
    workspace: Path,
    fake_checker: Callable[[str], Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Print the full record as JSON with `--json`, and nothing else."""
    monkeypatch.setenv('VERIPHY_OO_HORN', str(fake_checker('accepted')))
    main(['--root', str(workspace), 'layers', 'step', 'reason', '--json'])
    record = json.loads(capsys.readouterr().out)
    assert (record['step'], record['kind']) == ('reason', 'check')
    main(['--root', str(workspace), 'layers', 'step', 'records', record['digest'][:12]])
    assert json.loads(capsys.readouterr().out)['digest'] == record['digest']


def test_command_exits_with_the_status(workspace: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Exit with status 3 when the run is unchecked."""
    monkeypatch.setenv('VERIPHY_OO_HORN', str(workspace / 'missing-oo-horn'))
    with pytest.raises(SystemExit) as raised:
        main(['--root', str(workspace), 'layers', 'step', 'reason'])
    assert raised.value.code == 3
