"""Test the field packs built on each field's standard libraries, from statistics to chemistry.

Each test selects one pack alone in a fresh workspace, checks its configuration, and runs its steps on a correct claim
and a wrong one: the correct one is accepted or agrees, the wrong one is refused or differs and grants nothing.
"""

import shutil
from pathlib import Path

import pytest

from veriphy.core import check_config, level_order, resolve
from veriphy.steps import load_steps, run_step

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / 'docs' / 'examples'


def _workspace(root: Path, pack: str, *files: Path) -> Path:
    """Write a workspace of one pack, with copies of the given example files."""
    for file in files:
        shutil.copyfile(file, root / file.name)
    (root / 'veriphy.yaml').write_text(f'version: 1\npacks: [{pack}]\n')
    assert check_config(resolve(root)) == []
    return root


def _run(root: Path, step: str, **inputs: object) -> tuple[str, str | None, dict[str, object]]:
    """Run a step and return its status, level and outputs."""
    record = run_step(load_steps(root)[step], root, inputs).record
    return record.status, record.level, record.outputs


@pytest.mark.parametrize(
    ('pack', 'packs', 'levels'),
    [
        ('statistics', ['core', 'statistics'], ('none', 'recomputed', 'reproduced', 'robust')),
        ('economics', ['core', 'statistics', 'economics'], ('none', 'recomputed', 'reproduced', 'robust')),
        ('physics', ['core', 'physics'], ('none', 'dimensionally-consistent')),
        ('life-sciences', ['core', 'life-sciences'], ('none', 'sequence-checked')),
        ('chemistry', ['core', 'chemistry'], ('none', 'structure-checked')),
    ],
)
def test_each_pack_stands_alone(tmp_path: Path, pack: str, packs: list[str], levels: tuple[str, ...]) -> None:
    """Pass the configuration check with the pack alone, bringing the packs it requires and ordering its levels."""
    resolved = resolve(_workspace(tmp_path, pack))
    assert [p.name for p in resolved.packs] == packs
    assert level_order(resolved) == levels


def test_p_values_are_recomputed_from_their_statistics(tmp_path: Path) -> None:
    """Accept a p-value the statistic's rounding allows, a bound that holds, and refuse one SciPy does not give."""
    root = _workspace(tmp_path, 'statistics')
    assert _run(root, 'check-p-value', test='t', statistic='2.20', df='28', claimed='.036')[0] == 'agrees'
    assert _run(root, 'check-p-value', test='F', statistic='12.5', df='1,30', claimed='<.01')[0] == 'agrees'
    status, level, outputs = _run(root, 'check-p-value', test='t', statistic='2.20', df='28', claimed='.01')
    assert (status, level) == ('differs', None)
    assert round(float(str(outputs['p'])), 3) == 0.036


def test_means_must_be_possible_for_their_sample(tmp_path: Path) -> None:
    """Apply the GRIM test: 5.18 is a possible mean of 28 integers, 5.19 is not."""
    root = _workspace(tmp_path, 'statistics')
    assert _run(root, 'check-mean', mean='5.18', n=28)[0] == 'agrees'
    assert _run(root, 'check-mean', mean='5.19', n=28)[0] == 'differs'


def test_table_statistics_are_recomputed(tmp_path: Path) -> None:
    """Grant `recomputed` for the example's growth rate, and nothing for a misreported one."""
    root = _workspace(tmp_path, 'economics', EXAMPLES / 'economics' / 'gdp.csv')
    status, level, _ = _run(root, 'recompute', data='gdp.csv', column='real_gdp', statistic='cagr', claimed=0.016)
    assert (status, level) == ('agrees', 'recomputed')
    assert _run(root, 'recompute', data='gdp.csv', column='real_gdp', statistic='cagr', claimed=0.025)[:2] == (
        'differs',
        None,
    )


