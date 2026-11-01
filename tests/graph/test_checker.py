"""Test setting up `oo-horn` and the reasoner from a release, on first use and on demand, and the rule table."""

import dataclasses
import hashlib
from pathlib import Path

import pytest

from veriphy.core import CheckerError, GraphExtraMissingError
from veriphy.graph import (
    Release,
    build_checker,
    builtin_rules,
    cache_dir,
    ensure_checker,
    ensure_reasoner,
    ensure_release,
    find_checker,
    load_graph,
    reason,
)


def _environ(tmp_path: Path, **extra: str) -> dict[str, str]:
    """Return an environment whose cache is under the test directory."""
    return {'XDG_CACHE_HOME': str(tmp_path / 'cache'), **extra}


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
    assert (missing.path, missing.searched, missing.explicit) == (None, (tmp_path / 'none',), True)


def test_ensure_release_fetches_once(tmp_path: Path, fake_release: Release) -> None:
    """Fetch the release on first use, report it, and fetch nothing the second time."""
    messages: list[str] = []
    directory, commit = ensure_release(environ=_environ(tmp_path), release=fake_release, notify=messages.append)
    ensure_release(environ=_environ(tmp_path), release=fake_release, notify=messages.append)
    assert commit == fake_release.commit
    assert (directory / 'python' / 'src' / 'open_ontologies_lite').is_dir()
    assert len(messages) == 1
    assert messages[0].startswith('Fetching Open Ontologies v-test')


def test_ensure_release_refuses_a_moved_tag(tmp_path: Path, fake_release: Release) -> None:
    """Refuse a release whose tag points to another commit than the pinned one, and keep nothing."""
    pinned = dataclasses.replace(fake_release, commit='0' * 40)
    with pytest.raises(CheckerError, match=f'points to commit {fake_release.commit}, and Veriphy pins {"0" * 40}'):
        ensure_release(environ=_environ(tmp_path), release=pinned, notify=lambda _: None)
    assert not cache_dir(_environ(tmp_path), pinned).exists()


def test_ensure_reasoner_returns_the_cached_source(tmp_path: Path, fake_release: Release) -> None:
    """Return the release's source directory, installing nothing."""
    source = ensure_reasoner(environ=_environ(tmp_path), release=fake_release, notify=lambda _: None)
    assert source == cache_dir(_environ(tmp_path), fake_release) / 'python' / 'src'
    assert (source / 'open_ontologies_lite' / 'horn').is_dir()


def test_ensure_reasoner_with_setup_off_names_the_command(tmp_path: Path, fake_release: Release) -> None:
    """Refuse to fetch when setup is off, and name the setup command."""
    environ = _environ(tmp_path, VERIPHY_GRAPH_SETUP='off')
    with pytest.raises(GraphExtraMissingError, match='checker build'):
        ensure_reasoner(environ=environ, release=fake_release, notify=lambda _: None)
    assert not cache_dir(environ, fake_release).exists()


def test_ensure_checker_keeps_a_verified_prebuilt_binary(tmp_path: Path, fake_release: Release) -> None:
    """Download the prebuilt checker, check both hashes and that it runs, and find it afterwards."""
    messages: list[str] = []
    path = ensure_checker(environ=_environ(tmp_path), release=fake_release, notify=messages.append, prebuilt=True)
    assert path == cache_dir(_environ(tmp_path), fake_release) / 'bin' / 'oo-horn'
    assert find_checker(_environ(tmp_path), fake_release).path == path
    assert any('Downloading the prebuilt oo-horn' in m for m in messages)


def test_ensure_checker_refuses_a_tampered_binary(tmp_path: Path, fake_release: Release) -> None:
    """Refuse a binary whose hash is not the pinned one, naming both hashes, and keep nothing."""
    pinned = dataclasses.replace(fake_release, prebuilt_sha256='f' * 64)
    expected = f'while Veriphy pins {"f" * 64} and the release lists {fake_release.prebuilt_sha256}'
    with pytest.raises(CheckerError, match=expected):
        ensure_checker(environ=_environ(tmp_path), release=pinned, notify=lambda _: None, prebuilt=True)
    assert not (cache_dir(_environ(tmp_path), pinned) / 'bin' / 'oo-horn').exists()


def test_ensure_checker_builds_when_the_prebuilt_does_not_run(
    tmp_path: Path,
    fake_release: Release,
    fake_lake: Path,
) -> None:
    """Delete a prebuilt binary that does not run here, and build the checker instead."""
    assets = Path(fake_release.assets.removeprefix('file://'))
    broken = assets / 'oo-horn-broken'
    broken.write_text('#!/bin/sh\nexit 9\n')
    broken.chmod(0o755)
    digest = hashlib.sha256(broken.read_bytes()).hexdigest()
    (assets / 'SHASUMS.txt').write_text(f'{digest}  oo-horn-broken\n')
    release = dataclasses.replace(fake_release, prebuilt='oo-horn-broken', prebuilt_sha256=digest)
    messages: list[str] = []
    path = ensure_checker(environ=_environ(tmp_path), release=release, notify=messages.append, prebuilt=True)
    assert path == cache_dir(_environ(tmp_path), release) / 'lean' / '.lake' / 'build' / 'bin' / 'oo-horn'
    assert 'build oo-horn' in fake_lake.read_text()
    assert any('does not run on this machine' in m for m in messages)


def test_ensure_checker_with_setup_off_fetches_nothing(tmp_path: Path, fake_release: Release) -> None:
    """Refuse to set up the checker when setup is off, and fetch nothing."""
    environ = _environ(tmp_path, VERIPHY_GRAPH_SETUP='off')
    with pytest.raises(CheckerError, match='VERIPHY_GRAPH_SETUP is off'):
        ensure_checker(environ=environ, release=fake_release, notify=lambda _: None)
    assert not cache_dir(environ, fake_release).exists()


def test_build_checker_sets_up_whatever_the_setup_variable(
    tmp_path: Path,
    fake_release: Release,
    fake_lake: Path,
) -> None:
    """Fetch and build on demand even when automatic setup is off, and report the commit."""
    environ = _environ(tmp_path, VERIPHY_GRAPH_SETUP='off')
    report = build_checker(environ=environ, release=fake_release, notify=lambda _: None, prebuilt=False)
    assert (report.tag, report.commit) == ('v-test', fake_release.commit)
    assert report.checker is not None
    assert report.checker.is_file()
    assert fake_lake.read_text().strip() == 'build oo-horn'


def test_build_checker_reasoner_only_skips_the_checker(tmp_path: Path, fake_release: Release) -> None:
    """Fetch the release without setting up the checker."""
    report = build_checker(reasoner_only=True, environ=_environ(tmp_path), release=fake_release, notify=lambda _: None)
    assert report.checker is None
    assert report.reasoner.is_dir()


def test_builtin_rules_match_the_reasoner(workspace: Path, checker: Path) -> None:
    """Fail when the reasoner's built-in table drifts from the checker's."""
    run = reason(load_graph(workspace), checker)
    assert (run.directory / 'rules.tsv').read_text() == builtin_rules(checker)
    assert run.report.get('rules_digest') == run.report.get('builtin_rules_digest')
