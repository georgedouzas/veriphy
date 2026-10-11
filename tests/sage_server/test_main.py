"""Test the daemon runner."""

import importlib
import io
import json
import sys
from types import ModuleType

import pytest

import veriphy
from veriphy.sage_server import main

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
        main()
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
        main()


def test_main_answers_each_line(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """Answer one response line per request line and skip blank lines."""
    monkeypatch.setattr(sys, 'stdin', io.StringIO('{"id":1,"method":"ping"}\n\n{"id":2,"method":"nosuch"}\n'))
    main()
    responses = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [r['id'] for r in responses] == [1, 2]
    assert responses[0]['result']['veriphy'] == veriphy.__version__
    assert 'nosuch' in responses[1]['error']
