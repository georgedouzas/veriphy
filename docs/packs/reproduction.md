# The `reproduction` pack

The `reproduction` pack checks empirical claims the way a referee would: it reruns the authors' analysis from their
own script and data, compares the estimate with the published one, and tests whether it survives the variations
declared before the run. It needs neither Lean nor SageMath, only podman or docker for its pinned R image.

```yaml
# veriphy.yaml
version: 1
packs: [reproduction]
```

## Steps and levels

| Step | Kind | Does | Grants |
|---|---|---|---|
| `reproduce <script> <data> <sha256> [--claimed v] [--claim c]` | check | runs the script on the data in `rocker/r-ver` pinned by digest, refusing data whose SHA-256 differs from the claim's, and compares the estimate with `--claimed` | `reproduced` |
| `vary <script> <data> <sha256> <variations>` | check | runs each declared variation, `robust` when the estimate keeps its sign and significance under all of them, `fragile` otherwise, naming the variations that break it | `robust` |

```sh
veriphy layers step reproduce analysis.R mtcars.csv <sha256> --claimed -5.344472 --claim mpg-weight
veriphy layers step vary analysis.R mtcars.csv <sha256> '["mpg ~ wt + hp", "mpg ~ wt + cyl"]' --claim mpg-weight
```

Both levels are of the `reproduction` class: every report shows `reproduced (reproduction)` and
`robust (reproduction)`, never a proof. `reproduce` records both estimates whether they agree or not, and `--claim`
names the claim of the graph that the record gives its level.

The script defines `run <- function(data, inputs)` and returns `list(estimate = ..., se = ...)`. The seed (`--seed`,
0 by default) is set before it runs and enters the record's digest.

## Conventions

The pack declares the aspect `identification: [parallel-trends, no-parallel-trends]`. A claim that rests on an
estimate assuming parallel trends and on one assuming the opposite is a clash in the
[claim graph](../overview/user_guide.md#conventions-impact-and-clashes), even when the second estimate comes from a
cited paper.

## Workflow and skill

`reproduce-analysis` is `[extract, reproduce, vary]`: an agent extracts the claims with their data and declared
variations, and the steps check them. The `reproduce` skill follows it, and its playbook is in
`veriphy layers agents path --pack reproduction`. `src/veriphy/packs/reproduction/example/` is a worked claim on R's
`mtcars`, which CI reproduces on every push.

The pack is also the reference for writing one outside mathematics: one tool pinned by image (a `files` tool writing
JSON), two composites in Python, two declared steps, two levels, a convention, a workflow and a playbook.
