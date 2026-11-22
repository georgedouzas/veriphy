"""Check what a source claims about molecules and reactions, with RDKit."""

import re
from collections import Counter

import rdkit
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, rdMolDescriptors

RDLogger.DisableLog('rdApp.*')
TOOLS = [{'name': 'rdkit', 'version': rdkit.__version__, 'pin': 'version'}]
TERM = re.compile(r'^\s*(\d+)?\s*(\S+)\s*$')


def _molecule(smiles: str) -> Chem.Mol | None:
    """Return the molecule a SMILES string describes, or `None` when it doesn't parse."""
    return Chem.MolFromSmiles(smiles)


def molecule(inputs: dict[str, object]) -> dict[str, object]:
    """Return a molecule's formula and molar mass, and check the ones a claim gives it.

    Args:
        inputs: `smiles`, the molecule, and optionally `formula` (in Hill order, as RDKit writes it) and `mass`
            (the molar mass in g/mol, compared to its reported digits).

    Returns:
        `accepted` when every given property holds, `refused` naming each that doesn't, with the formula and the mass.

    Examples:
        >>> molecule({'smiles': 'CCO', 'formula': 'C2H6O', 'mass': '46.07'})['status']
        'accepted'
    """
    mol = _molecule(str(inputs['smiles']))
    if mol is None:
        return {'status': 'failed', 'error': f"RDKit cannot read the SMILES '{inputs['smiles']}'"}
    formula, mass = rdMolDescriptors.CalcMolFormula(mol), Descriptors.MolWt(mol)
    errors = []
    if inputs.get('formula') and str(inputs['formula']) != formula:
        errors.append(f"the formula is {formula}, not {inputs['formula']}")
    if inputs.get('mass'):
        text = str(inputs['mass'])
        decimals = len(text.split('.', 1)[1]) if '.' in text else 0
        if abs(mass - float(text)) > 0.5 * 10.0**-decimals:
            errors.append(f'the molar mass is {mass:.3f} g/mol, not {text}')
    return {
        'status': 'refused' if errors else 'accepted',
        'formula': formula,
        'mass': round(mass, 4),
        'errors': [{'message': e} for e in errors],
        'tools': TOOLS,
    }


def _side(text: str) -> Counter[str] | str:
    """Return the atoms of one side of a reaction, by element, hydrogens included; or the term that doesn't parse."""
    atoms: Counter[str] = Counter()
    for term in text.split(' + '):
        match = TERM.match(term)
        mol = _molecule(match.group(2)) if match else None
        if match is None or mol is None:
            return term.strip()
        count = int(match.group(1) or 1)
        for atom in Chem.AddHs(mol).GetAtoms():
            atoms[atom.GetSymbol()] += count
    return atoms


def reaction(inputs: dict[str, object]) -> dict[str, object]:
    """Check that a reaction balances: each element as many times on each side.

    Args:
        inputs: `reaction`, as `2 [H][H] + O=O >> 2 O`: terms of a coefficient and a SMILES, joined by ` + `, with
            the two sides joined by `>>`.

    Returns:
        `accepted` when every element balances, `refused` naming each that doesn't.

    Examples:
        >>> [reaction({'reaction': r})['status'] for r in ('2 [H][H] + O=O >> 2 O', '[H][H] + O=O >> O')]
        ['accepted', 'refused']
    """
    text = str(inputs['reaction'])
    if text.count('>>') != 1:
        return {'status': 'failed', 'error': 'write the reaction as reactants >> products'}
    sides = [_side(side) for side in text.split('>>')]
    unread = [side for side in sides if isinstance(side, str)]
    if unread:
        return {'status': 'failed', 'error': f"RDKit cannot read the term '{unread[0]}'"}
    left, right = (side for side in sides if not isinstance(side, str))
    errors = [
        f'{element}: {left[element]} on the left, {right[element]} on the right'
        for element in sorted(set(left) | set(right))
        if left[element] != right[element]
    ]
    return {
        'status': 'refused' if errors else 'accepted',
        'atoms': {element: left[element] for element in sorted(left)},
        'errors': [{'message': e} for e in errors],
        'tools': TOOLS,
    }
