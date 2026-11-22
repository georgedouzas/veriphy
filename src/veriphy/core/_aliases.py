"""Re-export a module under another name, as a facade over it."""

import importlib
import sys


def reexport(name: str, target: str) -> None:
    """Make the module `name` expose the public names of `target`, as a facade over it.

    Args:
        name: The facade's name, its `__name__`.
        target: The module whose names it exposes.
    """
    module = importlib.import_module(target)
    facade = sys.modules[name]
    public = getattr(module, '__all__', [n for n in vars(module) if not n.startswith('_')])
    for key in public:
        setattr(facade, key, getattr(module, key))
    vars(facade)['__all__'] = list(public)
