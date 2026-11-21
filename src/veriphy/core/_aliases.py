"""Re-export a module under another name: a facade over it, or an old path that warns it moved."""

import importlib
import runpy
import sys
import warnings


def alias(name: str, target: str) -> None:
    """Make the module `name` expose the public names of `target`, warning once that it moved.

    Args:
        name: The old module's name, its `__name__`.
        target: The module it moved to.
    """
    warnings.warn(f'{name} moved to {target}; the old path goes in the next minor release', DeprecationWarning, 3)
    reexport(name, target)


def reexport(name: str, target: str) -> None:
    """Make the module `name` expose the public names of `target`, as a facade over it.

    Args:
        name: The facade's name, its `__name__`.
        target: The module whose names it exposes.
    """
    module = importlib.import_module(target)
    old = sys.modules[name]
    public = getattr(module, '__all__', [n for n in vars(module) if not n.startswith('_')])
    for key in public:
        setattr(old, key, getattr(module, key))
    vars(old)['__all__'] = list(public)


def run_alias(target: str) -> None:
    """Run the program of the module an old program moved to, as `python -m <target>` would.

    Args:
        target: The module whose `__main__` runs.
    """
    warnings.warn(f'this program moved to python -m {target}', DeprecationWarning, 2)
    runpy.run_module(target, run_name='__main__', alter_sys=True)
