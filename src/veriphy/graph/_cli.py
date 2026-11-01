"""Run the research graph from the command line: `python -m veriphy.graph <command>`."""

import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from veriphy.core import GraphError, find_workspace_root
from veriphy.graph._appendix import FORMATS, appendix
from veriphy.graph._checker import CHECKER_VARIABLE, build_checker, find_checker
from veriphy.graph._checks import clash_report, clashes, propose_excludes, shape_report, validate_shapes
from veriphy.graph._impact import convention_impact, impact_report, plan, plan_report
from veriphy.graph._levels import claim_levels, level_report
from veriphy.graph._reasoning import Run, reason, reasoning_input, recheck
from veriphy.graph._slices import render_slice, slice_claim
from veriphy.graph._store import add_triples, confirm, graph_dir, load_graph, resolve_term
from veriphy.graph._vocabulary import AXIOM, label_of, source_of, vocabulary_text

FAILED, NOT_ACCEPTED = 1, 3
APPENDIX_DIR = 'appendix'
SUFFIXES = {'markdown': '.md', 'latex': '.tex'}
COMMANDS = {
    'validate': 'validate_shapes',
    'reason': 'reason',
    'recheck': 'recheck',
    'levels': 'claim_levels',
    'impact': 'convention_impact',
    'plan': 'plan',
    'slice': 'slice_claim',
    'clashes': 'clashes',
    'excludes': 'propose_excludes',
    'confirm': 'confirm',
    'appendix': 'appendix',
    'axioms': 'reasoning_input',
    'vocabulary': 'vocabulary_text',
    'checker': 'build_checker',
}


def _out(text: str) -> None:
    """Write text to standard output."""
    sys.stdout.write(text)


def _exit_for(run: Run) -> None:
    """Exit with status 3 when the checker did not accept a complete run."""
    if not run.checked:
        sys.stderr.write(f'run {run.directory.name}: {run.label} ({run.report.get("status")})\n')
        raise SystemExit(NOT_ACCEPTED)


def _run_summary(run: Run) -> str:
    """Return the lines that describe a run."""
    theorem = f' ({run.theorem})' if run.theorem else ''
    lines = [
        f'run: {run.directory}',
        f'asserted: {len(run.asserted)}, derived: {len(run.derived)}, complete: {run.complete}',
        f'status: {run.status}, verdict: {run.label}{theorem}',
    ]
    if run.status == 'unchecked_no_checker':
        searched = run.report.get('searched')
        lines.append(f'checker not found at {", ".join(map(str, searched if isinstance(searched, list) else []))}')
        lines.append(f'build it with: {run.report.get("build")} (or set {CHECKER_VARIABLE})')
    if run.status in {'rejected', 'unreadable'}:
        lines.append(f'checker report: {run.report}')
    return '\n'.join(lines) + '\n'


def _cmd_validate(args: argparse.Namespace) -> None:
    """Load the graph, report its files, and validate it against the shapes."""
    graph = load_graph(args.root)
    _out(''.join(f'{path}: {count} triples\n' for path, count in graph.files))
    report = validate_shapes(graph)
    _out(shape_report(report))
    if not report.conforms:
        raise SystemExit(NOT_ACCEPTED)


def _cmd_reason(args: argparse.Namespace) -> None:
    """Reason over the graph and report the checked run."""
    run = reason(load_graph(args.root))
    _out(_run_summary(run))
    _exit_for(run)


def _cmd_recheck(args: argparse.Namespace) -> None:
    """Check a stored run again and compare its digest with the current graph."""
    run, matches = recheck(Path(args.run), load_graph(args.root))
    _out(_run_summary(run))
    _out('the current graph asserts the same triples\n' if matches else 'the current graph has changed since the run\n')
    _exit_for(run)


def _cmd_levels(args: argparse.Namespace) -> None:
    """Report the levels of every claim, or of one source."""
    graph = load_graph(args.root)
    run = reason(graph)
    _out(level_report(claim_levels(graph, run, args.source), run))


def _cmd_impact(args: argparse.Namespace) -> None:
    """Report the nodes that assume a convention."""
    graph = load_graph(args.root)
    run = reason(graph)
    convention = resolve_term(args.convention, args.source)
    _out(impact_report(convention_impact(graph, run, convention), run, convention))


def _cmd_plan(args: argparse.Namespace) -> None:
    """Report what the working graph changes against a git revision."""
    result = plan(load_graph(args.root), args.against)
    _out(plan_report(result))
    if not result.checked:
        raise SystemExit(NOT_ACCEPTED)


def _cmd_slice(args: argparse.Namespace) -> None:
    """Print a claim's slice as agent context, refusing a slice that loses a consequence."""
    graph = load_graph(args.root)
    run = reason(graph)
    piece = slice_claim(graph, run, resolve_term(args.claim, args.source))
    if piece.lost:
        lost = ''.join(f'- {" ".join(label_of(t) for t in triple)}\n' for triple in sorted(piece.lost))
        sys.stderr.write(f'the slice loses consequences about {args.claim}, so it is not offered:\n{lost}')
        raise SystemExit(NOT_ACCEPTED)
    if not piece.keeps:
        sys.stderr.write(f'the slice is unchecked: full run {piece.full.label}, slice run {piece.own.label}\n')
    _out(render_slice(graph, piece))


def _cmd_clashes(args: argparse.Namespace) -> None:
    """Report the clashes of the graph."""
    graph = load_graph(args.root)
    run = reason(graph)
    _out(clash_report(clashes(graph, run), run))


