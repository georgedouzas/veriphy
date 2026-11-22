"""Test the operation API: `veriphy.run` and the `veriphy` command give one result, and `veriphy help` lists verbs."""

import importlib
import re
from pathlib import Path

import click
import pytest
from click.testing import CliRunner

import veriphy
from veriphy.__main__ import help_text, main
from veriphy.__main__ import veriphy as group
from veriphy.core import StepError, check_config, resolve
from veriphy.steps import Argument, Outcome, Prepared, Step, register

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
    """Return the same record from `veriphy.run` as `veriphy layers step <verb>` writes, with the result's fields."""
    result = veriphy.run('echo-operation', 'hello', root=tmp_path)
    assert (result.verb, result.target, result.status, result.outputs, result.level) == (
        'echo-operation',
        'hello',
        'agrees',
        {'text': 'hello'},
        None,
    )
    main(['--root', str(tmp_path), 'layers', 'step', 'echo-operation', 'hello'])
    assert 'echo-operation hello: agrees' in (out := capsys.readouterr().out)
    assert 'replayed: its inputs did not change' in out


def test_help_lists_the_verbs() -> None:
    """List the registered operations with their kind, the programs, and Lean's verbs."""
    text = help_text()
    assert 'echo-operation' in text
    assert 'evidence' in text
    for verb in ('check', 'levels', 'sample', 'claims', 'agents', 'certify', 'translate'):
        assert verb in text


def test_unknown_verb_names_the_operations(tmp_path: Path) -> None:
    """Refuse a verb no step has, naming the operations there are."""
    with pytest.raises(StepError, match='the operations are'):
        veriphy.run('certfy', 'x', root=tmp_path)


def test_programs_run_through_veriphy(capsys: pytest.CaptureFixture[str]) -> None:
    """Run a program's subcommand as `veriphy layers agents …`."""
    main(['layers', 'agents', 'list'])
    assert 'prove.md' in capsys.readouterr().out


def test_one_click_group(tmp_path: Path) -> None:
    """Run every program and operation through one click group, with help generated from each step."""
    assert isinstance(group, click.Group)
    runner = CliRunner()
    shown = runner.invoke(group, ['--root', str(tmp_path), 'layers', 'step', 'sample', '--help'])
    assert shown.exit_code == 0
    assert all(option in shown.output for option in ('--seed', '--values', '--points', '--informal'))
    (tmp_path / 'veriphy.yaml').write_text('version: 1\npacks: [core]\n')
    missing = runner.invoke(group, ['--root', str(tmp_path), 'layers', 'step', 'check', 'x.lean'])
    assert missing.exit_code == 2
    assert runner.invoke(group, ['--root', str(tmp_path), 'config', 'check']).exit_code == 0


def test_old_names_are_unknown(tmp_path: Path) -> None:
    """Fail on a removed verb or module path as on any unknown name."""
    removed = CliRunner().invoke(group, ['--root', str(tmp_path), 'layers', 'step', 'elaborate', 'x.lean'])
    assert (removed.exit_code, 'No such command' in removed.output) == (2, True)
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module('veriphy.toolkit')


def test_layers_config_and_packs(tmp_path: Path) -> None:
    """Group the command as `layers` (one group per layer, in order), `config`, `pack` and `help`, and nothing else."""
    runner = CliRunner()

    def commands(*argv: str) -> list[str]:
        """Return the commands the help of `veriphy --root <tmp> <argv> --help` lists, in its order."""
        shown = runner.invoke(group, ['--root', str(tmp_path), *argv, '--help']).output
        # a command's row starts two spaces in; a description wrapped onto the next line starts further in
        return re.findall(r'^  (\S+)', shown.split('Commands:')[1], re.MULTILINE)

    assert commands() == ['config', 'help', 'layers', 'pack']
    assert commands('layers') == ['primitive', 'step', 'claims', 'workflow', 'agents']
    assert commands('pack') == ['list', 'math']
    assert commands('pack', 'math') == ['certificates', 'translations']
    (tmp_path / 'veriphy.yaml').write_text('version: 1\npacks: [core]\n')
    assert commands('pack') == ['list']


def test_a_step_cannot_take_a_group_command_name(tmp_path: Path) -> None:
    """Refuse a step named as the step group's own commands."""
    (tmp_path / 'veriphy.yaml').write_text(
        "version: 1\npacks: [core]\nsteps:\n  records: {kind: agent, inputs: {artifact: {path: true}}}\n",
    )
    assert any("'records' is the step group's own command" in p for p in check_config(resolve(tmp_path)))


def test_help_aligns_long_step_names_and_shows_lean_only_with_math(tmp_path: Path) -> None:
    """Keep a long step name apart from its kind, and leave out Lean's verbs in a workspace without `math`."""
    (tmp_path / 'veriphy.yaml').write_text('version: 1\npacks: [social-science]\n')
    text = help_text(tmp_path)
    assert re.search(r'check-reliability +evidence', text)
    assert 'In Lean:' not in text