def test_formulas_are_checked_for_dimensions(tmp_path: Path) -> None:
    """Grant `dimensionally-consistent` to E = m c², and name both sides' dimensions for E = m c."""
    root = _workspace(tmp_path, 'physics')
    units = ['E=J', 'm=kg', 'c=m/s']
    assert _run(root, 'check-units', formula='E = m * c**2', units=units)[:2] == (
        'accepted',
        'dimensionally-consistent',
    )
    status, level, outputs = _run(root, 'check-units', formula='E = m * c', units=units)
    assert (status, level) == ('refused', None)
    assert 'left side' in str(outputs['error'])


def test_constants_are_compared_with_codata(tmp_path: Path) -> None:
    """Agree with a value of G given to its reported digits, and differ from a wrong one."""
    root = _workspace(tmp_path, 'physics')
    name = 'Newtonian constant of gravitation'
    assert _run(root, 'check-constant', name=name, claimed=6.674e-11)[0] == 'agrees'
    assert _run(root, 'check-constant', name=name, claimed=6.67e-12)[0] == 'differs'


def test_sequences_are_checked_with_biopython(tmp_path: Path) -> None:
    """Grant `sequence-checked` for the example's length, GC fraction and translation, and refuse a wrong length."""
    root = _workspace(tmp_path, 'life-sciences', EXAMPLES / 'life-sciences' / 'sequences.fasta')
    status, level, _ = _run(root, 'check-sequence', fasta='sequences.fasta', length=720, gc='0.39', motif='ATG')
    assert (status, level) == ('accepted', 'sequence-checked')
    status, level, outputs = _run(root, 'check-sequence', fasta='sequences.fasta', length=717)
    assert (status, level) == ('refused', None)
    assert 'the length is 720, not 717' in str(outputs['errors'])


def test_concepts_name_ontology_terms(tmp_path: Path) -> None:
    """Match a concept to its Gene Ontology term read from OBO with pronto, and refuse a term the ontology lacks."""
    root = _workspace(tmp_path, 'life-sciences', EXAMPLES / 'life-sciences' / 'go-excerpt.obo')
    sources = root / '.veriphy' / 'graph' / 'sources'
    sources.mkdir(parents=True)
    shutil.copyfile(EXAMPLES / 'life-sciences' / 'claims.agent.ttl', sources / 'claims.agent.ttl')
    status, _, outputs = _run(root, 'check-concepts', thesaurus='go-excerpt.obo')
    assert (status, outputs['concepts']) == ('conforms', {'bioluminescence': 'bioluminescence'})
    obo = root / 'go-excerpt.obo'
    obo.write_text(obo.read_text().replace('GO:0008218', 'GO:0008219'))
    assert _run(root, 'check-concepts', thesaurus='go-excerpt.obo')[0] == 'violations'


def test_molecules_and_reactions_are_checked_with_rdkit(tmp_path: Path) -> None:
    """Grant `structure-checked` to ethanol's formula and mass and to a balanced reaction, refusing wrong ones."""
    root = _workspace(tmp_path, 'chemistry')
    assert _run(root, 'check-molecule', smiles='CCO', formula='C2H6O', mass='46.07')[:2] == (
        'accepted',
        'structure-checked',
    )
    assert _run(root, 'check-molecule', smiles='CCO', formula='C2H4O')[:2] == ('refused', None)
    assert _run(root, 'check-reaction', reaction='2 [H][H] + O=O >> 2 O')[:2] == ('accepted', 'structure-checked')
    assert _run(root, 'check-reaction', reaction='[H][H] + O=O >> O')[:2] == ('refused', None)


def test_scale_reliability_is_recomputed(tmp_path: Path) -> None:
    """Agree with the example's trust scale alpha, 0.76 as reported, and differ from an inflated one."""
    root = _workspace(tmp_path, 'social-science', EXAMPLES / 'social-science' / 'survey.csv')
    items = ['trust_q1', 'trust_q2', 'trust_q3']
    assert _run(root, 'check-reliability', data='survey.csv', items=items, claimed=0.76)[0] == 'agrees'
    assert _run(root, 'check-reliability', data='survey.csv', items=items, claimed=0.9)[0] == 'differs'
