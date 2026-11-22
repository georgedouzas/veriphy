"""Check claims about graphs with Sage's graph library: invariants such as the chromatic number, girth or diameter.

A graph is given in graph6, or named by one of Sage's constructors, such as `PetersenGraph()` or `CompleteGraph(5)`;
nothing else is evaluated. These functions run under Sage, through the math pack's `sage` tool.
"""

import re

NAMED = re.compile(r'^([A-Z][A-Za-z]*Graph)\(\s*(\d+(?:\s*,\s*\d+)*)?\s*\)$')
# each property, and how Sage computes it
PROPERTIES = {
    'vertices': lambda g: g.order(),
    'edges': lambda g: g.size(),
    'chromatic-number': lambda g: g.chromatic_number(),
    'clique-number': lambda g: g.clique_number(),
    'independence-number': lambda g: len(g.independent_set()),
    'girth': lambda g: g.girth(),
    'diameter': lambda g: g.diameter(),
    'automorphisms': lambda g: g.automorphism_group().order(),
    'planar': lambda g: g.is_planar(),
    'hamiltonian': lambda g: g.is_hamiltonian(),
    'bipartite': lambda g: g.is_bipartite(),
}


def graph(inputs: dict[str, object]) -> dict[str, object]:
    """Compute a graph invariant with Sage, and compare the claim with it.

    Args:
        inputs: `graph`, in graph6 or as a Sage constructor (`PetersenGraph()`), `property` (vertices, edges,
            chromatic-number, clique-number, independence-number, girth, diameter, automorphisms, planar,
            hamiltonian, bipartite), and `claimed`.

    Returns:
        `accepted` when Sage's value is the claim, `refused` otherwise, with Sage's value.
    """
    from sage.all import Graph, graphs  # noqa: PLC0415 - runs under Sage only
    from sage.version import version  # noqa: PLC0415

    text, wanted = str(inputs['graph']).strip(), str(inputs['property'])
    if wanted not in PROPERTIES:
        return {'status': 'failed', 'error': f"the property '{wanted}' is not one of {', '.join(PROPERTIES)}"}
    named = NAMED.match(text)
    if named and hasattr(graphs, named[1]):
        arguments = [int(a) for a in (named[2] or '').split(',') if a.strip()]
        built = getattr(graphs, named[1])(*arguments)
    else:
        try:
            built = Graph(text, format='graph6')
        except (ValueError, RuntimeError) as exc:
            return {'status': 'failed', 'error': f"'{text}' is neither graph6 nor a Sage graph constructor: {exc}"}
    value = PROPERTIES[wanted](built)
    found = str(value).lower() if isinstance(value, bool) else str(value)
    tools = [{'name': 'sagemath', 'version': version, 'pin': 'version'}]
    result: dict[str, object] = {'property': wanted, 'value': found, 'vertices': built.order(), 'tools': tools}
    claimed = str(inputs['claimed']).strip().lower()
    if found != claimed:
        error = f"it is {'' if found == 'true' else 'not '}{wanted}" if found in {'true', 'false'} else None
        error = error or f'its {wanted} is {found}, not {claimed}'
        return result | {'status': 'refused', 'errors': [{'message': error}]}
    return result | {'status': 'accepted'}
