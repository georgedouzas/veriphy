"""Test primitives: schemas both ways, the two contracts, pins, composites, determinism and purity."""

import json
from pathlib import Path

import pytest

from veriphy.core import PinError, PrimitiveError
from veriphy.primitives import Pin, Registry, Tool, assert_deterministic, check_pin, load_registry
from veriphy.primitives._contracts import _argv, container_runtime


def test_files_tool_returns_its_result(fake: Registry) -> None:
    """Run a files tool, its input and seed as files and placeholders, and name the tool in the output."""
    output = fake.call('fake.echo', {'text': 'hello', 'seed': 7})
    assert (output['echo'], output['seed']) == ('hello', 7)
    assert output['tools'] == [{'name': 'echo', 'version': 'unknown', 'pin': 'none'}]


def test_shell_syntax_reaches_the_tool_as_data(fake: Registry, tmp_path: Path) -> None:
    """Pass an input with shell syntax as data: no shell runs it."""
    marker = tmp_path / 'marker'
    text = f'; touch {marker}; $(touch {marker})'
    assert fake.call('fake.echo', {'text': text})['echo'] == text
    assert not marker.exists()


def test_invalid_input_names_the_field(fake: Registry) -> None:
    """Refuse an input its schema rejects, naming the field, before the tool starts."""
    with pytest.raises(PrimitiveError, match=r'fake.echo input: `seed`: \'ten\' is not of type \'integer\''):
        fake.call('fake.echo', {'seed': 'ten'})


def test_drifting_output_names_the_missing_field(fake: Registry) -> None:
    """Refuse an output that lacks a field its schema requires."""
    with pytest.raises(PrimitiveError, match=r"fake\.echo output: .*'echo' is a required property"):
        fake.call('fake.echo', {'fail': 'drift'})


def test_files_tool_without_a_result(fake: Registry) -> None:
    """Fail when a files tool exits 0 but writes no result."""
    with pytest.raises(PrimitiveError, match='exited with status 0 and no result'):
        fake.call('fake.echo', {'fail': 'no-out'})


def test_files_tool_timeout(fake: Registry) -> None:
    """Stop a files tool past its timeout."""
    with pytest.raises(PrimitiveError, match=r'timed out|did not finish|exceeded'):
        fake.call('fake.echo', {'fail': 'sleep'})


def test_json_lines_tool_and_its_pin(fake: Registry) -> None:
    """Start a JSON-RPC tool once, check its pinned version, and name it in every output."""
    first = fake.call('fake.draw', {'seed': 3})
    second = fake.call('fake.draw', {'seed': 3})
    assert first == second
    assert first['tools'] == [{'name': 'server', 'version': '2.5.0', 'pin': 'version'}]
    assert len(fake.sessions) == 1


def test_python_function(fake: Registry) -> None:
    """Call a Python primitive in-process, with its schemas checked, naming Veriphy as its tool."""
    output = fake.call('fake.square', {'x': 7})
    assert output['square'] == 49
    assert [t['name'] for t in output['tools']] == ['veriphy']
    assert fake.sessions == {}


def test_json_rpc_error(fake: Registry) -> None:
    """Report a JSON-RPC error object by its message."""
    with pytest.raises(PrimitiveError, match='fails: on purpose'):
        fake.call('fake.fails', {})


def test_malformed_line(fake: Registry) -> None:
    """Fail on a response line that is not JSON."""
    with pytest.raises(PrimitiveError, match='not JSON'):
        fake.call('fake.broken', {})


def test_version_drift_refuses_to_run(fake: Registry) -> None:
    """Refuse a tool whose version differs from its pin, naming both."""
    with pytest.raises(PinError, match=r'pinned at version 2\.4\.0, and 2\.5\.0 was found'):
        fake.call('fake.drifted', {})


def test_commit_and_image_pins() -> None:
    """Name a commit pin's commit, and refuse an image pin with no container runtime."""
    horn = Tool('horn', 'files', ('oo-horn',), Pin('commit', 'ef6e781c', 'abc'))
    assert check_pin(horn, None).to_json() == {'name': 'horn', 'version': 'ef6e781c', 'pin': 'commit'}
    if container_runtime() is None:
        r = Tool('r', 'files', ('Rscript',), Pin('image', 'rocker/r-ver@sha256:5f0c'))
        with pytest.raises(PinError, match='needs podman or docker'):
            _argv(r, (), {}, {}, Path())


def test_unavailable_tool(fake: Registry) -> None:
    """Report a primitive whose program is missing, with the program's name."""
    assert "'no-such-program-veriphy' is not on the path" in str(fake.unavailable('fake.absent'))
    assert fake.unavailable('fake.echo') is None


def test_composite_trust_and_tools(fake: Registry) -> None:
    """Give a composite its deciding part's class, or its lowest part's, and the tools of every part it called."""
    assert fake.get('fake.both').trust == 'oracle'
    assert fake.get('fake.pair').trust == 'search'
    output = fake.call('fake.both', {})
    assert [t['name'] for t in output['tools']] == ['echo', 'server']


def test_determinism(fake: Registry) -> None:
    """Pass a seeded primitive through the determinism helper, and fail an unseeded random one."""
    assert 'value' in assert_deterministic(fake, 'fake.draw', {'seed': 5})
    with pytest.raises(PrimitiveError, match='not deterministic'):
        assert_deterministic(fake, 'fake.noise', {})


def test_primitives_write_no_records(fake: Registry, tmp_path: Path) -> None:
    """Leave the workspace's `.veriphy/` untouched: a primitive records nothing."""
    fake.call('fake.echo', {'text': 'x'})
    fake.call('fake.draw', {'seed': 1})
    assert not (tmp_path / '.veriphy').exists()


def test_shipped_packs_declare_every_daemon_method() -> None:
    """Give every Sage daemon method a `sage.*` primitive with both schemas, and the shipped packs their primitives."""
    registry = load_registry({'core': 'veriphy.packs.core', 'lean': 'veriphy.packs.lean', 'math': 'veriphy.packs.math'})
    methods = {p.method for p in registry.primitives.values() if p.tool == 'sage'}
    assert methods == {'ping', 'run', 'run_script', 'meaning', 'test', 'solve', 'symbolic_check', 'matrix_check'}
    assert {'horn.check', 'shacl.validate', 'lean.check', 'lean.serialize', 'lean.level', 'meaning', 'certify'} <= set(
        registry.primitives,
    )
    assert (registry.get('certify').parts, registry.get('certify').decides) == (
        ('lean.serialize', 'sage.search', 'lean.check'),
        'lean.check',
    )
    assert registry.get('certify').trust == 'kernel'
    assert registry.get('meaning').trust == 'oracle'
    assert registry.get('horn.check').function == 'veriphy.primitives.graph._primitives:horn_check'


def test_lean_bridge_starts_the_packs_daemon() -> None:
    """Keep the Lean bridge's default daemon command equal to the `math` pack's `sage` tool."""
    run = load_registry().tools['sage'].run
    bridge = (Path(__file__).resolve().parents[2] / 'lean' / 'Veriphy' / 'Bridge.lean').read_text()
    module = run[2].split('|', 1)[1].rstrip('}').split()[1]
    assert f'"{module}"' in bridge
    assert json.dumps('-m') in bridge
