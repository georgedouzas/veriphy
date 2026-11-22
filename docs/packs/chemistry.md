# The `chemistry` pack

The `chemistry` pack checks molecules and reactions with RDKit: a molecule's formula and molar mass from its SMILES,
and that a reaction balances, element by element.

```console
$ pip install 'veriphy[chemistry]'
```

```yaml
# veriphy.yaml
version: 1
packs: [chemistry]
```

## Molecules and reactions

```console
$ veriphy layers step check-molecule "CC(=O)Oc1ccccc1C(=O)O" --formula C9H8O4 --mass 180.2
check-molecule CC(=O)Oc1ccccc1C(=O)O: accepted
  level: structure-checked (checker)
  record: .veriphy/runs/check-molecule/….json
$ veriphy layers step check-reaction "2 [H][H] + O=O >> 2 O"
check-reaction 2 [H][H] + O=O >> 2 O: accepted
  level: structure-checked (checker)
  record: .veriphy/runs/check-reaction/….json
$ veriphy layers step check-reaction "[H][H] + O=O >> O"
check-reaction [H][H] + O=O >> O: refused
  why: O: 2 on the left, 1 on the right
  record: .veriphy/runs/check-reaction/….json
```

The formula is in Hill order, and the mass, in g/mol, agrees when it rounds to the figure given. A reaction is
`reactants >> products`, each a SMILES with an optional coefficient; hydrogens are counted whether written or not.

## Steps, levels and conventions

| Step | Kind | Does | Grants |
|---|---|---|---|
| `check-molecule <smiles> [--formula f] [--mass m]` | check | checks a molecule's formula and molar mass | `structure-checked` |
| `check-reaction <reaction>` | check | checks that a reaction balances | `structure-checked` |

The convention `standard-state` (`standard-state-1-bar`, `standard-state-1-atm`) lets claims say which standard state
their thermodynamic values assume.
