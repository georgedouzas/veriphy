"""Report each claim's own verification level and its effective level, capped by what the claim rests on."""

from collections import Counter, deque
from dataclasses import dataclass

from veriphy.graph._reasoning import Run
from veriphy.graph._store import ProjectGraph
from veriphy.graph._vocabulary import LEVELS, label_of, source_of, vp

LEVEL_RANK = {level: rank for rank, level in enumerate(LEVELS)}


def _level_name(term: str) -> str | None:
    """Return the level a vocabulary term names, or `None`."""
    name = term.strip('<>').rsplit('#', 1)[-1]
    return name if name in LEVEL_RANK and term == vp(name) else None


def _asserted_level(graph: ProjectGraph, node: str) -> str | None:
    """Return the level asserted for a node, the lowest when several are."""
    levels = [name for o in graph.objects(node, 'hasLevel') if (name := _level_name(o))]
    return min(levels, key=LEVEL_RANK.__getitem__) if levels else None


def own_level(graph: ProjectGraph, claim: str) -> str:
    """Return a claim's own level: the exported level, else the level of the Lean claim that formalizes it, else `none`.

    Args:
        graph: The research graph.
        claim: The claim, in N-Triples spelling.

    Returns:
        The level's name.
    """
    asserted = _asserted_level(graph, claim)
    if asserted is not None:
        return asserted
    formal = [level for f in graph.objects(claim, 'formalizedBy') if (level := _asserted_level(graph, f))]
    return min(formal, key=LEVEL_RANK.__getitem__) if formal else 'none'


def _caps(run: Run, claim: str) -> list[str]:
    """Return the levels a run caps a claim at."""
    return [level for level in LEVELS if run.holds((claim, vp('cappedAt'), vp(level)))]


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
    for claim in sorted(claims, key=lambda c: (source_of(c), label_of(c))):
        own = own_level(graph, claim)
        effective = min([own, *_caps(run, claim)], key=LEVEL_RANK.__getitem__)
        capped = _capping_claim(graph, claim, effective) if effective != own else None
        rows.append(LevelRow(claim, own, effective, capped, _lean_name(graph, claim), run.checked))
    return tuple(rows)


def level_report(rows: tuple[LevelRow, ...], run: Run) -> str:
    """Return a level report: one line per claim, then the number of claims at each effective level.

    Args:
        rows: The rows, from `claim_levels`.
        run: The run the rows come from.

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
    for row in rows:
        capped = label_of(row.capped_by) if row.capped_by else ''
        lines.append(f'| {label_of(row.claim)} | {row.own} | {row.effective} | {capped} | {row.lean_name or ""} |')
    counts = Counter(row.effective for row in rows)
    lines += ['', ', '.join(f'{level}: {counts[level]}' for level in reversed(LEVELS))]
    return '\n'.join(lines) + '\n'
