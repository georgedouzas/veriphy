"""A fake pack for the primitive tests: tools written as small Python scripts, declared in a `pack.yaml`."""

import sys
import textwrap
from collections.abc import Iterator
from pathlib import Path

import pytest

from veriphy.primitives import Registry, load_registry

ECHO = """
import json, sys
inputs = json.load(open(sys.argv[1]))
if inputs.get('fail') == 'no-out':
    sys.exit(0)
if inputs.get('fail') == 'sleep':
    import time; time.sleep(5)
out = {'echo': inputs.get('text', ''), 'seed': int(sys.argv[3])}
if inputs.get('fail') == 'drift':
    out = {'other': 1}
json.dump(out, open(sys.argv[2], 'w'))
"""
SERVER = """
import json, random, sys
for line in sys.stdin:
    request = json.loads(line)
    params = request.get('params') or {}
    if request['method'] == 'version':
        result = {'version': 'fake 2.5.0'}
    elif request['method'] == 'draw':
        result = {'value': random.Random(params.get('seed', 0)).random()}
    elif request['method'] == 'noise':
        result = {'value': random.random()}
    elif request['method'] == 'fails':
        error = {'code': -32000, 'message': 'fails: on purpose'}
        print(json.dumps({'jsonrpc': '2.0', 'id': request['id'], 'error': error}), flush=True)
        continue
    else:
        print('this is not json', flush=True)
        continue
    print(json.dumps({'jsonrpc': '2.0', 'id': request['id'], 'result': result}), flush=True)
"""
PACK = """
version: 1
name: fake
requires: []
tools:
  echo:
    contract: files
    run: ['{python}', '{tools}/echo.py', '{input}', '{out}', '{seed}']
    timeout: 2
  server:
    contract: jsonrpc
    run: ['{python}', '{tools}/server.py']
    version: {method: version, field: version}
    pin: {version: 2.5.0}
  drifted:
    contract: jsonrpc
    run: ['{python}', '{tools}/server.py']
    version: {method: version, field: version}
    pin: {version: 2.4.0}
  absent:
    contract: files
    run: [no-such-program-veriphy]
primitives:
  fake.echo:
    tool: echo
    trust: search
    seed: placeholder
    input: {type: object, properties: {text: {type: string}, fail: {type: string}, seed: {type: integer}}}
    output: {type: object, required: [echo, seed]}
  fake.draw:
    tool: server
    method: draw
    trust: oracle
    seed: param
    input: {type: object, required: [seed], properties: {seed: {type: integer}}}
    output: {type: object, required: [value]}
  fake.noise:
    tool: server
    method: noise
    trust: oracle
    input: {type: object}
    output: {type: object, required: [value]}
  fake.broken:
    tool: server
    method: broken
    trust: oracle
    input: {type: object}
    output: {type: object}
  fake.drifted:
    tool: drifted
    method: draw
    trust: oracle
    input: {type: object}
    output: {type: object}
  fake.fails:
    tool: server
    method: fails
    trust: oracle
    input: {type: object}
    output: {type: object}
  fake.square:
    function: fakepack.functions:square
    trust: oracle
    input: {type: object, required: [x], properties: {x: {type: integer}}}
    output: {type: object, required: [square]}
  fake.absent:
    tool: absent
    trust: search
    input: {type: object}
    output: {type: object}
"""
COMPOSITES = """
from veriphy.primitives import composite

@composite('fake.both', ('fake.echo', 'fake.draw'), decides='fake.draw', input_schema={'type': 'object'},
           output_schema={'type': 'object'}, pack='fake')
def both(inputs, call):
    return {'echo': call('fake.echo', {'text': 'x'})['echo'], 'value': call('fake.draw', {'seed': 1})['value']}

@composite('fake.pair', ('fake.echo', 'fake.draw'), input_schema={'type': 'object'}, output_schema={'type': 'object'},
           pack='fake')
def pair(inputs, call):
    return call('fake.echo', {'text': 'y'})
"""


@pytest.fixture
def fake(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Registry]:
    """Return a registry of the fake pack alone, its tools in `tmp_path/tools`, and stop its sessions after."""
    tools = tmp_path / 'tools'
    tools.mkdir()
    (tools / 'echo.py').write_text(textwrap.dedent(ECHO))
    (tools / 'server.py').write_text(textwrap.dedent(SERVER))
    package = tmp_path / 'site' / 'fakepack'
    (package / 'primitives').mkdir(parents=True)
    (package / '__init__.py').write_text('')
    (package / 'pack.yaml').write_text(PACK.replace('{tools}', str(tools)))
    (package / 'primitives' / '__init__.py').write_text(COMPOSITES)
    (package / 'functions.py').write_text('def square(inputs):\n    return {"square": inputs["x"] ** 2}\n')
    monkeypatch.syspath_prepend(str(tmp_path / 'site'))
    monkeypatch.chdir(tmp_path)
    registry = load_registry({'fake': 'fakepack'})
    yield registry
    registry.close()
    for name in ('fakepack.primitives', 'fakepack.functions', 'fakepack'):
        sys.modules.pop(name, None)
