"""Resolve a workspace's configuration: its packs in order, then `veriphy.yaml`, as JSON Merge Patches (RFC 7396)."""

import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from veriphy.core._digests import canonical_json, content_digest
from veriphy.core._errors import PackError
from veriphy.core._packs import PACK_FILE, pack_dir, pack_packages, read_pack

WORKSPACE_FILE = 'veriphy.yaml'
# the pack that holds the framework's own steps, levels and primitives, applied first in every workspace
FRAMEWORK_PACK = 'core'
DEFAULT_PACKS = ('math',)
DEFAULT = {'version': 1, 'packs': list(DEFAULT_PACKS)}
# trust classes, lowest first; `measurement` and `search` grant no level, and no pack can add a class
TRUST_CLASSES = ('search', 'measurement', 'oracle', 'reproduction', 'checker', 'kernel')
GRANTING = frozenset({'oracle', 'reproduction', 'checker', 'kernel'})
BOTTOM = 'none'
# the digest scopes every workspace has; a pack adds others under `scopes`
BUILTIN_SCOPES = ('value', 'file', 'files')
SECTIONS = ('tools', 'primitives', 'scopes', 'steps', 'levels', 'conventions', 'workflows', 'playbooks', 'commands')
# the step group's own commands, which no step may take as its name
RESERVED_STEPS = ('list', 'records')
# the fields a step and its inputs declare; any other is a typo, such as a comma in an unquoted help text
STEP_FIELDS = ('kind', 'primitive', 'inputs', 'seed', 'status', 'accepts', 'compare', 'grants', 'help', 'code')
# the statuses Veriphy knows the meaning of; a tool with other words must say which accept, by `accepts`
KNOWN_STATUSES = frozenset(
    {
        'accepted',
        'refused',
        'failed',
        'agrees',
        'differs',
        'counterexample',
        'undecided',
        'written',
        'reported',
        'conforms',
        'violations',
        'entailed',
        'rejected',
        'unchecked',
        'incomplete',
        'robust',
        'fragile',
        'mismatch',
    },
)
INPUT_FIELDS = ('scope', 'path', 'optional', 'type', 'default', 'many', 'record', 'flag', 'help')
SCHEMA: dict[str, object] = {
    'type': 'object',
    'additionalProperties': False,
    'required': ['version'],
    'properties': {
        'version': {'const': 1},
        'name': {'type': 'string'},
        'requires': {'type': 'array', 'items': {'type': 'string'}},
        'packs': {'type': 'array', 'items': {'type': 'string'}},
        **{
            section: {'type': 'object', 'additionalProperties': {'type': ['object', 'array', 'null']}}
            for section in SECTIONS
        },
    },
}


@dataclass(frozen=True)
class Pack:
    """A pack selected for a workspace.

    Args:
        name: Its name.
        directory: The directory holding its `pack.yaml`.
        package: Its Python package, for a pack whose code registers steps or composites; `None` for a data-only pack.
        declared: Its `pack.yaml`.
        parent: The pack it is nested in, which it builds on: a field's, for a subfield's pack; `None` at the top.
    """

    name: str
    directory: Path
    package: str | None
    declared: Mapping[str, object]
    parent: str | None = None


@dataclass(frozen=True)
class Resolved:
    """A workspace's resolved configuration.

    Args:
        config: The merged mapping.
        packs: The selected packs, each after the packs it requires.
        root: The workspace root, against which `veriphy.yaml`'s paths resolve.
        sources: The pack, or `veriphy.yaml`, that gave each entry its value, as `tools.sage`.
        collisions: The entries two packs that do not require each other both define, with the two packs.
    """

    config: dict[str, object]
    packs: tuple[Pack, ...]
    root: Path
    sources: dict[str, str] = field(default_factory=dict)
    collisions: tuple[tuple[str, str, str], ...] = ()

    def directory(self, entry: str) -> Path:
        """Return the directory an entry's relative paths resolve against: its pack's, or the workspace's."""
        source = self.sources.get(entry)
        return next((p.directory for p in self.packs if p.name == source), self.root)

    def section(self, name: str) -> dict[str, object]:
        """Return one section of the configuration, empty when no pack declares it."""
        value = self.config.get(name)
        return dict(value) if isinstance(value, dict) else {}

    def digest(self) -> str:
        """Return the digest of the configuration's meaning: canonical JSON, so comments and order do not count."""
        return content_digest(canonical_json(self.config))


