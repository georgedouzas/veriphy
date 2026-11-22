"""Test the social-science pack: its steps, levels and workflow on the example study, its concepts, and no Lean."""

import json
import re
import shutil
from pathlib import Path

import pytest

from veriphy.__main__ import LAYERS
from veriphy.claims import add_triples, clashes, label_of, load_graph, propose_excludes, reason, shown_level, source_of
from veriphy.core import check_config, level_order, level_trust, resolve
from veriphy.primitives import load_registry
from veriphy.steps import load_steps, run_step

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / 'docs' / 'examples' / 'social-science'
PLAYBOOK = ROOT / 'src' / 'veriphy' / 'packs' / 'social_science' / 'agents' / 'reproduce.md'
CLAIM = json.loads((EXAMPLE / 'claim.json').read_text())


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Return a workspace of the social-science pack alone, with the example's script, data and claim."""
    for name in ('analysis.py', 'survey.csv', 'claim.json', 'thesaurus.ttl'):
        shutil.copyfile(EXAMPLE / name, tmp_path / name)
    sources = tmp_path / '.veriphy' / 'graph' / 'sources'
    sources.mkdir(parents=True)
    shutil.copyfile(EXAMPLE / 'chapter3.agent.ttl', sources / 'chapter3.agent.ttl')
    (tmp_path / 'veriphy.yaml').write_text('version: 1\npacks: [social-science]\n')
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
    assert [p.name for p in resolved.packs] == ['core', 'social-science']
    registry = load_registry(resolved=resolved)
    assert registry.tools['python'].run[1].endswith('social_science/primitives/runner.py')
    assert {'analysis.exec', 'analysis.run', 'analysis.robustness'} <= set(registry.primitives)
    assert not any(name.startswith(('sage.', 'lean.')) for name in registry.primitives)
    assert {'reproduce', 'robustness', 'check-concepts'} <= set(load_steps(workspace))
    assert level_order(resolved) == ('none', 'reproduced', 'robust')
    assert 'reproduce-analysis' in resolved.section('workflows')


def test_wrong_data_is_refused_before_the_analysis_runs(workspace: Path) -> None:
    """Refuse data whose digest differs from the claim's, naming both, without running the analysis."""
    (workspace / 'survey.csv').write_text((workspace / 'survey.csv').read_text() + '201,12,40,50,3,3,3,3,1\n')
    record = run_step(load_steps(workspace)['reproduce'], workspace, _inputs(claimed=CLAIM['estimate'])).record
    assert (record.status, record.level) == ('refused', None)
    assert CLAIM['sha256'] in str(record.outputs['error'])
    assert 'python' not in record.tools


def test_the_example_reproduces(workspace: Path) -> None:
    """Reproduce the example's estimate, granting `reproduced`, with both estimates and the data's digest recorded."""
    record = run_step(load_steps(workspace)['reproduce'], workspace, _inputs(claimed=CLAIM['estimate'])).record
    assert (record.status, record.level) == ('agrees', 'reproduced')
    assert record.outputs['compared']['claimed'] == CLAIM['estimate']
    assert abs(float(record.outputs['estimate']) - CLAIM['estimate']) <= record.outputs['compared']['tolerance']
    assert record.outputs['sha256'] == CLAIM['sha256']
    assert record.tools['python'].count('.') == 2
    assert shown_level('reproduced', level_trust(resolve(workspace))) == 'reproduced (reproduction)'


def test_a_differing_estimate_grants_nothing(workspace: Path) -> None:
    """Record both estimates and grant nothing when the claim reports another estimate."""
    record = run_step(load_steps(workspace)['reproduce'], workspace, _inputs(claimed=0.2)).record
    assert (record.status, record.level, record.outputs['claimed']) == ('differs', None, 0.2)


def test_robust_and_fragile(workspace: Path) -> None:
    """Grant `robust` when every declared variation holds, and name the one that flips the sign otherwise."""
    step = load_steps(workspace)['robustness']
    robust = run_step(step, workspace, _inputs(variations=CLAIM['variations'])).record
    assert (robust.status, robust.level) == ('robust', 'robust')
    unrelated = 'age ~ education_years'
    fragile = run_step(step, workspace, _inputs(variations=[CLAIM['variations'][0], unrelated])).record
    assert (fragile.status, fragile.level, fragile.outputs['breaking']) == ('fragile', None, [unrelated])


def test_the_playbook_names_real_commands(workspace: Path) -> None:
    """Name only the steps and programs a workspace of the social-science pack has, and say levels with their class."""
    text = PLAYBOOK.read_text()
    named = set(re.findall(r'(?<![#\w.-])veriphy layers step ([a-z][a-z-]*)', text))
    assert named <= {*load_steps(workspace), 'list', 'records'}
    assert set(re.findall(r'(?<![#\w.-])veriphy ([a-z]+)', text)) <= {'layers', 'config', 'pack', 'help'}
    assert set(re.findall(r'(?<![#\w.-])veriphy layers ([a-z]+)', text)) <= set(LAYERS)
    assert 'reproduced (reproduction)' in text


def test_concepts_name_the_thesaurus(workspace: Path) -> None:
    """Match each construct to its thesaurus label, and refuse a construct the thesaurus does not define."""
    step = load_steps(workspace)['check-concepts']
    record = run_step(step, workspace, {'thesaurus': 'thesaurus.ttl'}).record
    assert (record.status, record.outputs['concepts']) == (
        'conforms',
        {'education': 'educational attainment', 'social-trust': 'social trust'},
    )
    thesaurus = workspace / 'thesaurus.ttl'
    thesaurus.write_text(thesaurus.read_text().replace(':social-trust a skos:Concept', ':trust a skos:Concept'))
    record = run_step(step, workspace, {'thesaurus': 'thesaurus.ttl'}).record
    assert record.status == 'violations'
    assert 'social-trust names <https://example.org/thesaurus/social-trust>' in record.outputs['violations'][0]


def test_two_measures_of_one_construct_clash(workspace: Path) -> None:
    """Report the policy claim, which rests on two measures of social trust, as a clash once they exclude each other."""
    for triple in propose_excludes(load_graph(workspace)):
        add_triples(workspace, source_of(triple[0]), 'human', {triple})
    graph = load_graph(workspace)
    found = clashes(graph, reason(graph))
    assert [label_of(c.node) for c in found] == ['policy']
