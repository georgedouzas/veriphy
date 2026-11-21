"""Test the reproduction pack: a field with no proofs, its primitives, steps, levels and workflow, and no Lean."""

import json
import re
import shutil
from pathlib import Path

import pytest

from veriphy.__main__ import LAYERS
from veriphy.claims import shown_level
from veriphy.core import check_config, level_order, level_trust, resolve
from veriphy.primitives import load_registry
from veriphy.primitives._contracts import container_runtime
from veriphy.steps import load_steps, run_step

EXAMPLE = Path(__file__).resolve().parents[2] / 'src' / 'veriphy' / 'packs' / 'reproduction' / 'example'
CLAIM = json.loads((EXAMPLE / 'claim.json').read_text())
CLAIM_IMAGE = 'rocker/r-ver:4.4.1@sha256:78cb94ce2db23aaaf7b546450fcf70b5a3f2ace5a9b5fa1f87217da329211312'
needs_r = pytest.mark.skipif(container_runtime() is None, reason='needs podman or docker for the pinned R image')


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Return a workspace of the reproduction pack alone, with the example's script, data and claim."""
    for name in ('analysis.R', 'mtcars.csv', 'claim.json'):
        shutil.copyfile(EXAMPLE / name, tmp_path / name)
    (tmp_path / 'veriphy.yaml').write_text('version: 1\npacks: [reproduction]\n')
    return tmp_path


def _inputs(**extra: object) -> dict[str, object]:
    """Return the example claim's inputs to a step."""
    return {
        'script': CLAIM['script'],
        'data': CLAIM['data'],
        'sha256': CLAIM['sha256'],
        'claim': CLAIM['claim'],
        **extra,
    }


def test_selecting_the_pack(workspace: Path) -> None:
    """List the pack's tool, primitives, steps, levels and workflow, and nothing of Lean or SageMath."""
    resolved = resolve(workspace)
    assert check_config(resolved) == []
    assert [p.name for p in resolved.packs] == ['core', 'reproduction']
    assert resolved.section('tools')['r']['pin'] == {'image': CLAIM_IMAGE}
    registry = load_registry(resolved=resolved)
    assert {'r.exec', 'r.run', 'r.robustness'} <= set(registry.primitives)
    assert not any(name.startswith(('sage.', 'lean.')) for name in registry.primitives)
    assert {'reproduce', 'vary'} <= set(load_steps(workspace))
    assert level_order(resolved) == ('none', 'reproduced', 'robust')
    assert 'reproduce-analysis' in resolved.section('workflows')


def test_wrong_data_is_refused_before_r_runs(workspace: Path) -> None:
    """Refuse data whose digest differs from the claim's, naming both, without starting R."""
    (workspace / 'mtcars.csv').write_text((workspace / 'mtcars.csv').read_text() + '1,2,3,4,5,6,7,8,9,10,11\n')
    record = run_step(load_steps(workspace)['reproduce'], workspace, _inputs(claimed=CLAIM['estimate'])).record
    assert (record.status, record.level) == ('refused', None)
    assert CLAIM['sha256'] in str(record.outputs['error'])
    assert 'r' not in record.tools


@needs_r
def test_the_example_reproduces(workspace: Path) -> None:
    """Reproduce the example's estimate in the pinned image, granting `reproduced`, with both estimates recorded."""
    record = run_step(load_steps(workspace)['reproduce'], workspace, _inputs(claimed=CLAIM['estimate'])).record
    assert (record.status, record.level) == ('agrees', 'reproduced')
    assert record.outputs['compared']['claimed'] == CLAIM['estimate']
    assert abs(float(record.outputs['estimate']) - CLAIM['estimate']) < 1e-6
    assert record.tools['r'] == CLAIM_IMAGE
    assert shown_level('reproduced', level_trust(resolve(workspace))) == 'reproduced (reproduction)'


@needs_r
def test_a_differing_estimate_grants_nothing(workspace: Path) -> None:
    """Record both estimates and grant nothing when the claim reports another estimate."""
    record = run_step(load_steps(workspace)['reproduce'], workspace, _inputs(claimed=-4.0)).record
    assert (record.status, record.level, record.outputs['claimed']) == ('differs', None, -4.0)


@needs_r
def test_robust_and_fragile(workspace: Path) -> None:
    """Grant `robust` when every declared variation holds, and name the one that flips the sign otherwise."""
    step = load_steps(workspace)['vary']
    robust = run_step(step, workspace, _inputs(variations=CLAIM['variations'])).record
    assert (robust.status, robust.level) == ('robust', 'robust')
    fragile = run_step(step, workspace, _inputs(variations=['mpg ~ wt + hp', 'hp ~ wt'])).record
    assert (fragile.status, fragile.level, fragile.outputs['breaking']) == ('fragile', None, ['hp ~ wt'])


def test_the_playbook_names_real_commands(workspace: Path) -> None:
    """Name only the steps and programs a workspace of the reproduction pack has, and say levels with their class."""
    text = (EXAMPLE.parent / 'agents' / 'reproduce.md').read_text()
    named = set(re.findall(r'(?<![#\w.-])veriphy layers step ([a-z]+)', text))
    assert named <= {*load_steps(workspace), 'list', 'records'}
    assert set(re.findall(r'(?<![#\w.-])veriphy ([a-z]+)', text)) <= {'layers', 'config', 'pack', 'help'}
    assert set(re.findall(r'(?<![#\w.-])veriphy layers ([a-z]+)', text)) <= set(LAYERS)
    assert 'reproduced (reproduction)' in text
