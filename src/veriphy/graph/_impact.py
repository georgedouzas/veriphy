"""Show which claims a convention reaches, and what an edit to the graph changes against a git revision."""

import tempfile
from collections import deque
from dataclasses import dataclass, replace
from pathlib import Path

from veriphy.core import GraphError
from veriphy.graph._checks import clashes
from veriphy.graph._engine import Triple
from veriphy.graph._levels import claim_levels, own_level
from veriphy.graph._process import find_tool, run_process
from veriphy.graph._reasoning import Run, reason
from veriphy.graph._store import ProjectGraph, graph_dir, load_graph
from veriphy.graph._vocabulary import AXIOM, SAME_AS, label_of, source_of, vp

GRAPH_PATHS = ('sources', 'lean')


def _assumers(graph: ProjectGraph, convention: str) -> set[str]:
    """Return the nodes that state the convention directly: asserted `assumes`, or `uses` of a realizing definition."""
    direct = {s for s, p, o in graph.triples() if p == vp('assumes') and o == convention}
    definitions = set(graph.objects(convention, 'realizedBy'))
    return direct | {s for s, p, o in graph.triples() if p == vp('uses') and o in definitions}


def _neighbours(graph: ProjectGraph) -> dict[str, list[str]]:
    """Return, for each node, the nodes it reaches by `uses` and by `owl:sameAs` in either direction."""
    links: dict[str, list[str]] = {}
    for s, p, o in sorted(graph.triples()):
        if p == vp('uses'):
            links.setdefault(s, []).append(o)
        elif p == SAME_AS:
            links.setdefault(s, []).append(o)
            links.setdefault(o, []).append(s)
    return links


def _chain(links: dict[str, list[str]], start: str, targets: set[str]) -> tuple[str, ...]:
    """Return the shortest chain of links from a node to one of the targets, both ends included."""
    previous: dict[str, str | None] = {start: None}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        if node in targets:
            path = [node]
            while (before := previous[path[-1]]) is not None:
                path.append(before)
            return tuple(reversed(path))
        for nxt in links.get(node, []):
            if nxt not in previous:
                previous[nxt] = node
                queue.append(nxt)
    return (start,)


@dataclass(frozen=True)
class ImpactEntry:
    """A node that assumes a convention.

    Args:
        node: The node, in N-Triples spelling.
        chain: The chain of `uses` and `owl:sameAs` from the node to a node that states the convention, both ends
            included.
        lean_name: The Lean declaration of the node or its formalization, if any.
        level: The node's own level when it is a claim, else `None`.
    """

    node: str
    chain: tuple[str, ...]
    lean_name: str | None
    level: str | None


def convention_impact(graph: ProjectGraph, run: Run, convention: str) -> tuple[ImpactEntry, ...]:
    """Return every node that assumes a convention, directly or through its dependencies, sorted by source and label.

    Args:
        graph: The research graph.
        run: A run of the graph.
        convention: The convention, in N-Triples spelling.

    Returns:
        The entries.
    """
    reached = {s for s, p, o in run.asserted | run.derived if p == vp('assumes') and o == convention}
    reached = {n for n in reached if not n.startswith(f'<{AXIOM}') and n not in graph.objects(convention, 'realizedBy')}
    stated, links = _assumers(graph, convention), _neighbours(graph)
    claims = graph.nodes_of_type('Claim')
    names = {row.claim: row.lean_name for row in claim_levels(graph, run)}
    entries = []
    for node in sorted(reached, key=lambda n: (source_of(n), label_of(n))):
        level = own_level(graph, node) if node in claims else None
        entries.append(ImpactEntry(node, _chain(links, node, stated), names.get(node), level))
    return tuple(entries)


def impact_report(entries: tuple[ImpactEntry, ...], run: Run, convention: str) -> str:
    """Return the impact of a convention as Markdown, grouped by source.

    Args:
        entries: The entries, from `convention_impact`.
        run: The run they come from.
        convention: The convention.

    Returns:
        The report.
    """
    lines = [f'Impact of {label_of(convention)} (run {run.directory.name}: {run.label})']
    for source in sorted({source_of(e.node) for e in entries}):
        lines += ['', f'## {source}', '']
        for entry in (e for e in entries if source_of(e.node) == source):
            chain = ' → '.join(label_of(n) for n in entry.chain[1:])
            lean = f' [{entry.lean_name}, {entry.level}]' if entry.lean_name else ''
            via = f' via {chain}' if chain else ''
            lines.append(f'- {label_of(entry.node)}{via}{lean}')
    return '\n'.join(lines) + '\n'


