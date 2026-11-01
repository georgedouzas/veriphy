"""Test finding and building `oo-horn`, installing the reasoner, and the built-in rule table."""

import stat
from pathlib import Path

import pytest

from veriphy.core import CheckerError
from veriphy.graph import build_checker, builtin_rules, cache_dir, find_checker, load_graph, reason

FAKE_TOOL = """#!/bin/sh
echo "$0 $*" >> "{log}"
case "$1" in
  clone) /bin/mkdir -p "$8/.git" "$8/python" "$8/lean/.lake/build/bin" ;;
  rev-parse) echo 0123abcd ;;
esac
"""


def _fake_tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, names: tuple[str, ...]) -> Path:
    """Put fake tools on PATH that log their arguments, and return the log."""
    bin_dir, log = tmp_path / 'bin', tmp_path / 'calls.log'
    bin_dir.mkdir()
    for name in names:
        tool = bin_dir / name
        tool.write_text(FAKE_TOOL.format(log=log))
        tool.chmod(tool.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv('PATH', str(bin_dir))
    return log


def test_cache_dir_follows_xdg() -> None:
    """Place the release under XDG_CACHE_HOME, at the pinned tag."""
    assert cache_dir({'XDG_CACHE_HOME': '/c'}) == Path('/c/veriphy/open-ontologies/v2.1.0')


def test_find_checker_prefers_the_explicit_path(tmp_path: Path) -> None:
    """Use the path VERIPHY_OO_HORN names, and never replace it with the cache."""
    binary = tmp_path / 'oo-horn'
    binary.write_text('')
    binary.chmod(0o755)
    assert find_checker({'VERIPHY_OO_HORN': str(binary), 'XDG_CACHE_HOME': str(tmp_path)}).path == binary
    missing = find_checker({'VERIPHY_OO_HORN': str(tmp_path / 'none'), 'XDG_CACHE_HOME': str(tmp_path)})
    assert (missing.path, missing.searched) == (None, (tmp_path / 'none',))


def test_build_checker_clones_builds_and_installs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Clone the pinned tag into the cache, build oo-horn there, and install the release's reasoner."""
    log = _fake_tools(tmp_path, monkeypatch, ('git', 'lake', 'uv'))
    report = build_checker(environ={'XDG_CACHE_HOME': str(tmp_path / 'cache')})
    directory = tmp_path / 'cache' / 'veriphy' / 'open-ontologies' / 'v2.1.0'
    calls = log.read_text()
    assert '--branch v2.1.0 https://github.com/fabio-rovai/open-ontologies' in calls
    assert 'pip install --python' in calls
    assert str(directory / 'python') in calls
    assert 'lake build oo-horn' in calls
    assert (report.tag, report.commit, report.checker) == (
        'v2.1.0',
        '0123abcd',
        directory / 'lean/.lake/build/bin/oo-horn',
    )


def test_build_checker_reasoner_only_skips_lake(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Install the reasoner without building the checker."""
    log = _fake_tools(tmp_path, monkeypatch, ('git', 'uv'))
    report = build_checker(reasoner_only=True, environ={'XDG_CACHE_HOME': str(tmp_path / 'cache')})
    assert report.checker is None
    assert 'lake' not in log.read_text()


def test_build_checker_names_a_missing_tool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Name the tool that is not on PATH."""
    _fake_tools(tmp_path, monkeypatch, ())
    with pytest.raises(CheckerError, match='`git` is not on PATH'):
        build_checker(environ={'XDG_CACHE_HOME': str(tmp_path / 'cache')})


def test_builtin_rules_match_the_reasoner(workspace: Path, checker: Path) -> None:
    """Fail when the reasoner's built-in table drifts from the checker's."""
    run = reason(load_graph(workspace), checker)
    assert (run.directory / 'rules.tsv').read_text() == builtin_rules(checker)
    assert run.report.get('rules_digest') == run.report.get('builtin_rules_digest')
