"""Test the operation API: `veriphy.run` and the `veriphy` command give one result, and `veriphy help` lists verbs."""

from pathlib import Path

import click
import pytest
from click.testing import CliRunner

import veriphy
from veriphy.__main__ import help_text, main
from veriphy.__main__ import veriphy as group
from veriphy.core import StepError
from veriphy.steps import Argument, Outcome, Prepared, Step, register, resolve_verb

ECHO = Step(
    'echo-operation',
    'evidence',
    lambda root, params: Prepared({'text': str(params['text'])}, {'text': params['text']}),
    lambda root, params, prepared: Outcome('agrees', {'text': params['text']}),
    help='repeat the text',
    arguments=(Argument('text'),),
)
register(ECHO)


def test_run_and_the_shell_give_one_record(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Return the same record from `veriphy.run` as `veriphy <verb>` writes, with the result's fields."""
    result = veriphy.run('echo-operation', 'hello', root=tmp_path)
    assert (result.verb, result.target, result.status, result.outputs, result.level) == (
        'echo-operation',
        'hello',
        'agrees',
        {'text': 'hello'},
        None,
    )
    main(['--root', str(tmp_path), 'echo-operation', 'hello'])
    assert 'echo-operation: agrees (replayed)' in capsys.readouterr().out


def test_help_lists_the_verbs() -> None:
    """List the registered operations with their kind, the programs, and Lean's verbs."""
    text = help_text()
    assert 'echo-operation' in text
    assert 'evidence' in text
    for verb in ('check', 'level', 'meaning', 'claims', 'agents', 'certify', 'translate'):
        assert verb in text


def test_unknown_verb_names_the_operations(tmp_path: Path) -> None:
    """Refuse a verb no step has, naming the operations there are."""
    with pytest.raises(StepError, match='the operations are'):
        veriphy.run('certfy', 'x', root=tmp_path)


def test_programs_run_through_veriphy(capsys: pytest.CaptureFixture[str]) -> None:
    """Run a program's subcommand as `veriphy agents …`."""
    main(['agents', 'list'])
    assert 'prove.md' in capsys.readouterr().out


def test_deprecated_verb() -> None:
    """Accept `elaborate` as `check`, warning that it was renamed."""
    with pytest.warns(DeprecationWarning, match="'elaborate' is now 'check'"):
        assert resolve_verb('elaborate') == 'check'


def test_one_click_group(tmp_path: Path) -> None:
    """Run every program and operation through one click group, with help generated from each step."""
    assert isinstance(group, click.Group)
    runner = CliRunner()
    shown = runner.invoke(group, ['--root', str(tmp_path), 'meaning', '--help'])
    assert shown.exit_code == 0
    assert all(option in shown.output for option in ('--seed', '--values', '--points', '--informal'))
    (tmp_path / 'veriphy.yaml').write_text('version: 1\npacks: [core]\n')
    missing = runner.invoke(group, ['--root', str(tmp_path), 'check', 'x.lean'])
    assert missing.exit_code == 2
    assert runner.invoke(group, ['--root', str(tmp_path), 'config', 'check']).exit_code == 0