def _git(root: Path, *args: str) -> str:
    """Run git in a workspace and return its output."""
    code, out, err = run_process([find_tool('git', 'plans read the graph at a revision with git'), *args], root)
    if code != 0:
        message = f'git {" ".join(args)}: {err.strip()}'
        raise GraphError(message)
    return out


def graph_at(root: Path, revision: str, workspace: Path) -> ProjectGraph:
    """Load the research graph a git revision holds, by copying its graph files into another workspace.

    Args:
        root: The Lean workspace root, inside a git repository.
        revision: The git revision.
        workspace: An empty directory to hold the copy.

    Returns:
        The graph at the revision, rooted at `workspace`.
    """
    prefix = _git(root, 'rev-parse', '--show-prefix').strip()
    base = graph_dir(root).relative_to(root)
    paths = [f'{prefix}{base}/{name}' for name in GRAPH_PATHS]
    for name in _git(root, 'ls-tree', '-r', '--name-only', revision, '--', *paths).splitlines():
        target = workspace / Path(name).relative_to(prefix)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_git(root, 'show', f'{revision}:{name}'))
    (workspace / 'lakefile.toml').write_text('')
    return load_graph(workspace)


def _consequences(graph: ProjectGraph, run: Run) -> set[Triple]:
    """Return the consequences a plan compares: `assumes` and caps of graph nodes, and clashes as triples."""
    kept = {vp('assumes'), vp('cappedAt')}
    triples = {t for t in run.asserted | run.derived if t[1] in kept and not t[0].startswith(f'<{AXIOM}')}
    return triples | {(c.node, vp('excludes'), f'{c.first} {c.second}') for c in clashes(graph, run)}


@dataclass(frozen=True)
class Plan:
    """What an edit to the graph changes.

    Args:
        added: The consequences the edit adds.
        removed: The consequences the edit removes.
        assertions_added: The asserted triples the edit adds.
        assertions_removed: The asserted triples the edit removes.
        before: The run of the graph at the revision.
        after: The run of the working graph.
    """

    added: frozenset[Triple]
    removed: frozenset[Triple]
    assertions_added: frozenset[Triple]
    assertions_removed: frozenset[Triple]
    before: Run
    after: Run

    @property
    def checked(self) -> bool:
        """Whether the checker accepted both runs."""
        return self.before.checked and self.after.checked


def plan(graph: ProjectGraph, revision: str, checker: Path | None = None) -> Plan:
    """Compare the working graph with the graph at a git revision: both are reasoned and checked.

    Args:
        graph: The working graph.
        revision: The git revision to compare against.
        checker: The `oo-horn` executable, found with `find_checker` when `None`.

    Returns:
        The plan.
    """
    with tempfile.TemporaryDirectory() as tmp:
        old_graph = graph_at(graph.root, revision, Path(tmp))
        before = reason(old_graph, checker)
        old = _consequences(old_graph, before)
        old_assertions = old_graph.triples()
    before = replace(before, directory=Path(revision))
    after = reason(graph, checker)
    new = _consequences(graph, after)
    return Plan(
        frozenset(new - old),
        frozenset(old - new),
        frozenset(graph.triples() - old_assertions),
        frozenset(old_assertions - graph.triples()),
        before,
        after,
    )


def _plan_lines(sign: str, triples: frozenset[Triple]) -> list[str]:
    """Return one line per triple of a plan, with labels for IRIs."""
    return [' '.join([sign, *(label_of(t) if t.startswith('<') else t for t in triple)]) for triple in sorted(triples)]


def plan_report(result: Plan) -> str:
    """Return a plan as Markdown: the changed assertions, then the changed consequences.

    Args:
        result: The plan.

    Returns:
        The report.
    """
    word = 'checked' if result.checked else 'unchecked'
    out = [
        f'{len(result.assertions_added) + len(result.assertions_removed)} changed assertions',
        *_plan_lines('+', result.assertions_added),
        *_plan_lines('-', result.assertions_removed),
        '',
        f'{len(result.added) + len(result.removed)} changed consequences ({word})',
        *_plan_lines('+', result.added),
        *_plan_lines('-', result.removed),
    ]
    return '\n'.join(out) + '\n'
