"""Keep the steps that layers and packs register, and load every pack's registrations by name."""

import importlib
from importlib.metadata import entry_points

from veriphy.core import StepError
from veriphy.steps._runner import Step

# Veriphy's own packs; others register under the `veriphy.packs` entry point, naming their package
BUILTIN_PACKS = ('core', 'lean', 'math')
LAYERS = ('primitives', 'steps', 'claims', 'workflows', 'agents')
_STEPS: dict[str, Step] = {}


def register(*steps: Step) -> None:
    """Add steps to the registry.

    Args:
        *steps: The steps. Registering the same step again is harmless.

    Raises:
        StepError: If another step already has the name.

    Examples:
        >>> from veriphy.steps._runner import Outcome, Prepared
        >>> echo = Step('echo-doctest', 'evidence', lambda root, p: Prepared({}), lambda root, p, q: Outcome('ok'))
        >>> register(echo)
        >>> register(echo)
        >>> 'echo-doctest' in registered()
        True
    """
    for step in steps:
        known = _STEPS.get(step.name)
        if known is not None and known is not step:
            message = f"two steps are named '{step.name}': rename one of them"
            raise StepError(message)
        _STEPS[step.name] = step


def registered() -> dict[str, Step]:
    """Return the registered steps, by name, without loading any pack."""
    return dict(_STEPS)


def pack_packages() -> dict[str, str]:
    """Return each pack's name and package: Veriphy's own, then those under the `veriphy.packs` entry point."""
    packages = {name: f'veriphy.packs.{name}' for name in BUILTIN_PACKS}
    for entry in entry_points(group='veriphy.packs'):
        packages.setdefault(entry.name, entry.value)
    return packages


def _import_layer(package: str, layer: str) -> None:
    """Import a pack's layer subpackage, so it registers its steps; a pack without that layer is skipped."""
    module = f'{package}.{layer}'
    try:
        importlib.import_module(module)
    except ModuleNotFoundError as exc:
        if exc.name not in {module, package}:
            raise


def load_steps() -> dict[str, Step]:
    """Import every pack's layer subpackages, so each registers its steps, and return the registry.

    Returns:
        Every step, by name.
    """
    for package in pack_packages().values():
        for layer in LAYERS:
            _import_layer(package, layer)
    return registered()
