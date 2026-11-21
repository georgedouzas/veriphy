"""Test the primitive command: `veriphy layers primitive list`, `describe` and `run`, which records nothing."""

import json
from pathlib import Path

import pytest

from veriphy.__main__ import main

SHAPES = """@prefix sh: <http://www.w3.org/ns/shacl#> .
<urn:shape> a sh:NodeShape ; sh:targetClass <urn:Claim> ;
  sh:property [ sh:path <urn:statement> ; sh:minCount 1 ] .
"""


def test_list_names_each_primitive_with_its_class(capsys: pytest.CaptureFixture[str]) -> None:
    """List every shipped primitive with its trust class, its pack, and whether it can run here."""
    main(['layers', 'primitive', 'list'])
    rows = {line.split('\t')[0]: line.split('\t')[1:] for line in capsys.readouterr().out.splitlines()}
    assert rows['horn.check'][:2] == ['checker', 'core']
    assert rows['certify'][:2] == ['kernel', 'math']
    assert all(state[2].startswith(('available', 'unavailable: ')) for state in rows.values())


def test_describe_a_composite(capsys: pytest.CaptureFixture[str]) -> None:
    """Describe a composite by its parts, its deciding part and its class."""
    main(['layers', 'primitive', 'describe', 'meaning'])
    description = json.loads(capsys.readouterr().out)
    assert (description['parts'], description['decides'], description['trust']) == (
        ['lean.serialize', 'sage.sample'],
        None,
        'oracle',
    )


def test_run_by_hand_records_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Run a primitive on an input file, print its output, and write no record."""
    pytest.importorskip('pyshacl')
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'data.nt').write_text('<urn:c1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <urn:Claim> .\n')
    (tmp_path / 'shapes.ttl').write_text(SHAPES)
    (tmp_path / 'input.json').write_text(json.dumps({'data': 'data.nt', 'shapes': 'shapes.ttl'}))
    main(['layers', 'primitive', 'run', 'shacl.validate', '--input', 'input.json'])
    output = json.loads(capsys.readouterr().out)
    assert output['conforms'] is False
    assert output['violations'][0]['focus'] == '<urn:c1>'
    assert not (tmp_path / '.veriphy').exists()


def test_unknown_primitive_fails(capsys: pytest.CaptureFixture[str]) -> None:
    """Exit with status 1 on an unknown primitive, naming those there are."""
    with pytest.raises(SystemExit) as exit_info:
        main(['layers', 'primitive', 'describe', 'lean.chek'])
    assert exit_info.value.code == 1
    assert 'the primitives are' in capsys.readouterr().err
