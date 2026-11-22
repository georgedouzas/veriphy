"""Test the subfield packs, each over the field pack it builds on, with its subfield's own code.

Particle physics with flavio, wilson and the PDG tables, general relativity with EinsteinPy, genomics with pysam,
econometrics with linearmodels, and epidemiology with lifelines: each check accepts or agrees with a correct claim,
and refuses or differs from a wrong one, granting nothing.
"""

import shutil
from pathlib import Path

import pytest

from veriphy.core import FIELDS, check_config, level_order, pack_packages, resolve
from veriphy.steps import load_steps, run_step

EXAMPLES = Path(__file__).resolve().parents[2] / 'docs' / 'examples'
SCHWARZSCHILD = 'diag(-(1 - 2*M/r), 1/(1 - 2*M/r), r**2, r**2*sin(theta)**2)'


def _workspace(root: Path, pack: str, example: str = '') -> Path:
    """Write a workspace of one pack, with a copy of its example's files."""
    if example:
        shutil.copytree(EXAMPLES / example, root, dirs_exist_ok=True)
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
        (
            'particle-physics',
            ['core', 'physics', 'particle-physics'],
            ('none', 'dimensionally-consistent', 'prediction-recomputed'),
        ),
        (
            'general-relativity',
            ['core', 'physics', 'general-relativity'],
            ('none', 'dimensionally-consistent', 'curvature-checked'),
        ),
        ('genomics', ['core', 'life-sciences', 'genomics'], ('none', 'sequence-checked', 'genomic-data-checked')),
        (
            'econometrics',
            ['core', 'statistics', 'economics', 'econometrics'],
            ('none', 'recomputed', 'reproduced', 'robust'),
        ),
        ('epidemiology', ['core', 'statistics', 'epidemiology'], ('none', 'recomputed', 'reproduced', 'robust')),
    ],
)
def test_each_subfield_builds_on_its_field(
    tmp_path: Path,
    pack: str,
    packs: list[str],
    levels: tuple[str, ...],
) -> None:
    """Bring the field pack a subfield requires, and place the subfield's level above the field's."""
    resolved = resolve(_workspace(tmp_path, pack))
    assert [p.name for p in resolved.packs] == packs
    assert level_order(resolved) == levels


def test_flavour_predictions_are_recomputed_with_flavio(tmp_path: Path) -> None:
    """Agree with the Standard Model prediction of BR(Bs→μμ) and with a new-physics one, and differ from a wrong one."""
    root = _workspace(tmp_path, 'particle-physics')
    status, level, outputs = _run(
        root,
        'check-prediction',
        observable='BR(Bs->mumu)',
        claimed='3.66e-9',
        uncertainty='0.14e-9',
    )
    assert (status, level) == ('agrees', 'prediction-recomputed')
    assert 3.5e-9 < float(str(outputs['value'])) < 3.8e-9
    assert _run(root, 'check-prediction', observable='BR(Bs->mumu)', claimed='2.9e-9')[:2] == ('differs', None)
    shifted = _run(
        root,
        'check-prediction',
        observable='BR(Bs->mumu)',
        claimed='5.6e-9',
        coefficients=['C10_bsmumu=-1'],
    )
    assert shifted[0] == 'agrees'


def test_coefficients_run_with_wilson(tmp_path: Path) -> None:
    """Run a SMEFT coefficient from 1 TeV to the b-quark scale, matching onto the weak effective theory."""
    root = _workspace(tmp_path, 'particle-physics')
    inputs = {
        'coefficient': 'C9_bsmumu',
        'to_scale': '4.8',
        'coefficients': ['lq1_2223=1e-8'],
        'to_eft': 'WET',
        'to_basis': 'flavio',
    }
    assert _run(root, 'run-coefficients', **inputs, claimed=-5.66)[:2] == ('agrees', 'prediction-recomputed')
    assert _run(root, 'run-coefficients', **inputs, claimed=-4.0)[:2] == ('differs', None)


def test_particle_properties_come_from_the_pdg(tmp_path: Path) -> None:
    """Agree with the Bs mass, and differ from the B0 mass given for it."""
    root = _workspace(tmp_path, 'particle-physics')
    assert _run(root, 'check-pdg', particle='B(s)0', property='mass', claimed='5366.9')[0] == 'agrees'
    assert _run(root, 'check-pdg', particle='B(s)0', property='mass', claimed='5279.3')[0] == 'differs'


