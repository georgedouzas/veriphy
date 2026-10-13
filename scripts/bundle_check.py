"""Bundle the VeriphyCheck library into one Lean file a project can copy into `.veriphy/lean/`.

The bundle imports mathlib only, so proofs using the checkers build in projects that do not depend on Veriphy, such as
mathlib or Physlib contributions.

Usage: python3 scripts/bundle_check.py [OUTPUT]   (default: dist/VeriphyCheck.lean)
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = re.compile(r'^import (\S+)$', re.MULTILINE)


def _module_path(name: str) -> Path:
    """Return the source file of a `VeriphyCheck` module."""
    return ROOT.joinpath(*name.split('.')).with_suffix('.lean')


def _order(name: str, seen: list[str]) -> None:
    """Append `name` after the `VeriphyCheck` modules it imports, each once."""
    if name in seen:
        return
    for dependency in MODULE.findall(_module_path(name).read_text()):
        if dependency.startswith('VeriphyCheck'):
            _order(dependency, seen)
    seen.append(name)


def bundle() -> str:
    """Return the bundled source: mathlib imports first, then each module's body in dependency order."""
    modules: list[str] = []
    for root_import in MODULE.findall((ROOT / 'VeriphyCheck.lean').read_text()):
        _order(root_import, modules)
    imports: list[str] = []
    bodies: list[str] = []
    for name in modules:
        source = _module_path(name).read_text()
        imports += [i for i in MODULE.findall(source) if not i.startswith('VeriphyCheck') and i not in imports]
        bodies.append(f'/-! ## {name} -/\n\n' + MODULE.sub('', source).strip() + '\n')
    header = '-- VeriphyCheck, bundled by scripts/bundle_check.py from the Veriphy repository; imports mathlib only.\n'
    return header + ''.join(f'import {i}\n' for i in imports) + '\n' + '\n'.join(bodies)


def main() -> None:
    """Write the bundle to the given path."""
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'dist' / 'VeriphyCheck.lean'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(bundle())
    sys.stdout.write(f'wrote {output}\n')


if __name__ == '__main__':
    main()
