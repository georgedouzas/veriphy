"""Locate a downstream project's `.veriphy/` directory, where every Veriphy artifact of the project lives."""

from pathlib import Path

PROJECT_DIR_NAME = '.veriphy'
LAKEFILES = ('lakefile.toml', 'lakefile.lean')
# what marks a workspace root: a Lean workspace's lakefile, or a workspace file, as a workspace without Lean has
MARKERS = ('veriphy.yaml', *LAKEFILES)


def find_workspace_root(start: Path | None = None) -> Path:
    """Return the workspace root: the nearest directory, from `start` upwards, holding `veriphy.yaml` or a lakefile.

    Args:
        start: The directory to search from, the working directory when `None`.

    Returns:
        The workspace root, or `start` itself when no ancestor holds either.

    Examples:
        >>> import tempfile
        >>> with tempfile.TemporaryDirectory() as tmp:
        ...     root = Path(tmp).resolve()
        ...     _ = (root / 'lakefile.toml').write_text('')
        ...     (root / 'Sub' / 'Dir').mkdir(parents=True)
        ...     find_workspace_root(root / 'Sub' / 'Dir') == root
        True
    """
    origin = (start or Path.cwd()).resolve()
    for directory in (origin, *origin.parents):
        if any((directory / name).is_file() for name in MARKERS):
            return directory
    return origin


def project_dir(root: Path | None = None) -> Path:
    """Return the project's `.veriphy/` directory, without creating it.

    Args:
        root: The workspace root, found from the working directory when `None`.

    Returns:
        The path of `.veriphy/` under the workspace root.

    Examples:
        >>> project_dir(Path('/work/project')).as_posix()
        '/work/project/.veriphy'
    """
    return (root if root is not None else find_workspace_root()) / PROJECT_DIR_NAME
