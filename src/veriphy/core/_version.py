"""Read the installed version of veriphy."""

from importlib.metadata import PackageNotFoundError, version


def _read_version() -> str:
    """Return the installed distribution version, or `0+unknown` for an uninstalled checkout."""
    try:
        return version('veriphy')
    except PackageNotFoundError:
        return '0+unknown'


__version__ = _read_version()