def merge_patch(target: object, patch: object) -> object:
    """Apply a JSON Merge Patch (RFC 7396) to a value.

    Args:
        target: The value patched.
        patch: The patch: a mapping merges key by key, `null` removes a key, anything else replaces.

    Returns:
        The patched value; neither argument is changed.

    Examples:
        >>> merge_patch({'a': 'b', 'c': {'d': 'e', 'f': 'g'}}, {'a': 'z', 'c': {'f': None}})
        {'a': 'z', 'c': {'d': 'e'}}
        >>> merge_patch({'a': ['b']}, {'a': ['c', 'd']})
        {'a': ['c', 'd']}
        >>> merge_patch({'a': 'b'}, {'b': None})
        {'a': 'b'}
    """
    if not isinstance(patch, dict):
        return patch
    merged = dict(target) if isinstance(target, dict) else {}
    for key, value in patch.items():
        if value is None:
            merged.pop(key, None)
        else:
            merged[key] = merge_patch(merged.get(key), value)
    return merged


def validate(declared: object, where: str) -> None:
    """Raise unless a `veriphy.yaml` or `pack.yaml` mapping fits the schema, naming the first key that does not.

    Args:
        declared: The file's content.
        where: The file, for the message.

    Raises:
        PackError: If the content does not fit.

    Examples:
        >>> validate({'version': 1, 'tool': {}}, 'veriphy.yaml')
        Traceback (most recent call last):
        ...
        veriphy.core._errors.PackError: veriphy.yaml: Additional properties are not allowed ('tool' was unexpected)
    """
    errors = sorted(Draft202012Validator(SCHEMA).iter_errors(declared), key=lambda e: list(e.path))
    if errors:
        place = '.'.join(str(p) for p in errors[0].path)
        message = f'{where}: {place + ": " if place else ""}{errors[0].message}'
        raise PackError(message)


def read_workspace(root: Path) -> dict[str, object]:
    """Return a workspace's `veriphy.yaml`, or the default `packs: [math]` when it has none.

    Args:
        root: The workspace root.

    Returns:
        The file's mapping.

    Raises:
        PackError: If the file does not read as YAML or does not fit the schema.
    """
    path = root / WORKSPACE_FILE
    if not path.is_file():
        return dict(DEFAULT)
    try:
        declared = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as exc:
        message = f'{path} does not read as YAML: {exc}'
        raise PackError(message) from exc
    validate(declared, str(path))
    return dict(declared)


def _find_pack(name: str, root: Path, packages: Mapping[str, str]) -> Pack:
    """Return a pack by name (an installed pack) or by path (a directory holding `pack.yaml`)."""
    if '/' in name or name.startswith('.'):
        directory = (root / name).resolve()
        path = directory / PACK_FILE
        if not path.is_file():
            message = f"the pack '{name}' has no {PACK_FILE} at {path}"
            raise PackError(message)
        declared = yaml.safe_load(path.read_text()) or {}
        validate(declared, str(path))
        # a local pack's Python (its functions, scopes and steps) imports from its own directory
        if str(directory) not in sys.path:
            sys.path.append(str(directory))
        # a pack in another pack's directory is that pack's subfield, and builds on it
        parent = str(directory.parent) if (directory.parent / PACK_FILE).is_file() else None
        return Pack(str(declared.get('name', directory.name)), directory, None, declared, parent)
    if name not in packages:
        message = f"no pack is named '{name}': the installed packs are {', '.join(packages)}"
        raise PackError(message)
    declared = read_pack(packages[name])
    validate(declared, f'{name}/{PACK_FILE}')
    # a pack in another pack's package is that pack's subfield, and builds on it
    enclosing = packages[name].rpartition('.')[0]
    parent = next((n for n, package in packages.items() if package == enclosing), None)
    return Pack(name, pack_dir(packages[name]), packages[name], declared, parent)


