"""Slice a research graph for one claim, check that the slice keeps the claim's consequences, and render it."""

from dataclasses import dataclass
from pathlib import Path

from veriphy.graph._engine import Triple
from veriphy.graph._levels import claim_levels
from veriphy.graph._reasoning import RUNS_DIR, Run, reason_triples
from veriphy.graph._store import ProjectGraph, graph_dir
from veriphy.graph._vocabulary import AXIOM, VOCABULARY, label_of, literal_text, vp

SLICES_DIR = 'slices'


def _about(run: Run, node: str) -> frozenset[Triple]:
    """Return the conclusions of a run whose subject is a node."""
    return frozenset(t for t in run.derived if t[0] == node)


def slice_premises(run: Run, claim: str) -> frozenset[Triple]:
    """Return the asserted triples that the derivations of a claim's consequences rest on, through earlier lines.

    Args:
        run: A run of the graph.
        claim: The claim, in N-Triples spelling.

    Returns:
        The asserted premises, with the claim's own asserted triples.
    """
    by_conclusion = {step.conclusion: step for step in run.steps}
    premises = {t for t in run.asserted if t[0] == claim}
    pending, seen = list(_about(run, claim)), set()
    while pending:
        triple = pending.pop()
        if triple in seen:
            continue
        seen.add(triple)
        step = by_conclusion.get(triple)
        if step is None:
            premises.add(triple)
            continue
        pending.extend(step.premises)
    return frozenset(premises)


@dataclass(frozen=True)
class Slice:
    """A claim's slice of the graph and whether it keeps the claim's consequences.

    Args:
        claim: The claim, in N-Triples spelling.
        triples: The asserted triples of the slice.
        lost: The consequences about the claim that the full run has and the slice's run does not.
        full: The run of the full graph.
        own: The run of the slice alone.
    """

    claim: str
    triples: frozenset[Triple]
    lost: frozenset[Triple]
    full: Run
    own: Run

    @property
    def keeps(self) -> bool:
        """Whether the slice keeps every consequence about the claim, by two checked runs."""
        return not self.lost and self.full.checked and self.own.checked


def check_slice(
    graph: ProjectGraph,
    run: Run,
    claim: str,
    triples: frozenset[Triple],
    checker: Path | None = None,
) -> Slice:
    """Reason over a set of asserted triples alone, and compare its consequences about a claim with the full run.

    Args:
        graph: The research graph.
        run: A run of the full graph.
        claim: The claim, in N-Triples spelling.
        triples: The asserted triples of the slice.
        checker: The `oo-horn` executable, found with `find_checker` when `None`.

    Returns:
        The slice.
    """
    own = reason_triples(triples, graph_dir(graph.root) / RUNS_DIR / SLICES_DIR, checker)
    lost = _about(run, claim) - _about(own, claim) - own.asserted
    return Slice(claim, triples, frozenset(lost), run, own)


def slice_claim(graph: ProjectGraph, run: Run, claim: str, checker: Path | None = None) -> Slice:
    """Compute a claim's slice from the run's certificate and check that it keeps the claim's consequences.

    Args:
        graph: The research graph.
        run: A run of the full graph.
        claim: The claim, in N-Triples spelling.
        checker: The `oo-horn` executable, found with `find_checker` when `None`.

    Returns:
        The slice.
    """
    return check_slice(graph, run, claim, slice_premises(run, claim), checker)


def _statement(graph: ProjectGraph, node: str) -> str:
    """Return a node's statement text, empty when it has none."""
    values = graph.objects(node, 'statement')
    return literal_text(values[0]) if values else ''


def render_slice(graph: ProjectGraph, piece: Slice) -> str:
    """Return a slice as Markdown context for the proving agent.

    Args:
        graph: The research graph, for statements and Lean names.
        piece: The slice, from `slice_claim`.

    Returns:
        The context.
    """
    rows = {row.claim: row for row in claim_levels(graph, piece.full)}
    nodes = {t[0] for t in piece.triples} | {t[2] for t in piece.triples if t[2].startswith('<')}
    nodes = {n for n in nodes if not n.startswith(f'<{AXIOM}') and not n.startswith(f'<{VOCABULARY}')}
    word = 'checked' if piece.full.checked else 'unchecked'
    lines = [f'# Context for {label_of(piece.claim)}', '', _statement(graph, piece.claim), '']
    used = sorted(n for n in nodes if n != piece.claim and n in graph.nodes_of_type('Claim'))
    if used:
        lines += ['## Uses', '']
        for node in used:
            row = rows.get(node)
            level = f' [{row.effective}]' if row else ''
            lines.append(f'- {label_of(node)}{level}: {_statement(graph, node)}')
        lines.append('')
    assumed = sorted(
        o for s, p, o in piece.full.derived | piece.full.asserted if s == piece.claim and p == vp('assumes')
    )
    if assumed:
        lines += [f'## Conventions ({word})', '']
        for convention in assumed:
            aspect = ', '.join(literal_text(o) for o in graph.objects(convention, 'conventionFor'))
            realized = ', '.join(label_of(d) for d in graph.objects(convention, 'realizedBy'))
            lean = f' — Lean: {realized}' if realized else ''
            lines.append(f'- {label_of(convention)} ({aspect}): {_statement(graph, convention)}{lean}')
        lines.append('')
    row = rows.get(piece.claim)
    if row:
        lean = f', Lean: {row.lean_name}' if row.lean_name else ''
        lines.append(f'Level: own {row.own}, effective {row.effective} ({word}){lean}')
    return '\n'.join(lines).rstrip() + '\n'
