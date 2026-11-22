# The `group-theory` pack

The `group-theory` pack checks claims about finite groups with GAP, the system Sage ships: a group's order, structure,
identification in the small groups library, and properties such as being abelian, nilpotent, solvable or simple. It is
a subfield of [`math`](math.md), nested in its pack, and runs under Sage through the math pack's `sage` tool.

```yaml
# veriphy.yaml
version: 1
packs: [group-theory]
```

## Checks

```console
$ veriphy layers step check-group "SmallGroup(12, 3)" structure A4
check-group SmallGroup(12, 3): accepted
  level: oracle-test (oracle)
$ veriphy layers step check-group "DihedralGroup(8)" abelian true
check-group DihedralGroup(8): refused
  why: it is not abelian
```

A group is named by a GAP constructor with integer arguments, such as `SmallGroup(12, 3)`, `DihedralGroup(8)` (GAP
counts the dihedral group of order 8) or `SymmetricGroup(5)`. Nothing else is evaluated, so a claim can't run GAP
code. The property is `order`, `structure`, `id`, `abelian`, `nilpotent`, `solvable`, `simple`, `exponent`,
`center-order` or `classes`, and the claim is written as GAP prints it: `A4`, `C2 x C2`, `true`, `[ 12, 3 ]`.

## Steps and levels

| Step | Kind | Does | Grants |
|---|---|---|---|
| `check-group <group> <property> <claimed>` | check | checks a finite group's property with GAP | `oracle-test` |