def order_packs(names: Sequence[str], root: Path, packages: Mapping[str, str] | None = None) -> tuple[Pack, ...]:
    """Return the framework pack, the named packs and those they require, each after the packs it requires.

    Args:
        names: The packs the workspace lists.
        root: The workspace root, against which pack paths resolve.
        packages: Each installed pack's package; those of the `veriphy.packs` entry point by default.

    Returns:
        The packs.

    An unknown pack, or requirements forming a cycle, raise `PackError`.
    """
    known = dict(packages) if packages is not None else pack_packages()
    ordered: dict[str, Pack] = {}
    visiting: list[str] = []

    def visit(name: str) -> None:
        """Add a pack after its requirements."""
        pack = _find_pack(name, root, known)
        if pack.name in ordered:
            return
        if pack.name in visiting:
            message = f'the packs require each other in a cycle: {" → ".join([*visiting, pack.name])}'
            raise PackError(message)
        visiting.append(pack.name)
        for required in _direct(pack):
            visit(required)
        visiting.pop()
        ordered[pack.name] = pack

    # the framework's own pack comes first in every workspace: it is not one a workspace chooses
    framework = (FRAMEWORK_PACK,) if FRAMEWORK_PACK in known else ()
    for name in (*framework, *names):
        visit(name)
    return tuple(ordered.values())


def _direct(pack: Pack) -> list[str]:
    """Return the packs a pack requires directly: the pack it is nested in, then those its `requires` names."""
    requires = pack.declared.get('requires')
    named = [str(r) for r in requires] if isinstance(requires, list) else []
    return list(dict.fromkeys([pack.parent, *named] if pack.parent else named))


def _requires(packs: Sequence[Pack]) -> dict[str, set[str]]:
    """Return every pack's requirements, direct and indirect."""
    # a local pack's parent is named by its directory
    by_name = {p.name: p for p in packs} | {str(p.directory): p for p in packs}
    closure: dict[str, set[str]] = {}
    for pack in packs:
        seen: set[str] = set()
        pending = _direct(pack)
        while pending:
            name = pending.pop()
            if name in seen or name not in by_name:
                continue
            seen.add(by_name[name].name)
            pending.extend(_direct(by_name[name]))
        closure[pack.name] = seen
    return closure


def installed(packages: Mapping[str, str] | None = None) -> Resolved:
    """Resolve the configuration outside a workspace: the given packs, or those a workspace with no file selects.

    Args:
        packages: Each pack's name and package; the default packs (`math`, with what it requires) when `None`.

    Returns:
        The configuration.
    """
    known = dict(packages) if packages is not None else pack_packages()
    names = list(packages) if packages is not None else list(DEFAULT_PACKS)
    return _merge(order_packs(names, Path.cwd(), known), {}, Path.cwd())


def resolve(root: Path) -> Resolved:
    """Resolve a workspace's configuration: its packs in order, then its `veriphy.yaml`, as JSON Merge Patches.

    Args:
        root: The workspace root.

    Returns:
        The configuration, with the source of each entry and the collisions between unrelated packs.
    """
    workspace = read_workspace(root)
    listed = workspace.get('packs')
    packs = order_packs([str(n) for n in listed] if isinstance(listed, list) else list(DEFAULT_PACKS), root)
    return _merge(packs, workspace, root)


def _merge(packs: tuple[Pack, ...], workspace: Mapping[str, object], root: Path) -> Resolved:
    """Merge the packs in order, then the workspace file, recording each entry's source and the collisions."""
    closure = _requires(packs)
    config: object = {}
    sources: dict[str, str] = {}
    collisions = []
    for pack in packs:
        for section in SECTIONS:
            entries = pack.declared.get(section)
            for key in entries if isinstance(entries, dict) else {}:
                entry = f'{section}.{key}'
                earlier = sources.get(entry)
                if earlier is not None and earlier not in closure[pack.name]:
                    collisions.append((entry, earlier, pack.name))
                sources[entry] = pack.name
        config = merge_patch(config, {k: v for k, v in pack.declared.items() if k in SECTIONS})
    overrides = {k: v for k, v in workspace.items() if k in SECTIONS}
    for section, entries in overrides.items():
        for key in entries if isinstance(entries, dict) else {}:
            sources[f'{section}.{key}'] = WORKSPACE_FILE
    settled = {f'{s}.{k}' for s, e in overrides.items() if isinstance(e, dict) for k in e}
    config = merge_patch(config, overrides)
    merged = config if isinstance(config, dict) else {}
    sources = {entry: source for entry, source in sources.items() if _present(merged, entry)}
    unsettled = tuple(c for c in collisions if c[0] not in settled)
    return Resolved(merged, packs, root, sources, unsettled)


def _present(config: Mapping[str, object], entry: str) -> bool:
    """Return whether an entry `section.key` is still in the configuration after the merge."""
    section, _, key = entry.partition('.')
    value = config.get(section)
    return isinstance(value, dict) and key in value


