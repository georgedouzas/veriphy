"""Report each claim's own verification level and its effective level, capped by what the claim rests on."""

import functools
from collections import Counter, deque
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from veriphy.claims._reasoning import Run
from veriphy.claims._store import ProjectGraph
from veriphy.claims._vocabulary import graph_levels, label_of, source_of, vp, workspace_config
from veriphy.core import level_trust
from veriphy.steps import RecordStore, read_record


@functools.lru_cache(maxsize=64)
def _rank_of(root: Path) -> dict[str, int]:
    """Return each level's rank in a workspace's order, the lowest first, read once per workspace."""
    return {level: rank for rank, level in enumerate(graph_levels(root))}


def _rank(graph: ProjectGraph) -> dict[str, int]:
    """Return each level's rank in the graph's workspace."""
    return _rank_of(graph.root)


@functools.lru_cache(maxsize=64)
def _granted(paths: tuple[Path, ...]) -> tuple[tuple[str, frozenset[str]], ...]:
    """Return the level each record grants, with the values its inputs name, read once per set of records."""
    found = []
    for path in paths:
        record = read_record(path)
        if record.level is not None:
            found.append((str(record.level), frozenset(str(v) for v in record.inputs.values())))
    return tuple(found)


def _level_name(term: str, rank: dict[str, int]) -> str | None:
    """Return the level a vocabulary term names, or `None`."""
    name = term.strip('<>').rsplit('#', 1)[-1]
    return name if name in rank and term == vp(name) else None


def _asserted_level(graph: ProjectGraph, node: str, rank: dict[str, int]) -> str | None:
    """Return the level asserted for a node, the lowest when several are."""
    levels = [name for o in graph.objects(node, 'hasLevel') if (name := _level_name(o, rank))]
    return min(levels, key=rank.__getitem__) if levels else None


def _recorded_level(graph: ProjectGraph, names: set[str], rank: dict[str, int]) -> str | None:
    """Return the highest level a step's record grants to a claim its inputs name, or `None`."""
    granted = _granted(tuple(RecordStore(graph.root).all()))
    found = [level for level, named in granted if level in rank and names & named]
    return max(found, key=rank.__getitem__) if found else None


def own_level(graph: ProjectGraph, claim: str) -> str:
    """Return a claim's own level: the highest of its exported level, its formalization's, and its records'.

    A record gives a claim a level when its inputs name the claim, by its label, or the Lean declaration that
    formalizes it; a claim with none of these is at `none`.

    Args:
        graph: The research graph.
        claim: The claim, in N-Triples spelling.

    Returns:
        The level's name.
    """
    rank = _rank(graph)
    asserted = _asserted_level(graph, claim, rank)
    formal = [level for f in graph.objects(claim, 'formalizedBy') if (level := _asserted_level(graph, f, rank))]
    exported = asserted if asserted is not None else min(formal, key=rank.__getitem__) if formal else None
    names = {label_of(claim), *(label_of(f) for f in graph.objects(claim, 'formalizedBy'))}
    recorded = _recorded_level(graph, names, rank)
    candidates = [level for level in (exported, recorded) if level is not None]
    return max(candidates, key=rank.__getitem__) if candidates else 'none'


def _caps(graph: ProjectGraph, run: Run, claim: str) -> list[str]:
    """Return the levels a run caps a claim at."""
    return [level for level in graph_levels(graph.root) if run.holds((claim, vp('cappedAt'), vp(level)))]


def _capping_claim(graph: ProjectGraph, claim: str, level: str) -> str | None:
    """Return the nearest claim reached through `uses` and `formalizedBy` whose own level is `level`."""
    seen, queue = {claim}, deque([claim])
    while queue:
        node = queue.popleft()
        for nxt in (*graph.objects(node, 'uses'), *graph.objects(node, 'formalizedBy')):
            if nxt in seen:
                continue
            if nxt in graph.nodes_of_type('Claim') and own_level(graph, nxt) == level:
                return nxt
            seen.add(nxt)
            queue.append(nxt)
    return None


@dataclass(frozen=True)
class LevelRow:
    """One claim's levels.

    Args:
        claim: The claim, in N-Triples spelling.
        own: Its own level.
        effective: The lowest of its own level and its caps.
        capped_by: The claim that lowers the effective level below the own level, if any.
        lean_name: The Lean declaration of the claim or of its formalization, if any.
        checked: Whether the caps come from a run the checker accepted.
    """

    claim: str
    own: str
    effective: str
    capped_by: str | None
    lean_name: str | None
    checked: bool


def _lean_name(graph: ProjectGraph, claim: str) -> str | None:
    """Return the Lean name of a claim, or of the Lean claim that formalizes it."""
    if source_of(claim) == 'lean':
        return label_of(claim)
    formal = graph.objects(claim, 'formalizedBy')
    return label_of(formal[0]) if formal else None


def claim_levels(graph: ProjectGraph, run: Run, source: str | None = None) -> tuple[LevelRow, ...]:
    """Return the levels of every claim of the graph, or of one source.

    Args:
        graph: The research graph.
        run: A run of the graph.
        source: The source to report, every source when `None`.

    Returns:
        One row per claim, sorted by source and label.
    """
    claims = sorted(c for c in graph.nodes_of_type('Claim') if source is None or source_of(c) == source)
    rows = []
    rank = _rank(graph)
    for claim in sorted(claims, key=lambda c: (source_of(c), label_of(c))):
        own = own_level(graph, claim)
        effective = min([own, *_caps(graph, run, claim)], key=rank.__getitem__)
        capped = _capping_claim(graph, claim, effective) if effective != own else None
        rows.append(LevelRow(claim, own, effective, capped, _lean_name(graph, claim), run.checked))
    return tuple(rows)


def shown_level(level: str, trusts: Mapping[str, str]) -> str:
    """Return a level with its trust class, so a reproduction or an oracle test never reads as a proof.

    Args:
        level: The level.
        trusts: Each level's trust class.

    Returns:
        The level, as `certificate (kernel)`; `none` alone.

    Examples:
        >>> shown_level('reproduced', {'reproduced': 'reproduction'}), shown_level('none', {'none': ''})
        ('reproduced (reproduction)', 'none')
    """
    return f'{level} ({trusts[level]})' if trusts.get(level) else level


def level_report(rows: tuple[LevelRow, ...], run: Run, graph: ProjectGraph | None = None) -> str:
    """Return a level report: one line per claim, each level with its trust class, then the count at each level.

    Args:
        rows: The rows, from `claim_levels`.
        run: The run the rows come from.
        graph: The graph, whose workspace's packs give the levels; every installed pack's when `None`.

    Returns:
        The report as Markdown.
    """
    effective_header = 'effective' if run.checked else 'effective (unchecked)'
    lines = [
        f'Run {run.directory.name}: {run.label}',
        '',
        f'| claim | own | {effective_header} | capped by | Lean |',
        '|---|---|---|---|---|',
    ]
    root = graph.root if graph is not None else None
    trusts = level_trust(workspace_config(root))
    for row in rows:
        capped = label_of(row.capped_by) if row.capped_by else ''
        own, effective = shown_level(row.own, trusts), shown_level(row.effective, trusts)
        cells = [label_of(row.claim), own, effective, capped, row.lean_name or '']
        lines.append('| ' + ' | '.join(cells) + ' |')
    counts = Counter(row.effective for row in rows)
    lines += ['', ', '.join(f'{level}: {counts[level]}' for level in reversed(graph_levels(root)))]
    return '\n'.join(lines) + '\n'
