"""Run the research graph from the command line: `python -m veriphy.claims <command>`."""

import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from types import SimpleNamespace

import click

from veriphy.claims._appendix import FORMATS, appendix
from veriphy.claims._checks import clash_report, clashes, propose_excludes, shape_report, validate_shapes
from veriphy.claims._impact import convention_impact, impact_report, plan, plan_report
from veriphy.claims._levels import claim_levels, level_report
from veriphy.claims._reasoning import Run, reason, reasoning_input, recheck
from veriphy.claims._slices import render_slice, slice_claim
from veriphy.claims._store import add_triples, confirm, graph_dir, load_graph, resolve_term
from veriphy.claims._vocabulary import AXIOM, label_of, source_of, vocabulary_text
from veriphy.core import GraphError, find_workspace_root
from veriphy.core._commands import run_command
from veriphy.primitives.graph._checker import CHECKER_VARIABLE, build_checker, find_checker

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


def _cmd_validate(args: SimpleNamespace) -> None:
    """Load the graph, report its files, and validate it against the shapes."""
    graph = load_graph(args.root)
    _out(''.join(f'{path}: {count} triples\n' for path, count in graph.files))
    report = validate_shapes(graph)
    _out(shape_report(report))
    if not report.conforms:
        raise SystemExit(NOT_ACCEPTED)


def _cmd_reason(args: SimpleNamespace) -> None:
    """Reason over the graph and report the checked run."""
    run = reason(load_graph(args.root))
    _out(_run_summary(run))
    _exit_for(run)


def _cmd_recheck(args: SimpleNamespace) -> None:
    """Check a stored run again and compare its digest with the current graph."""
    run, matches = recheck(Path(args.run), load_graph(args.root))
    _out(_run_summary(run))
    _out('the current graph asserts the same triples\n' if matches else 'the current graph has changed since the run\n')
    _exit_for(run)


def _cmd_levels(args: SimpleNamespace) -> None:
    """Report the levels of every claim, or of one source."""
    graph = load_graph(args.root)
    run = reason(graph)
    _out(level_report(claim_levels(graph, run, args.source), run))


def _cmd_impact(args: SimpleNamespace) -> None:
    """Report the nodes that assume a convention."""
    graph = load_graph(args.root)
    run = reason(graph)
    convention = resolve_term(args.convention, args.source)
    _out(impact_report(convention_impact(graph, run, convention), run, convention))


def _cmd_plan(args: SimpleNamespace) -> None:
    """Report what the working graph changes against a git revision."""
    result = plan(load_graph(args.root), args.against)
    _out(plan_report(result))
    if not result.checked:
        raise SystemExit(NOT_ACCEPTED)


def _cmd_slice(args: SimpleNamespace) -> None:
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


def _cmd_clashes(args: SimpleNamespace) -> None:
    """Report the clashes of the graph."""
    graph = load_graph(args.root)
    run = reason(graph)
    _out(clash_report(clashes(graph, run), run))


def _cmd_excludes(args: SimpleNamespace) -> None:
    """Propose `excludes` triples, and write them as human assertions with `--confirm`."""
    graph = load_graph(args.root)
    proposed = propose_excludes(graph)
    _out(''.join(f'{label_of(s)} excludes {label_of(o)}\n' for s, _, o in proposed) or 'nothing to propose\n')
    if not args.confirm:
        return
    for triple in proposed:
        add_triples(graph.root, source_of(triple[0]), 'human', {triple})
    _out(f'wrote {len(proposed)} triples as human assertions\n')


def _cmd_confirm(args: SimpleNamespace) -> None:
    """Move one triple from a source's agent file to its human file."""
    root = find_workspace_root(args.root)
    triple = (
        resolve_term(args.subject, args.source),
        resolve_term(args.predicate, args.source, predicate=True),
        resolve_term(args.object, args.source),
    )
    _out(f'confirmed in {confirm(root, args.source, triple)}\n')


def _cmd_appendix(args: SimpleNamespace) -> None:
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


def _cmd_axioms(args: SimpleNamespace) -> None:
    """Print the generated axioms of the graph."""
    triples = reasoning_input(load_graph(args.root))
    _out(''.join(f'{s} {p} {o} .\n' for s, p, o in triples if s.startswith(f'<{AXIOM}') or o.endswith('#none>')))


def _cmd_vocabulary(_: SimpleNamespace) -> None:
    """Print the vocabulary."""
    _out(vocabulary_text())


def _cmd_checker(args: SimpleNamespace) -> None:
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


HANDLERS: dict[str, Callable[[SimpleNamespace], None]] = {
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


@click.group(name='claims', help='The research claim graph.')
@click.option('--root', type=click.Path(path_type=Path), default=None, help='the Lean workspace root')
@click.pass_context
def claims(ctx: click.Context, root: Path | None) -> None:
    """Hold the workspace root for the subcommand."""
    ctx.obj = root


def _command(name: str, *params: Callable[[Callable[..., None]], Callable[..., None]]) -> None:
    """Add one subcommand, its handler called with the workspace root and the subcommand's parameters."""
    handler = HANDLERS[name]

    @click.pass_obj
    def command(root: Path | None, **values: object) -> None:
        """Run the handler, turning a graph error into status 1."""
        try:
            handler(SimpleNamespace(root=root, **values))
        except GraphError as exc:
            sys.stderr.write(f'{exc}\n')
            raise SystemExit(FAILED) from exc

    for param in reversed(params):
        command = param(command)
    claims.command(name=name, help=handler.__doc__)(command)


TERM = 'a label, <source>#<label>, lean:<name> or <iri>'
for _name in ('validate', 'reason', 'clashes', 'axioms', 'vocabulary'):
    _command(_name)
_command('excludes', click.option('--confirm', is_flag=True, help='write the proposed triples'))
_command('recheck', click.argument('run'))
_command('levels', click.option('--source', default=None, help='one source only'))
_command('impact', click.argument('source'), click.argument('convention'))
_command('slice', click.argument('source'), click.argument('claim'))
_command('plan', click.option('--against', default='HEAD', help='the git revision to compare with'))
_command('confirm', *(click.argument(field) for field in ('source', 'subject', 'predicate', 'object')))
_command(
    'appendix',
    click.argument('source'),
    click.option('--format', type=click.Choice(FORMATS), default='markdown'),
    click.option('--output', default=None, help='the file to write, under .veriphy/graph/appendix/ by default'),
)
_command(
    'checker',
    click.argument('action', type=click.Choice(['build', 'path'])),
    click.option('--reasoner-only', is_flag=True, help='fetch the release (the reasoner) only'),
)


def main(argv: Sequence[str] | None = None) -> None:
    """Run one command of the research graph.

    It exits with status 1 on a graph error, 2 on bad usage, and 3 when a run is not accepted by the checker,
    validation finds a violation, or a slice loses a consequence.

    Args:
        argv: The command-line arguments, `sys.argv[1:]` when `None`.
    """
    run_command(claims, argv, 'veriphy claims')
