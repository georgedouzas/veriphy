"""Keep the steps that layers and packs register, and load every pack's registrations by name."""

import importlib
import warnings

from veriphy.core import StepError, pack_packages
from veriphy.steps._runner import Step

LAYERS = ('primitives', 'steps', 'claims', 'workflows', 'agents')
_STEPS: dict[str, Step] = {}
# old step names, kept for one minor release
DEPRECATED_VERBS = {'elaborate': 'check'}


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


def resolve_verb(verb: str) -> str:
    """Return the step name a verb denotes, warning when it is a deprecated name.

    Args:
        verb: The verb, as the caller wrote it.

    Returns:
        The step's name.

    Examples:
        >>> resolve_verb('check')
        'check'
    """
    new = DEPRECATED_VERBS.get(verb)
    if new is None:
        return verb
    message = f"the verb '{verb}' is now '{new}'; the old name goes in the next minor release"
    warnings.warn(message, DeprecationWarning, 2)
    return new


def registered() -> dict[str, Step]:
    """Return the registered steps, by name, without loading any pack."""
    return dict(_STEPS)


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
