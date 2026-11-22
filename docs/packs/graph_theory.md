# The `graph-theory` pack

The `graph-theory` pack checks graph invariants with Sage's graph library: the chromatic, clique and independence
numbers, girth, diameter, the order of the automorphism group, and whether a graph is planar, Hamiltonian or
bipartite. It is a subfield of [`math`](math.md), nested in its pack, and runs under Sage through the math pack's
`sage` tool.

```yaml
# veriphy.yaml
version: 1
packs: [graph-theory]
```

## Checks

```console
$ veriphy layers step check-graph "PetersenGraph()" chromatic-number 3
check-graph PetersenGraph(): accepted
  level: oracle-test (oracle)
  record: .veriphy/runs/check-graph/….json
$ veriphy layers step check-graph "PetersenGraph()" automorphisms 120
check-graph PetersenGraph(): accepted
  level: oracle-test (oracle)
  record: .veriphy/runs/check-graph/….json
$ veriphy layers step check-graph "PetersenGraph()" hamiltonian true
check-graph PetersenGraph(): refused
  why: it is not hamiltonian
  record: .veriphy/runs/check-graph/….json
```

A graph is given in graph6, or named by one of Sage's constructors with integer arguments, such as `PetersenGraph()`
or `CompleteGraph(5)`. The property is `vertices`, `edges`, `chromatic-number`, `clique-number`,
`independence-number`, `girth`, `diameter`, `automorphisms`, `planar`, `hamiltonian` or `bipartite`.

## Steps and levels

| Step | Kind | Does | Grants |
|---|---|---|---|
| `check-graph <graph> <property> <claimed>` | check | checks a graph invariant with Sage | `oracle-test` |
