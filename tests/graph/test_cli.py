"""Test the command line of the research graph and its parity with the Python API."""

from collections.abc import Callable
from pathlib import Path

import pytest

import veriphy.claims
from veriphy.__main__ import main as veriphy_main
from veriphy.claims import COMMANDS


def main(argv: list[str]) -> None:
    """Run `veriphy layers claims` with the arguments."""
    veriphy_main(['layers', 'claims', *argv])


def step(workspace: Path, argv: list[str]) -> None:
    """Run `veriphy layers step` in a workspace with the arguments."""
    veriphy_main(['--root', str(workspace), 'layers', 'step', *argv])


def test_main_commands_reach_the_api() -> None:
    """Map every command to a function of the public API."""
    assert set(COMMANDS) >= {'levels', 'impact', 'plan', 'slice', 'clashes', 'checker'}
    assert not {'validate', 'reason', 'appendix'} & set(COMMANDS)
    assert all(name in veriphy.claims.__all__ for name in COMMANDS.values())


def test_main_reason_exits_three_when_unchecked(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Exit with status 3 and say how to build the checker when it is missing."""
    monkeypatch.setenv('VERIPHY_OO_HORN', str(workspace / 'none'))
    with pytest.raises(SystemExit) as exc:
        step(workspace, ['reason'])
    assert exc.value.code == 3
    assert 'to fix: set up the checker with `veriphy layers claims checker build`' in capsys.readouterr().out


def test_main_appendix_writes_the_file(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_checker: Callable[[str], Path],
) -> None:
    """Write the appendix under `.veriphy/graph/appendix/`."""
    monkeypatch.setenv('VERIPHY_OO_HORN', str(fake_checker('accepted')))
    step(workspace, ['appendix', 'chapter9', '--format', 'latex'])
    assert (workspace / '.veriphy' / 'graph' / 'appendix' / 'chapter9.tex').is_file()


def test_main_confirm_and_validate(workspace: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Confirm a triple by short names, then validate the graph."""
    main(['--root', str(workspace), 'confirm', 'chapter9', 'lemma-5.2', 'assumes', 'half'])
    assert (workspace / '.veriphy' / 'graph' / 'sources' / 'chapter9.human.ttl').is_file()
    step(workspace, ['validate'])
    assert 'validate: conforms' in capsys.readouterr().out


def test_main_reports_a_graph_error(workspace: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Exit with status 1 and print the error."""
    with pytest.raises(SystemExit) as exc:
        main(['--root', str(workspace), 'confirm', 'chapter9', 'eq-4.1', 'uses', 'thm-9.1'])
    assert exc.value.code == 1
    assert 'does not assert' in capsys.readouterr().err


@pytest.mark.parametrize(
    'case',
    [
        (['levels', '--source', 'chapter9'], '| thm-9.1 | certificate (kernel) | oracle-test (oracle) |'),
        (['impact', 'chapter9', 'half'], '- eq-7.3 via lemma-5.2'),
        (['slice', 'chapter9', 'thm-9.1'], '# Context for thm-9.1'),
        (['clashes'], 'No clash'),
        (['excludes'], 'half excludes one'),
        (['axioms'], '<urn:veriphy:axiom:'),
        (['vocabulary'], 'vp:Claim a owl:Class'),
    ],
)
def test_main_read_commands_print_reports(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_checker: Callable[[str], Path],
    capsys: pytest.CaptureFixture[str],
    case: tuple[list[str], str],
) -> None:
    """Print each read command's report."""
    args, expected = case
    monkeypatch.setenv('VERIPHY_OO_HORN', str(fake_checker('accepted')))
    main(['--root', str(workspace), *args])
    assert expected in capsys.readouterr().out


def test_main_recheck_and_checker_path(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_checker: Callable[[str], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Recheck a stored run against the current graph, and print the checker's path."""
    checker = fake_checker('accepted')
    monkeypatch.setenv('VERIPHY_OO_HORN', str(checker))
    step(workspace, ['reason'])
    run = next((workspace / '.veriphy' / 'graph' / 'runs').iterdir())
    main(['--root', str(workspace), 'recheck', str(run)])
    main(['checker', 'path'])
    out = capsys.readouterr().out
    assert 'the current graph asserts the same triples' in out
    assert out.rstrip().endswith(str(checker))


def test_main_excludes_confirm_writes_human_triples(
    workspace: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Write the proposed triples to the human file of the convention's source."""
    main(['--root', str(workspace), 'excludes', '--confirm'])
    assert 'wrote 1 triples' in capsys.readouterr().out
    assert 'vp:excludes' in (workspace / '.veriphy' / 'graph' / 'sources' / 'chapter9.human.ttl').read_text()


def test_reason_refuses_a_rejected_run(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_checker: Callable[[str], Path],
) -> None:
    """Exit with status 1 when the checker rejects the run, as a refusal."""
    monkeypatch.setenv('VERIPHY_OO_HORN', str(fake_checker('rejected')))
    with pytest.raises(SystemExit) as exc:
        step(workspace, ['reason'])
    assert exc.value.code == 1
