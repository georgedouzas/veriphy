"""The steps over the research claim graph: `validate`, `reason` and `report`."""

from collections.abc import Iterable
from pathlib import Path

from veriphy.claims._appendix import appendix
from veriphy.claims._checks import validate_shapes
from veriphy.claims._reasoning import Run, load_run, reason, reasoning_input
from veriphy.claims._store import ProjectGraph, graph_dir, load_graph
from veriphy.core._version import __version__
from veriphy.primitives.graph._checker import PINNED_RELEASE
from veriphy.primitives.graph._engine import Triple
from veriphy.steps import Argument, Outcome, Params, Prepared, Step, run_step

APPENDIX_DIR = 'appendix'
SUFFIXES = {'markdown': '.md', 'latex': '.tex'}


def _ntriples(triples: Iterable[Triple]) -> str:
    """Return a set of triples as sorted N-Triples lines, the content their digest is taken over."""
    return ''.join(f'{s} {p} {o} .\n' for s, p, o in sorted(set(triples)))


def _graph_tools() -> dict[str, str]:
    """Return the versions of Veriphy and of the pinned checker release."""
    return {'veriphy': __version__, 'oo-horn': f'{PINNED_RELEASE.tag} ({PINNED_RELEASE.commit})'}


def _loaded(prepared: Prepared) -> ProjectGraph:
    """Return the graph a graph step loaded while preparing."""
    if not isinstance(prepared.context, ProjectGraph):
        message = 'a graph step must prepare its graph'
        raise TypeError(message)
    return prepared.context


def _prepare_graph(root: Path, _params: Params) -> Prepared:
    """Read every assertion of the graph."""
    graph = load_graph(root)
    files = [str(path.relative_to(graph.root)) for path, _ in graph.files]
    return Prepared({'graph': _ntriples(graph.triples())}, {'files': files}, context=graph)


def _validate(_root: Path, _params: Params, prepared: Prepared) -> Outcome:
    """Validate the graph against the shapes."""
    report = validate_shapes(_loaded(prepared))
    violations = [
        {'focus': v.focus, 'path': v.path, 'message': v.message, 'files': [str(f) for f in v.files]}
        for v in report.violations
    ]
    return Outcome(
        'conforms' if report.conforms else 'violations',
        {'violations': violations},
        {'veriphy': __version__},
    )


def _prepare_reason(root: Path, _params: Params) -> Prepared:
    """Read what a run of the graph asserts."""
    graph = load_graph(root)
    return Prepared(
        {'asserted': _ntriples(reasoning_input(graph))},
        {'graph': str(graph_dir(graph.root))},
        context=graph,
    )


def _run_outputs(run: Run, root: Path) -> dict[str, object]:
    """Return what a reasoning run records: its certificate directory, the checker's word and the counts."""
    hint = (
        {'hint': f"set up the checker with `{run.report.get('build')}`"} if run.status == 'unchecked_no_checker' else {}
    )
    return {
        **hint,
        'directory': str(run.directory.resolve().relative_to(root.resolve())),
        'checker_status': run.status,
        'verdict': run.verdict,
        'theorem': run.theorem,
        'complete': run.complete,
        'asserted_digest': run.digest,
        'asserted': len(run.asserted),
        'derived': len(run.derived),
    }


def _reason(root: Path, _params: Params, prepared: Prepared) -> Outcome:
    """Reason over the graph and have the checker check the run."""
    run = reason(_loaded(prepared))
    return Outcome(run.label, _run_outputs(run, root), _graph_tools())


def _prepare_report(root: Path, params: Params) -> Prepared:
    """Read the graph, the source and the format of the appendix."""
    fmt = str(params.get('format', 'markdown'))
    if fmt not in SUFFIXES:
        message = f"unknown format '{fmt}' (known: {', '.join(SUFFIXES)})"
        raise ValueError(message)
    prepared = _prepare_graph(root, params)
    source = str(params['source'])
    return Prepared(
        {**prepared.contents, 'source': source, 'format': fmt},
        {**prepared.sources, 'source': source, 'format': fmt},
        context=prepared.context,
    )


def _report(root: Path, params: Params, prepared: Prepared) -> Outcome:
    """Write the verification appendix of a source, over the recorded reasoning run."""
    graph = _loaded(prepared)
    reasoned = run_step(REASON, root)
    run = load_run(root / str(reasoned.record.outputs['directory']))
    source, fmt = str(params['source']), str(params.get('format', 'markdown'))
    path = graph_dir(graph.root) / APPENDIX_DIR / f'{source}{SUFFIXES[fmt]}'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(appendix(graph, run, source, fmt))
    outputs: dict[str, object] = {
        'path': str(path.relative_to(graph.root)),
        'run': reasoned.record.digest,
        'verdict': run.label,
    }
    return Outcome('written' if run.checked else 'unchecked', outputs, _graph_tools())


VALIDATE = Step(
    'validate',
    'evidence',
    _prepare_graph,
    _validate,
    help='check that the extracted claims are complete, against the shapes',
)
REASON = Step(
    'reason',
    'check',
    _prepare_reason,
    _reason,
    help='derive what the claims establish, and have oo-horn check the derivation',
)
APPENDIX = Step(
    'appendix',
    'derived',
    _prepare_report,
    _report,
    help='write the verification appendix of a source: each claim with its level and what caps it',
    arguments=(Argument('source'), Argument('format', option=True, default='markdown', choices=tuple(SUFFIXES))),
)
