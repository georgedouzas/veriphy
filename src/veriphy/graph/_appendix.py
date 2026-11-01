"""Write the verification appendix of a source, in Markdown or LaTeX, from a run of the research graph."""

from collections import Counter

from veriphy.graph._checks import clashes
from veriphy.graph._levels import claim_levels
from veriphy.graph._reasoning import Run
from veriphy.graph._store import ProjectGraph
from veriphy.graph._vocabulary import label_of, source_of

FORMATS = ('markdown', 'latex')
LATEX_SPECIAL = {
    '\\': r'\textbackslash{}',
    '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    '_': r'\_',
    '{': r'\{',
    '}': r'\}',
    '~': r'\textasciitilde{}',
    '^': r'\textasciicircum{}',
}
HEADERS = ('Claim', 'Own level', 'Effective level', 'Capped by', 'Lean', 'Clashes')


def latex_escape(text: str) -> str:
    r"""Return text with LaTeX's special characters escaped.

    Args:
        text: The text.

    Returns:
        The escaped text.

    Examples:
        >>> latex_escape('KK.killing_form_value & 50%')
        'KK.killing\\_form\\_value \\& 50\\%'
    """
    return ''.join(LATEX_SPECIAL.get(char, char) for char in text)


def _provenance_counts(graph: ProjectGraph, run: Run, source: str) -> dict[str, int]:
    """Return how many assertions about the source's nodes each provenance makes, with the generated axioms."""
    counts = Counter(a.provenance for a in graph.assertions if source_of(a.triple[0]) == source)
    counts['veriphy'] = len(run.asserted - graph.triples())
    return dict(counts)


def _rows(graph: ProjectGraph, run: Run, source: str) -> list[tuple[str, ...]]:
    """Return the table rows of a source: one per claim, as plain text."""
    clashing: dict[str, list[str]] = {}
    for clash in clashes(graph, run):
        clashing.setdefault(clash.node, []).append(f'{label_of(clash.first)}/{label_of(clash.second)}')
    return [
        (
            label_of(row.claim),
            row.own,
            row.effective,
            label_of(row.capped_by) if row.capped_by else '',
            row.lean_name or '',
            ', '.join(clashing.get(row.claim, [])),
        )
        for row in claim_levels(graph, run, source)
    ]


def _summary(graph: ProjectGraph, run: Run, source: str) -> list[str]:
    """Return the sentences that open an appendix: the run, its verdict, provenance, and how to recheck it."""
    counts = _provenance_counts(graph, run, source)
    provenance = ', '.join(f'{counts[name]} {name}' for name in sorted(counts))
    directory = run.directory.relative_to(graph.root) if run.directory.is_relative_to(graph.root) else run.directory
    if run.checked:
        verdict = f'The checker oo-horn accepted the run with the verdict {run.verdict} ({run.theorem}).'
    else:
        verdict = f'The effective levels are unchecked: the run is {run.label}, and no checker accepted it.'
    return [
        f'This appendix reports the verification of every claim of {source}, from reasoning run {run.directory.name}.',
        verdict,
        f'The run rests on these assertions by provenance: {provenance}.',
        f'Recheck it from the workspace root with: python -m veriphy.graph recheck {directory}',
    ]


def appendix(graph: ProjectGraph, run: Run, source: str, fmt: str = 'markdown') -> str:
    """Return the verification appendix of a source.

    Args:
        graph: The research graph.
        run: A run of the graph.
        source: The source.
        fmt: `markdown` or `latex`.

    Returns:
        The appendix.
    """
    headers = list(HEADERS)
    if not run.checked:
        headers[2] = 'Effective level (unchecked)'
    rows, summary = _rows(graph, run, source), _summary(graph, run, source)
    if fmt == 'latex':
        body = [' & '.join(latex_escape(cell) for cell in row) + r' \\' for row in rows]
        return '\n'.join(
            [
                f'\\section*{{Verification of {latex_escape(source)}}}',
                '',
                ' '.join(latex_escape(sentence) for sentence in summary),
                '',
                r'\begin{tabular}{llllll}',
                r'\hline',
                ' & '.join(headers) + r' \\',
                r'\hline',
                *body,
                r'\hline',
                r'\end{tabular}',
                '',
            ],
        )
    table = [f'| {" | ".join(headers)} |', '|' + '---|' * len(headers)]
    table += [f'| {" | ".join(row)} |' for row in rows]
    return '\n'.join([f'# Verification of {source}', '', ' '.join(summary), '', *table, ''])
