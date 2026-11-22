"""Check claims about finite groups with GAP, as Sage ships it: a group's order, structure and properties.

A group is named by one of GAP's constructors with integer arguments, such as `SmallGroup(12, 3)`,
`DihedralGroup(8)` or `SymmetricGroup(5)`; nothing else is evaluated. These functions run under Sage, through the math
pack's `sage` tool.
"""

import re

GROUP = re.compile(r'^[A-Z][A-Za-z]*Group\(\s*\d+(?:\s*,\s*\d+)*\s*\)$')
# each property, and the GAP function that answers it
PROPERTIES = {
    'order': 'Size',
    'structure': 'StructureDescription',
    'id': 'IdGroup',
    'abelian': 'IsAbelian',
    'nilpotent': 'IsNilpotentGroup',
    'solvable': 'IsSolvableGroup',
    'simple': 'IsSimpleGroup',
    'exponent': 'Exponent',
    'center-order': 'Center',
    'classes': 'NrConjugacyClasses',
}


def _normal(value: object) -> str:
    """Return a value as GAP prints it, lower case and without spaces, so `C2 x C2` and `C2xC2` compare equal."""
    return re.sub(r'\s+', '', str(value)).lower()


def group(inputs: dict[str, object]) -> dict[str, object]:
    """Compute a property of a finite group with GAP, and compare the claim with it.

    Args:
        inputs: `group`, a GAP constructor such as `SmallGroup(12, 3)`, `property` (order, structure, id, abelian,
            nilpotent, solvable, simple, exponent, center-order, classes), and `claimed`, as GAP prints it (`A4`,
            `true`, `[ 12, 3 ]`).

    Returns:
        `accepted` when GAP's value is the claim, `refused` otherwise, with GAP's value.
    """
    import sage.all  # noqa: F401, PLC0415 - initializes libgap, under Sage only
    from sage.libs.gap.libgap import libgap  # noqa: PLC0415

    text, wanted = str(inputs['group']).strip(), str(inputs['property'])
    if not GROUP.match(text):
        return {
            'status': 'failed',
            'error': f"name the group by a GAP constructor with integer arguments, not '{text}'",
        }
    if wanted not in PROPERTIES:
        return {'status': 'failed', 'error': f"the property '{wanted}' is not one of {', '.join(PROPERTIES)}"}
    value = getattr(libgap, PROPERTIES[wanted])(libgap.eval(text))
    if wanted == 'center-order':
        value = value.Size()
    found = str(value).lower() if str(value) in {'true', 'false'} else str(value)
    tools = [{'name': 'gap', 'version': str(libgap.eval('GAPInfo.Version')).strip('"'), 'pin': 'version'}]
    result: dict[str, object] = {'group': text, 'property': wanted, 'value': found, 'tools': tools}
    claimed = str(inputs['claimed'])
    if _normal(found) != _normal(claimed):
        error = f"it is {'' if found == 'true' else 'not '}{wanted}" if found in {'true', 'false'} else None
        error = error or f'its {wanted} is {found}, not {claimed}'
        return result | {'status': 'refused', 'errors': [{'message': error}]}
    return result | {'status': 'accepted'}
