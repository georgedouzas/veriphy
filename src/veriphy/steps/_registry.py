"""Keep the steps that layers and packs register, and load every pack's registrations by name."""

import importlib
import warnings
from pathlib import Path

from veriphy.core import StepError, installed, resolve
from veriphy.steps._runner import Step

LAYERS = ('primitives', 'steps', 'claims', 'workflows', 'agents')
_STEPS: dict[str, Step] = {}
# the pack that registered each step; a step of no pack is always available
_OWNERS: dict[str, str] = {}
# old step names, kept for one minor release
DEPRECATED_VERBS = {'elaborate': 'check'}


def register(*steps: Step, pack: str = '') -> None:
    """Add steps to the registry.

    Args:
        *steps: The steps. Registering the same step again is harmless.
        pack: The pack that defines them, so a workspace that does not select it does not see them.

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
        _OWNERS[step.name] = pack


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


def load_steps(root: Path | None = None) -> dict[str, Step]:
    """Import the selected packs' layer subpackages, so each registers its steps, and return their steps.

    Args:
        root: The workspace whose `veriphy.yaml` selects the packs; every installed pack when `None`.

    Returns:
        The selected packs' steps, by name.
    """
    config = resolve(root) if root is not None else installed()
    selected = {pack.name for pack in config.packs}
    for pack in config.packs:
        if pack.package is None:
            continue
        for layer in LAYERS:
            _import_layer(pack.package, layer)
    return {name: step for name, step in _STEPS.items() if _OWNERS.get(name) in selected or not _OWNERS.get(name)}
