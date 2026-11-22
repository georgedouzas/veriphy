"""Test trust classes and levels: levels from packs in one order, the grant rule, and levels from records."""

from pathlib import Path

import pytest

from veriphy.claims import claim_levels, level_report, load_graph, own_level, reason, source_iri, vocabulary_text
from veriphy.core import StepError, check_config, installed, level_order, resolve
from veriphy.steps import Record, RecordStore, load_steps, run_step

REPRODUCTION = """version: 1
name: reproduction
requires: [core]
levels:
  reproduced: {trust: reproduction, above: none}
primitives:
  repro.run:
    function: repro_functions:estimate
    trust: reproduction
    input: {type: object}
    output: {type: object}
  repro.guess:
    function: repro_functions:estimate
    trust: search
    input: {type: object}
    output: {type: object}
steps:
  reproduce:
    kind: check
    primitive: repro.run
    grants: reproduced
    inputs: {claim: {}}
"""


def _pack(root: Path, text: str = REPRODUCTION) -> None:
    """Write the social-science pack and its function under the workspace."""
    (root / 'reproduction').mkdir(exist_ok=True)
    (root / 'reproduction' / 'pack.yaml').write_text(text)
    (root / 'repro_functions.py').write_text("def estimate(inputs):\n    return {'status': 'agrees'}\n")


def test_invented_class_is_refused(tmp_path: Path) -> None:
    """Refuse a trust class outside the six, naming the primitive."""
    (tmp_path / 'veriphy.yaml').write_text('version: 1\npacks: [./reproduction]\n')
    _pack(tmp_path, REPRODUCTION.replace('trust: search', 'trust: certified'))
    assert any("primitives.repro.guess has the trust class 'certified'" in p for p in check_config(resolve(tmp_path)))


def test_default_levels_in_order(tmp_path: Path) -> None:
    """Give a workspace with no file today's five levels, in order, each from its pack."""
    resolved = resolve(tmp_path)
    assert level_order(resolved) == ('none', 'oracle-test', 'kernel-test', 'lean-proof', 'certificate')
    sources = {level: resolved.sources[f'levels.{level}'] for level in level_order(resolved)}
    assert sources == {
        'none': 'core',
        'oracle-test': 'math',
        'kernel-test': 'math',
        'lean-proof': 'math',
        'certificate': 'math',
    }


def test_two_fields_settled_by_the_workspace(tmp_path: Path) -> None:
    """Name two levels placed in one position, and pass once the workspace orders them."""
    _pack(tmp_path)
    (tmp_path / 'veriphy.yaml').write_text('version: 1\npacks: [math, ./reproduction]\n')
    assert any('oracle-test and reproduced are both directly above' in p for p in check_config(resolve(tmp_path)))
    settle = 'levels: {reproduced: {above: oracle-test}, kernel-test: {above: reproduced}}\n'
    (tmp_path / 'veriphy.yaml').write_text('version: 1\npacks: [math, ./reproduction]\n' + settle)
    resolved = resolve(tmp_path)
    assert check_config(resolved) == []
    assert level_order(resolved)[:4] == ('none', 'oracle-test', 'reproduced', 'kernel-test')
    assert 'vp:oracle-test vp:below vp:reproduced' in vocabulary_text(tmp_path)


def test_grant_rule_in_the_check_and_the_runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Refuse a step granting a level of another class, in `config check` and when its record is written."""
    monkeypatch.syspath_prepend(str(tmp_path))
    _pack(tmp_path, REPRODUCTION.replace('primitive: repro.run', 'primitive: repro.guess'))
    (tmp_path / 'veriphy.yaml').write_text('version: 1\npacks: [./reproduction]\n')
    assert any('steps.reproduce grants reproduced (reproduction)' in p for p in check_config(resolve(tmp_path)))
    with pytest.raises(StepError, match='would grant reproduced'):
        run_step(load_steps(tmp_path)['reproduce'], tmp_path, {'claim': 'est-2'})


def test_a_record_gives_a_claim_its_level(workspace: Path) -> None:
    """Give a claim the level a record naming it grants, shown with its class, beside the exported levels."""
    _pack(workspace)
    order = 'levels: {reproduced: {above: oracle-test}, kernel-test: {above: reproduced}}\n'
    (workspace / 'veriphy.yaml').write_text('version: 1\npacks: [math, ./reproduction]\n' + order)
    graph = load_graph(workspace)
    claim = source_iri('chapter9', 'eq-4.1')
    assert own_level(graph, claim) == 'none'
    RecordStore(workspace).write(
        Record.from_json(
            {
                'step': 'reproduce',
                'kind': 'check',
                'digest': 'a' * 64,
                'config': 'c' * 64,
                'status': 'agrees',
                'inputs': {'claim': 'eq-4.1'},
                'level': 'reproduced',
            },
        ),
    )
    graph = load_graph(workspace)
    assert own_level(graph, claim) == 'reproduced'


def test_claims_without_lean(workspace: Path) -> None:
    """Reason and report over a graph in a workspace of `core` alone, every level `none`."""
    (workspace / 'veriphy.yaml').write_text('version: 1\npacks: [core]\n')
    graph = load_graph(workspace)
    run = reason(graph)
    rows = claim_levels(graph, run)
    assert rows
    assert {row.own for row in rows} <= {'none'}
    assert 'none:' in level_report(rows, run, graph)


def test_lean_names_the_levels_as_the_packs_do() -> None:
    """Keep the level names Lean computes from proof terms equal to those the `lean` and `math` packs declare."""
    lean = Path(__file__).resolve().parents[2] / 'src' / 'veriphy' / 'packs' / 'math' / 'lean' / 'Veriphy'
    text = (lean / 'Kit' / 'Levels.lean').read_text() + (lean / 'Tactic' / 'SageTest.lean').read_text()
    assert all(f'"{level}"' in text for level in level_order(installed()))