def check(resolved: Resolved) -> list[str]:
    """Return what is wrong with a resolved configuration: collisions and references that do not resolve.

    Args:
        resolved: The configuration.

    Returns:
        One message per problem; empty when there is none.
    """
    problems = [
        f'{entry} is defined by {first} and by {second}, which do not require each other: define it in {WORKSPACE_FILE}'
        for entry, first, second in resolved.collisions
    ]
    tools = resolved.section('tools')
    for name, spec in resolved.section('primitives').items():
        tool = spec.get('tool') if isinstance(spec, dict) else None
        if tool and tool not in tools:
            problems.append(f"primitives.{name} names the tool '{tool}', which no pack or {WORKSPACE_FILE} declares")
    for name, spec in resolved.section('commands').items():
        target = spec.get('command') if isinstance(spec, dict) else None
        if not isinstance(target, str) or ':' not in target:
            problems.append(f'commands.{name} must name its click command as <module>:<attribute>')
    return problems + _step_problems(resolved) + _trust_problems(resolved) + _workflow_problems(resolved)


def pack_commands(resolved: Resolved) -> dict[str, dict[str, tuple[str, str]]]:
    """Return the programs each selected pack declares, by pack, each as its import target and its help line.

    Args:
        resolved: The configuration.

    Returns:
        For each pack that declares commands, `{name: (<module>:<attribute>, help)}`; the workspace's own are under
        `workspace`.
    """
    found: dict[str, dict[str, tuple[str, str]]] = {}
    for name, spec in resolved.section('commands').items():
        if not isinstance(spec, dict) or not isinstance(spec.get('command'), str):
            continue
        source = resolved.sources.get(f'commands.{name}', WORKSPACE_FILE)
        owner = 'workspace' if source == WORKSPACE_FILE else source
        found.setdefault(owner, {})[name] = (str(spec['command']), str(spec.get('help', '')))
    return found


def _step_problems(resolved: Resolved) -> list[str]:
    """Return the steps that name a primitive or a digest scope no pack declares."""
    primitives, scopes = resolved.section('primitives'), {*BUILTIN_SCOPES, *resolved.section('scopes')}
    problems = []
    for name, spec in resolved.section('steps').items():
        declared = spec if isinstance(spec, dict) else {}
        if name in RESERVED_STEPS:
            problems.append(f"steps.{name}: '{name}' is the step group's own command, so no step may take its name")
        primitive = declared.get('primitive')
        if 'code' in declared:
            continue
        problems += _status_problems(name, declared, primitives.get(str(primitive)))
        if declared.get('kind') != 'agent' and primitive not in primitives:
            problems.append(
                f"steps.{name} names the primitive '{primitive}', which no pack or {WORKSPACE_FILE} declares",
            )
        problems += [
            f"steps.{name} has the unknown field '{key}': a step takes {', '.join(STEP_FIELDS)}"
            for key in declared
            if key not in STEP_FIELDS
        ]
        inputs = declared.get('inputs')
        for given, raw in (inputs.items() if isinstance(inputs, dict) else []):
            problems += [
                f"steps.{name}.inputs.{given} has the unknown field '{key}': an input takes {', '.join(INPUT_FIELDS)}"
                for key in (raw if isinstance(raw, dict) else {})
                if key not in INPUT_FIELDS
            ]
            scope = raw.get('scope', 'value') if isinstance(raw, dict) else 'value'
            if scope not in scopes:
                problems.append(f"steps.{name}.inputs.{given} names the scope '{scope}', which no pack declares")
    return problems


def _status_problems(name: str, declared: Mapping[str, object], primitive: object) -> list[str]:
    """Return a problem for a granting step whose primitive has statuses of its own, and which names no `accepts`."""
    if 'grants' not in declared or 'accepts' in declared or not isinstance(primitive, dict):
        return []
    output = primitive.get('output')
    properties = output.get('properties') if isinstance(output, dict) else None
    field = str(declared.get('status', 'status'))
    spec = properties.get(field) if isinstance(properties, dict) else None
    words = spec.get('enum') if isinstance(spec, dict) else None
    unknown = sorted(str(w) for w in words if str(w) not in KNOWN_STATUSES) if isinstance(words, list) else []
    if not unknown:
        return []
    message = (
        f"steps.{name} grants a level, and its primitive answers {', '.join(unknown)}: "
        'say which statuses mean success with `accepts`, or every one would grant it'
    )
    return [message]


