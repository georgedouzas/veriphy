"""Test the Sage session runner."""

import importlib
import io
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

import veriphy
from veriphy.packs.math.primitives.sage import main

NOT_UNDER_SAGE = 2


def test_main_without_sage_exits_with_message(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Exit with status 2 and the install hint when Sage cannot be imported."""

    def refuse(name: str) -> ModuleType:
        """Fail the way a Python without Sage fails."""
        message = f"No module named 'sage' (importing {name})"
        raise ModuleNotFoundError(message, name='sage')

    monkeypatch.setattr(importlib, 'import_module', refuse)
    with pytest.raises(SystemExit) as exit_info:
        main([])
    assert exit_info.value.code == NOT_UNDER_SAGE
    assert 'must run under SageMath' in capsys.readouterr().err


def test_main_reraises_unrelated_missing_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """Propagate a missing module that is not Sage, since the install hint would mislead."""

    def refuse(name: str) -> ModuleType:
        """Fail on a module other than Sage."""
        message = f"No module named 'other' (importing {name})"
        raise ModuleNotFoundError(message, name='other')

    monkeypatch.setattr(importlib, 'import_module', refuse)
    with pytest.raises(ModuleNotFoundError):
        main([])


def test_main_answers_each_line(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """Answer one response line per request line and skip blank lines."""
    lines = '{"jsonrpc":"2.0","id":1,"method":"ping"}\n\n{"jsonrpc":"2.0","id":2,"method":"nosuch"}\n'
    monkeypatch.setattr(sys, 'stdin', io.StringIO(lines))
    main([])
    responses = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [r['id'] for r in responses] == [1, 2]
    assert responses[0]['result']['veriphy'] == veriphy.__version__
    assert 'nosuch' in responses[1]['error']['message']


def test_one_call_writes_its_result(tmp_path: Path) -> None:
    """Answer one call from an input file into an output file, and exit with status 1 naming an unknown method."""
    source, target = tmp_path / 'input.json', tmp_path / 'out.json'
    source.write_text('{}')
    main(['call', 'ping', str(source), str(target)])
    assert json.loads(target.read_text())['ok'] is True
    with pytest.raises(SystemExit) as exit_info:
        main(['call', 'nosuch', str(source), str(tmp_path / 'none.json')])
    assert exit_info.value.code == 1
    assert not (tmp_path / 'none.json').exists()


def test_version_and_usage(capsys: pytest.CaptureFixture[str]) -> None:
    """Print Sage's version, and the usage for anything else."""
    main(['version'])
    assert capsys.readouterr().out.startswith('SageMath version ')
    with pytest.raises(SystemExit) as exit_info:
        main(['frobnicate'])
    assert (exit_info.value.code, 'usage:' in capsys.readouterr().err) == (NOT_UNDER_SAGE, True)
