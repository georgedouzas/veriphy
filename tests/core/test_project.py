"""Test locating a project's `.veriphy/` directory."""

from pathlib import Path

import pytest

from veriphy.core import PROJECT_DIR_NAME, find_workspace_root, project_dir


@pytest.mark.parametrize('lakefile', ['lakefile.toml', 'lakefile.lean'])
def test_find_workspace_root_from_a_subdirectory(tmp_path: Path, lakefile: str) -> None:
    """Find the root through either lakefile, from a nested subdirectory."""
    (tmp_path / lakefile).write_text('')
    nested = tmp_path / 'Physics' / 'Anomaly'
    nested.mkdir(parents=True)
    assert find_workspace_root(nested) == tmp_path.resolve()


def test_find_workspace_root_prefers_the_nearest_lakefile(tmp_path: Path) -> None:
    """Stop at the nearest workspace, so a nested Lake project has its own `.veriphy/`."""
    (tmp_path / 'lakefile.toml').write_text('')
    inner = tmp_path / 'coverage'
    inner.mkdir()
    (inner / 'lakefile.toml').write_text('')
    assert find_workspace_root(inner) == inner.resolve()


def test_find_workspace_root_without_a_lakefile(tmp_path: Path) -> None:
    """Fall back to the start directory when no ancestor is a workspace."""
    assert find_workspace_root(tmp_path) == tmp_path.resolve()


def test_project_dir_defaults_to_the_working_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Resolve `.veriphy/` from the working directory, without creating it."""
    (tmp_path / 'lakefile.toml').write_text('')
    sub = tmp_path / 'Sub'
    sub.mkdir()
    monkeypatch.chdir(sub)
    assert project_dir() == tmp_path.resolve() / PROJECT_DIR_NAME
    assert not (tmp_path / PROJECT_DIR_NAME).exists()
