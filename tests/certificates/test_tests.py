"""Test the test records: listing, rerunning the oracle part, and refusing floating-point verdicts."""

import json
from pathlib import Path

import pytest

from veriphy.certificates import main
from veriphy.core import ScriptError
from veriphy.oracle import run_test_script

PROBLEM = {'vars': [], 'atoms': [], 'goal': {'kind': 'false'}, 'universal': [{'name': 'x', 'type': 'ℝ'}]}
SCRIPT = """
R = RealIntervalField(64)
instances = [oracle_instance(str(x), lhs=1 + R(x), rhs=R(x).exp(), relation='<=', edge=(x == 0)) for x in (0, 1, 2)]
"""


@pytest.fixture
def recorded(tmp_path: Path) -> Path:
    """Return a workspace with the record of a run of SCRIPT, as `sage_test` writes it."""
    (tmp_path / 'lakefile.toml').write_text('')
    fresh = run_test_script(PROBLEM, SCRIPT, 60)
    instances = [{**i, 'accepted': True, 'reason': ''} for i in fresh['instances']]
    record = {
        'target': 'expGe',
        'statement': '∀ (x : ℝ), 1 + x ≤ Real.exp x',
        'level': 'oracle-test',
        'seed': fresh['seed'],
        'sage_version': fresh['sage_version'],
        'script_hash': '0',
        'script': SCRIPT,
        'problem': PROBLEM,
        'instances': instances,
    }
    directory = tmp_path / '.veriphy' / 'tests'
    directory.mkdir(parents=True)
    (directory / 'expGe.json').write_text(json.dumps(record))
    return tmp_path


def test_listing_names_the_level(recorded: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """`tests` lists each record with its level and counts."""
    main(['tests', '--root', str(recorded)])
    assert capsys.readouterr().out.startswith('expGe: oracle-test (0 kernel, 3 oracle; seed 0, Sage ')


def test_rerun_holds(recorded: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Rerunning an unchanged script reports that the oracle instances hold."""
    main(['tests', '--root', str(recorded), '--rerun', 'expGe'])
    assert capsys.readouterr().out == 'expGe: the oracle instances hold as recorded\n'


def test_rerun_reports_a_change(recorded: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A script whose verdict changed exits with status 3 and names the instance."""
    path = recorded / '.veriphy' / 'tests' / 'expGe.json'
    record = json.loads(path.read_text())
    record['script'] = SCRIPT.replace("relation='<='", "relation='>'")
    path.write_text(json.dumps(record))
    with pytest.raises(SystemExit) as exit_info:
        main(['tests', '--root', str(recorded), '--rerun', 'expGe'])
    assert exit_info.value.code == 3
    assert 'Sage now refutes the claim' in capsys.readouterr().out


def test_rerun_of_a_missing_record(recorded: Path) -> None:
    """A target without a record is not found."""
    with pytest.raises(SystemExit) as exit_info:
        main(['tests', '--root', str(recorded), '--rerun', 'nothing'])
    assert exit_info.value.code == 1


def test_floating_point_verdicts_are_refused() -> None:
    """A script comparing RDF values fails, naming the instance."""
    script = "instances = [oracle_instance('1', lhs=RDF(2), rhs=RDF(1).exp(), relation='<=')]"
    with pytest.raises(ScriptError, match=r"the instance at \['1'\]: floating-point values"):
        run_test_script(PROBLEM, script, 60)
