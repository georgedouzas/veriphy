"""Test the deprecated module paths: each exposes its new module's public names, warns once, and runs its program."""

import importlib
import sys

import pytest

import veriphy.core
from veriphy.core import run_process
from veriphy.steps import RecordStore

ALIASES = {
    'veriphy.oracle': 'veriphy.packs.math.primitives.sage.methods',
    'veriphy.sage_server': 'veriphy.packs.math.primitives.sage',
    'veriphy.toolkit': 'veriphy.script',
    'veriphy.translations': 'veriphy.packs.math.primitives.translations',
    'veriphy.certificates': 'veriphy.packs.math.steps.certificates',
    'veriphy.graph': 'veriphy.claims',
    'veriphy.prompts': 'veriphy.agents',
}
PROGRAMS = ['veriphy.graph', 'veriphy.prompts', 'veriphy.certificates', 'veriphy.translations']


@pytest.mark.parametrize(('old', 'new'), ALIASES.items())
def test_alias_exposes_its_target(old: str, new: str) -> None:
    """Expose the same public names, the same objects, as the module the path moved to, and warn that it moved."""
    sys.modules.pop(old, None)
    with pytest.warns(DeprecationWarning, match=new.replace('.', r'\.')):
        module = importlib.import_module(old)
    target = importlib.import_module(new)
    assert module.__all__
    assert all(getattr(module, name) is getattr(target, name) for name in module.__all__)


def test_records_moved_out_of_core() -> None:
    """Keep `veriphy.core.RecordStore` working, warning that it moved to `veriphy.steps`."""
    with pytest.warns(DeprecationWarning, match=r'veriphy\.steps\.RecordStore'):
        moved = veriphy.core.RecordStore
    assert moved is RecordStore


@pytest.mark.parametrize('program', PROGRAMS)
def test_old_program_runs(program: str) -> None:
    """Run the new program when the old one is called, as `python -m <old> --help`."""
    code, out, err = run_process([sys.executable, '-m', program, '--help'])
    assert code == 0, err
    assert 'usage' in out.lower()