def level_order(resolved: Resolved) -> tuple[str, ...]:
    """Return a configuration's levels from the lowest, `none`, following each level's `above`.

    Args:
        resolved: The configuration.

    Returns:
        The levels in order; a level the chain does not reach is left out, and `check` names it.
    """
    levels = resolved.section('levels')
    above = {name: spec.get('above') for name, spec in levels.items() if isinstance(spec, dict)}
    order = [BOTTOM] if BOTTOM in levels else []
    while order:
        following = [name for name, below in above.items() if below == order[-1] and name not in order]
        if len(following) != 1:
            break
        order.append(following[0])
    return tuple(order)


def level_trust(resolved: Resolved) -> dict[str, str]:
    """Return each level's trust class; `none` has none.

    Args:
        resolved: The configuration.

    Returns:
        The classes, by level.
    """
    return {
        name: str(spec.get('trust', '')) for name, spec in resolved.section('levels').items() if isinstance(spec, dict)
    }


def _trust_problems(resolved: Resolved) -> list[str]:
    """Return the classes no schema allows, levels outside one chain, and steps granting another class's level."""
    problems = []
    for name, spec in resolved.section('primitives').items():
        trust = spec.get('trust') if isinstance(spec, dict) else None
        if trust is not None and trust not in TRUST_CLASSES:
            problems.append(f"primitives.{name} has the trust class '{trust}', not one of {', '.join(TRUST_CLASSES)}")
    trusts = level_trust(resolved)
    for name, trust in trusts.items():
        if name != BOTTOM and trust not in GRANTING:
            problems.append(f"levels.{name} has the trust class '{trust}', which grants no level")
    levels = resolved.section('levels')
    for below in {spec.get('above') for spec in levels.values() if isinstance(spec, dict)}:
        siblings = sorted(n for n, s in levels.items() if isinstance(s, dict) and s.get('above') == below)
        if len(siblings) > 1:
            problems.append(f"levels {' and '.join(siblings)} are both directly above '{below}': set one's `above`")
    reached = set(level_order(resolved))
    problems += [f'levels.{name} is not on the chain from none' for name in levels if name not in reached]
    primitives = resolved.section('primitives')
    for name, spec in resolved.section('steps').items():
        granted = spec.get('grants') if isinstance(spec, dict) else None
        primitive = primitives.get(str(spec.get('primitive'))) if isinstance(spec, dict) else None
        trust = primitive.get('trust') if isinstance(primitive, dict) else None
        if isinstance(granted, str) and trust is not None and trusts.get(granted) != trust:
            problems.append(
                f"steps.{name} grants {granted} ({trusts.get(granted) or 'unknown'}), which its primitive's class "
                f'({trust}) cannot grant',
            )
    return problems


def workflow_entries(workflow: object) -> list[tuple[str, dict[str, object]]]:
    """Return a workflow's entries as each step's name and its rules: transitions, `attempts`, `exhausted`, `when`.

    Args:
        workflow: The workflow, a list of step names or one-key mappings from a step to its rules.

    Returns:
        The entries, in order.

    Examples:
        >>> workflow_entries(['formalize', {'meaning': {'counterexample': 'stop'}}])
        [('formalize', {}), ('meaning', {'counterexample': 'stop'})]
    """
    entries: list[tuple[str, dict[str, object]]] = []
    for entry in workflow if isinstance(workflow, list) else []:
        if isinstance(entry, dict) and len(entry) == 1:
            ((step, rules),) = entry.items()
            entries.append((str(step), dict(rules) if isinstance(rules, dict) else {}))
        else:
            entries.append((str(entry), {}))
    return entries


RULES = frozenset({'attempts', 'exhausted', 'when'})


def _workflow_problems(resolved: Resolved) -> list[str]:
    """Return the workflows that name a step no pack defines, or go to an entry they do not have."""
    steps = set(resolved.section('steps'))
    problems = []
    for name, workflow in resolved.section('workflows').items():
        entries = workflow_entries(workflow)
        known = {step for step, _ in entries} | {'stop'}
        for step, rules in entries:
            if step not in steps:
                problems.append(f"workflows.{name} names the step '{step}', which no pack defines")
            targets = [v for k, v in rules.items() if k not in RULES or k == 'exhausted']
            problems += [
                f"workflows.{name}: {step} goes to '{target}', which is not an entry of the workflow"
                for target in targets
                if isinstance(target, str) and target not in known
            ]
    return problems