def _cmd_excludes(args: argparse.Namespace) -> None:
    """Propose `excludes` triples, and write them as human assertions with `--confirm`."""
    graph = load_graph(args.root)
    proposed = propose_excludes(graph)
    _out(''.join(f'{label_of(s)} excludes {label_of(o)}\n' for s, _, o in proposed) or 'nothing to propose\n')
    if not args.confirm:
        return
    for triple in proposed:
        add_triples(graph.root, source_of(triple[0]), 'human', {triple})
    _out(f'wrote {len(proposed)} triples as human assertions\n')


def _cmd_confirm(args: argparse.Namespace) -> None:
    """Move one triple from a source's agent file to its human file."""
    root = find_workspace_root(args.root)
    triple = (
        resolve_term(args.subject, args.source),
        resolve_term(args.predicate, args.source, predicate=True),
        resolve_term(args.object, args.source),
    )
    _out(f'confirmed in {confirm(root, args.source, triple)}\n')


def _cmd_appendix(args: argparse.Namespace) -> None:
    """Write the verification appendix of a source."""
    graph = load_graph(args.root)
    run = reason(graph)
    text = appendix(graph, run, args.source, args.format)
    path = (
        Path(args.output)
        if args.output
        else graph_dir(graph.root) / APPENDIX_DIR / f'{args.source}{SUFFIXES[args.format]}'
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    _out(f'wrote {path} ({run.label})\n')


def _cmd_axioms(args: argparse.Namespace) -> None:
    """Print the generated axioms of the graph."""
    triples = reasoning_input(load_graph(args.root))
    _out(''.join(f'{s} {p} {o} .\n' for s, p, o in triples if s.startswith(f'<{AXIOM}') or o.endswith('#none>')))


def _cmd_vocabulary(_: argparse.Namespace) -> None:
    """Print the vocabulary."""
    _out(vocabulary_text())


def _cmd_checker(args: argparse.Namespace) -> None:
    """Set up the checker and the reasoner ahead of first use, or print where the checker is."""
    if args.action == 'path':
        lookup = find_checker()
        _out(f'{lookup.path}\n' if lookup.path else f'not found at {", ".join(map(str, lookup.searched))}\n')
        if lookup.path is None:
            raise SystemExit(FAILED)
        return
    report = build_checker(reasoner_only=args.reasoner_only)
    _out(f'Open Ontologies {report.tag} ({report.commit})\nreasoner: {report.reasoner}\n')
    _out(f'checker: {report.checker}\n' if report.checker else 'checker: not set up (--reasoner-only)\n')


HANDLERS: dict[str, Callable[[argparse.Namespace], None]] = {
    'validate': _cmd_validate,
    'reason': _cmd_reason,
    'recheck': _cmd_recheck,
    'levels': _cmd_levels,
    'impact': _cmd_impact,
    'plan': _cmd_plan,
    'slice': _cmd_slice,
    'clashes': _cmd_clashes,
    'excludes': _cmd_excludes,
    'confirm': _cmd_confirm,
    'appendix': _cmd_appendix,
    'axioms': _cmd_axioms,
    'vocabulary': _cmd_vocabulary,
    'checker': _cmd_checker,
}


def _add_commands(commands: argparse._SubParsersAction) -> None:
    """Add every subcommand with its arguments."""
    for name in ('validate', 'reason', 'clashes', 'excludes', 'axioms', 'vocabulary'):
        commands.add_parser(name, help=HANDLERS[name].__doc__)
    commands.choices['excludes'].add_argument('--confirm', action='store_true', help='write the proposed triples')
    commands.add_parser('recheck', help=HANDLERS['recheck'].__doc__).add_argument('run', help='the run directory')
    commands.add_parser('levels', help=HANDLERS['levels'].__doc__).add_argument('--source', help='one source only')
    for name, term in (('impact', 'convention'), ('slice', 'claim')):
        sub = commands.add_parser(name, help=HANDLERS[name].__doc__)
        sub.add_argument('source', help='the source a bare label belongs to')
        sub.add_argument(term, help=f'the {term}: a label, <source>#<label>, lean:<name> or <iri>')
    commands.add_parser('plan', help=HANDLERS['plan'].__doc__).add_argument('--against', default='HEAD')
    sub = commands.add_parser('confirm', help=HANDLERS['confirm'].__doc__)
    for field in ('source', 'subject', 'predicate', 'object'):
        sub.add_argument(field)
    sub = commands.add_parser('appendix', help=HANDLERS['appendix'].__doc__)
    sub.add_argument('source')
    sub.add_argument('--format', choices=FORMATS, default='markdown')
    sub.add_argument('--output', help='the file to write, under .veriphy/graph/appendix/ by default')
    sub = commands.add_parser('checker', help=HANDLERS['checker'].__doc__)
    sub.add_argument('action', choices=('build', 'path'))
    sub.add_argument(
        '--reasoner-only',
        action='store_true',
        help='fetch the release (the reasoner) only',
    )


def _parser() -> argparse.ArgumentParser:
    """Return the command-line parser."""
    parser = argparse.ArgumentParser(prog='python -m veriphy.graph', description='The research claim graph.')
    parser.add_argument('--root', type=Path, default=None, help='the Lean workspace root')
    _add_commands(parser.add_subparsers(dest='command', required=True))
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Run one command of the research graph.

    Args:
        argv: The command-line arguments, `sys.argv[1:]` when `None`.

    Raises:
        SystemExit: With status 1 on a graph error, 2 on bad usage, and 3 when a run is not accepted by the checker,
            validation finds a violation, or a slice loses a consequence.
    """
    args = _parser().parse_args(list(sys.argv[1:] if argv is None else argv))
    try:
        HANDLERS[args.command](args)
    except GraphError as exc:
        sys.stderr.write(f'{exc}\n')
        raise SystemExit(FAILED) from exc
