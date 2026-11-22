"""Find Veriphy's packs and read their `pack.yaml`: Veriphy's own, then those installed under `veriphy.packs`."""

import importlib
from importlib.metadata import entry_points
from importlib.resources import files
from pathlib import Path

import yaml

from veriphy.core._errors import PackError

# Veriphy's own packs; others register under the `veriphy.packs` entry point, naming their package
BUILTIN_PACKS = (
    'core',
    'math',
    'statistics',
    'social-science',
    'economics',
    'physics',
    'life-sciences',
    'chemistry',
    'particle-physics',
    'general-relativity',
    'genomics',
    'econometrics',
    'epidemiology',
)
PACK_FILE = 'pack.yaml'


def pack_packages() -> dict[str, str]:
    """Return each pack's name and package: Veriphy's own, then those under the `veriphy.packs` entry point.

    Returns:
        The packs, in the order they are found.

    Examples:
        >>> list(pack_packages())[:3]
        ['core', 'math', 'statistics']
    """
    # a pack's name may hold a dash, its package an underscore
    packages = {name: f"veriphy.packs.{name.replace('-', '_')}" for name in BUILTIN_PACKS}
    for entry in entry_points(group='veriphy.packs'):
        packages.setdefault(entry.name, entry.value)
    return packages


def pack_dir(package: str) -> Path:
    """Return the directory of a pack's package, where its `pack.yaml` and schemas live.

    Args:
        package: The pack's package, as `veriphy.packs.math`.

    Returns:
        The directory.

    Raises:
        PackError: If the package does not import.
    """
    try:
        importlib.import_module(package)
    except ModuleNotFoundError as exc:
        message = f"no pack package '{package}': install it, or remove it from the packs"
        raise PackError(message) from exc
    return Path(str(files(package)))


def read_pack(package: str) -> dict[str, object]:
    """Return a pack's `pack.yaml` as a mapping, empty when the pack has none.

    Args:
        package: The pack's package.

    Returns:
        The declarations.

    Raises:
        PackError: If the file is not a YAML mapping.
    """
    path = pack_dir(package) / PACK_FILE
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        message = f'{path} does not read as YAML: {exc}'
        raise PackError(message) from exc
    if not isinstance(data, dict):
        message = f'{path} must be a mapping of declarations, as `version: 1` and `primitives: {{...}}`'
        raise PackError(message)
    return data
