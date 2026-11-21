"""Build steps from their declarations: a primitive, its inputs with a digest scope each, and how its result reads."""

import importlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from veriphy.core import BUILTIN_SCOPES, StepError, canonical_json, content_digest, level_trust, resolve
from veriphy.primitives import workspace_registry
from veriphy.steps._primitives import call_primitive
from veriphy.steps._runner import Argument, Outcome, Params, Prepared, Step, exit_code

Scope = Callable[[Path, object], str | bytes]
TYPES: dict[str, Callable[[str], object]] = {'string': str, 'integer': int, 'number': float, 'json': str}


def _value(_root: Path, value: object) -> str:
    """Return a value as the content its digest covers: itself, as canonical JSON."""
    return canonical_json(value)


def _file(_root: Path, value: object) -> bytes:
    """Return a file's bytes."""
    return Path(str(value)).read_bytes()


def _files(_root: Path, value: object) -> str:
    """Return the digest of every file under a directory, by its path inside it."""
    base = Path(str(value))
    found = {str(p.relative_to(base)): content_digest(p.read_bytes()) for p in sorted(base.rglob('*')) if p.is_file()}
    return canonical_json(found)


SCOPES: dict[str, Scope] = dict(zip(BUILTIN_SCOPES, (_value, _file, _files), strict=True))


@dataclass(frozen=True)
class Input:
    """One declared input of a step.

    Args:
        name: Its name, a parameter of the step and a field of the primitive's input.
        scope: The scope that gives the content its digest covers.
        path: Whether it is a path, resolved from the workspace root.
        optional: Whether it is an option rather than a positional argument.
        kind: `string`, `integer`, `number` or `json` (given as text, sent parsed).
        default: Its value when not given.
        many: Whether it may be given several times, collecting a list.
        record: Whether it is only kept in the record, not sent to the primitive.
        flag: The option's spelling when it differs from `--name`.
        help: One line on what it is.
    """

    name: str
    scope: str = 'value'
    path: bool = False
    optional: bool = False
    kind: str = 'string'
    default: object = None
    many: bool = False
    record: bool = False
    flag: str | None = None
    help: str = ''

    def argument(self) -> Argument:
        """Return the command-line argument of this input."""
        return Argument(
            self.name,
            self.help,
            option=self.optional,
            type=TYPES.get(self.kind, str),
            default=self.default,
            flag=self.flag,
            many=self.many,
        )


def _inputs(spec: Mapping[str, object]) -> list[Input]:
    """Return a declaration's inputs, in their declared order."""
    declared = spec.get('inputs')
    found = []
    for name, raw in (declared.items() if isinstance(declared, dict) else []):
        field = raw if isinstance(raw, dict) else {}
        found.append(
            Input(
                name=str(name),
                scope=str(field.get('scope', 'value')),
                path=bool(field.get('path', False)),
                optional=bool(field.get('optional', False)),
                kind=str(field.get('type', 'string')),
                default=field.get('default'),
                many=bool(field.get('many', False)),
                record=bool(field.get('record', False)),
                flag=field.get('flag') if isinstance(field.get('flag'), str) else None,
                help=str(field.get('help', '')),
            ),
        )
    return found


def scope_function(name: str, scopes: Mapping[str, object]) -> Scope:
    """Return the function of a scope: a built-in one, or one a pack declares by its import path.

    Args:
        name: The scope's name.
        scopes: The `scopes` section of the configuration.

    Returns:
        The function, which takes the workspace root and the value.

    Raises:
        StepError: If no scope has the name.
    """
    if name in SCOPES:
        return SCOPES[name]
    spec = scopes.get(name)
    target = spec.get('function') if isinstance(spec, dict) else None
    if not isinstance(target, str):
        message = f"no digest scope is named '{name}': the scopes are {', '.join([*SCOPES, *scopes])}"
        raise StepError(message)
    module, _, function = target.partition(':')
    found = getattr(importlib.import_module(module), function)
    if not callable(found):
        message = f"the scope '{name}' names {target}, which is not a function"
        raise StepError(message)
    return found


def _given(root: Path, spec: Input, params: Params) -> object:
    """Return an input's value as the step uses it: given or defaulted, a path resolved, JSON parsed."""
    value = params.get(spec.name, spec.default)
    if isinstance(value, tuple):
        value = list(value)
    if value is None or value == []:
        if not spec.optional:
            message = f"the input '{spec.name}' is required"
            raise KeyError(message)
        return None
    if spec.path:
        path = Path(str(value))
        return path if path.is_absolute() else root / path
    if spec.kind == 'json' and isinstance(value, str):
        return json.loads(value)
    return value