def test_metrics_are_checked_with_einsteinpy(tmp_path: Path) -> None:
    """Accept Schwarzschild as a vacuum solution and de Sitter's scalar, and refuse a metric that is not a solution."""
    root = _workspace(tmp_path, 'general-relativity')
    coordinates = 't r theta phi'
    assert _run(root, 'check-metric', coordinates=coordinates, metric=SCHWARZSCHILD, property='vacuum')[:2] == (
        'accepted',
        'curvature-checked',
    )
    wrong = SCHWARZSCHILD.replace('M/r', 'M/r**2')
    status, level, outputs = _run(root, 'check-metric', coordinates=coordinates, metric=wrong, property='vacuum')
    assert (status, level) == ('refused', None)
    assert 'is not zero' in str(outputs['error'])
    de_sitter = 'diag(-1, exp(2*H*t), exp(2*H*t), exp(2*H*t))'
    assert _run(root, 'check-metric', coordinates='t x y z', metric=de_sitter, property='R = 12*H**2')[0] == 'accepted'
    assert _run(root, 'check-metric', coordinates='t x y z', metric=de_sitter, property='R = 6*H**2')[0] == 'refused'


def test_variants_and_coverage_are_checked_with_pysam(tmp_path: Path) -> None:
    """Accept the patient's homozygous call and the region's depth, refusing the control's and a filtered depth."""
    root = _workspace(tmp_path, 'genomics', 'genomics')
    variant = {'vcf': 'variants.vcf', 'variant': 'chr1:120 C>T', 'genotype': '1/1'}
    assert _run(root, 'check-variant', **variant, sample='patient')[:2] == ('accepted', 'genomic-data-checked')
    status, _, outputs = _run(root, 'check-variant', **variant, sample='control')
    assert (status, outputs['genotype']) == ('refused', '0/1')
    assert _run(root, 'check-coverage', alignments='reads.sam', region='chr1:101-200', claimed=20)[0] == 'agrees'
    filtered = _run(root, 'check-coverage', alignments='reads.sam', region='chr1:101-200', quality=30, claimed=20)
    assert (filtered[0], filtered[2]['depth']) == ('differs', 15.0)


def test_regressions_are_refitted_with_linearmodels(tmp_path: Path) -> None:
    """Agree with the fixed-effects estimate of the returns to training, which pooled OLS overstates."""
    root = _workspace(tmp_path, 'econometrics', 'econometrics')
    panel = {'data': 'panel.csv', 'coefficient': 'training', 'claimed': 0.08}
    pooled = _run(root, 'check-regression', formula='log_wage ~ 1 + training', **panel)
    assert (pooled[0], pooled[2]['estimator']) == ('differs', 'OLS')
    formula = 'log_wage ~ training + EntityEffects + TimeEffects'
    fixed = _run(root, 'check-regression', formula=formula, entity='firm', time='year', covariance='clustered', **panel)
    assert (fixed[0], fixed[1], fixed[2]['estimator']) == ('agrees', 'recomputed', 'PanelOLS')


def test_survival_is_recomputed_with_lifelines(tmp_path: Path) -> None:
    """Agree with the trial's hazard ratio and the control arm's median survival, and differ from a wrong median."""
    root = _workspace(tmp_path, 'epidemiology', 'epidemiology')
    trial = {'data': 'trial.csv', 'duration': 'months', 'event': 'died'}
    ratio = _run(root, 'check-hazard-ratio', **trial, covariates=['treated', 'age'], claimed=0.63)
    assert ratio[:2] == ('agrees', 'recomputed')
    assert _run(root, 'check-median-survival', **trial, group='arm=control', claimed=19.2)[0] == 'agrees'
    assert _run(root, 'check-median-survival', **trial, group='arm=treatment', claimed=30)[0] == 'differs'


def test_subfield_packages_nest_in_their_fields() -> None:
    """Place each subfield's package in its field's, so the package tree is the tree of fields."""
    packages = pack_packages()
    for field, subfields in FIELDS.items():
        for name in subfields:
            assert packages[name] == f"{packages[field]}.{name.replace('-', '_')}"
    assert packages['particle-physics'] == 'veriphy.packs.physics.particle_physics'


def test_a_nested_local_pack_builds_on_the_pack_around_it(tmp_path: Path) -> None:
    """Bring a local pack's enclosing pack, with no `requires`, when the workspace names only the nested one."""
    field = tmp_path / 'packs' / 'oncology'
    subfield = field / 'radiotherapy'
    subfield.mkdir(parents=True)
    (field / 'pack.yaml').write_text('version: 1\nname: oncology\nconventions:\n  staging: [tnm-8, tnm-7]\n')
    (subfield / 'pack.yaml').write_text('version: 1\nname: radiotherapy\nconventions:\n  dose-unit: [gray, rad]\n')
    (tmp_path / 'veriphy.yaml').write_text('version: 1\npacks: [./packs/oncology/radiotherapy]\n')
    resolved = resolve(tmp_path)
    assert [p.name for p in resolved.packs] == ['core', 'oncology', 'radiotherapy']
    assert check_config(resolved) == []