def _compare(outputs: dict[str, object], values: Mapping[str, object], rule: Mapping[str, object]) -> str:
    """Return `agrees` or `differs`, comparing an output field with an input within the tolerance, and record both."""
    field, against = str(rule['field']), str(rule['against'])
    found, claimed = float(str(outputs[field])), float(str(values[against]))
    tolerance = float(str(rule.get('tolerance', 0)))
    outputs['compared'] = {'field': field, 'found': found, 'claimed': claimed, 'tolerance': tolerance}
    return 'agrees' if abs(found - claimed) <= tolerance else 'differs'


def _check_grant(root: Path, step: str, primitive: str, level: str) -> None:
    """Refuse a level that the primitive's trust class cannot grant, whatever the configuration says."""
    trust = workspace_registry(root.resolve()).get(primitive).trust
    granted = level_trust(resolve(root)).get(level)
    if granted != trust:
        message = (
            f'step {step} would grant {level} ({granted or "an unknown level"}), which {primitive} ({trust}) cannot'
        )
        raise StepError(message)


def declared_step(name: str, spec: Mapping[str, object], scopes: Mapping[str, object]) -> Step:
    """Return the step a declaration describes.

    Args:
        name: The step's name.
        spec: Its declaration: `kind`, `primitive`, `inputs`, `seed`, `status`, `compare`, `grants`, `help`.
        scopes: The configuration's `scopes` section.

    Returns:
        The step.

    Raises:
        StepError: If the declared kind is not one of `agent`, `evidence`, `check` and `derived`.
    """
    inputs = _inputs(spec)
    kind = str(spec.get('kind', 'evidence'))
    primitive = str(spec.get('primitive', ''))
    status = str(spec.get('status', 'status'))
    seeded = bool(spec.get('seed', False))
    declared_grants, declared_rule = spec.get('grants'), spec.get('compare')
    grants: str | None = declared_grants if isinstance(declared_grants, str) else None
    rule: Mapping[str, object] | None = declared_rule if isinstance(declared_rule, dict) else None

    def prepare(root: Path, params: Params) -> Prepared:
        """Read each input, and the content its scope gives the digest."""
        values = {i.name: _given(root, i, params) for i in inputs}
        present = [i for i in inputs if values[i.name] is not None]
        contents = {i.name: scope_function(i.scope, scopes)(root, values[i.name]) for i in present}
        sources = {i.name: str(values[i.name]) if i.path else values[i.name] for i in present}
        seed = int(str(params.get('seed') or 0)) if seeded else None
        return Prepared(contents, sources, seed=seed, context=values)

    def execute(root: Path, params: Params, prepared: Prepared) -> Outcome:
        """Record an agent's artifact, or call the primitive and read its result."""
        values = prepared.context if isinstance(prepared.context, dict) else {}
        kept = {i.name: values[i.name] for i in inputs if i.record and values[i.name] is not None}
        if kind == 'agent':
            return Outcome('written', {**kept, 'author': params.get('by') or 'agent'})
        sent = {i.name: str(v) if i.path else v for i in inputs if not i.record and (v := values[i.name]) is not None}
        schema = workspace_registry(root.resolve()).get(primitive).input_schema
        properties = schema.get('properties')
        if isinstance(properties, dict) and 'root' in properties:
            sent['root'] = str(root)
        if seeded:
            sent['seed'] = prepared.seed or 0
        outcome = call_primitive(root, primitive, sent, status=status)
        outputs = {**kept, **outcome.outputs}
        compared = rule is not None and exit_code(outcome.status) == 0 and str(rule.get('field')) in outputs
        result = _compare(outputs, values, rule) if compared and rule is not None else outcome.status
        level = grants if grants is not None and exit_code(result) == 0 else None
        if level is not None:
            _check_grant(root, name, primitive, level)
        return Outcome(result, outputs, outcome.tools, level)

    arguments = tuple(i.argument() for i in inputs)
    if seeded:
        arguments += (Argument('seed', 'the seed of the random draws', option=True, type=int, default=0),)
    if kind == 'agent':
        arguments += (Argument('by', 'who wrote the artifact (default: agent)', option=True),)
    if kind not in {'agent', 'evidence', 'check', 'derived'}:
        message = f"step {name}: kind '{kind}' is not one of agent, evidence, check, derived"
        raise StepError(message)
    return Step(name, kind, prepare, execute, help=str(spec.get('help', '')), arguments=arguments)
