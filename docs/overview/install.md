# Installation

Veriphy needs Python 3.11 or later.

## A field's checks

Each pack's libraries install with an extra of the same name:

```sh
pip install 'veriphy[statistics]'
```

| Extra | Installs | For |
|---|---|---|
| `statistics` | pandas, SciPy, statsmodels | rerunning analyses, checking p-values and means |
| `social-science` | `statistics`, pingouin | the reliability of scales |
| `economics` | `statistics` | statistics of published tables |
| `econometrics` | `economics`, linearmodels | OLS, IV and panel regressions |
| `epidemiology` | `statistics`, lifelines | hazard ratios and median survival |
| `physics` | pint, SciPy | units and physical constants |
| `particle-physics` | `physics`, flavio, wilson, particle | flavour predictions, Wilson coefficients, PDG values |
| `general-relativity` | `physics`, EinsteinPy, SymPy | the curvature of a metric |
| `life-sciences` | Biopython, pronto | sequences and ontology terms |
| `genomics` | `life-sciences`, pysam | variant calls and read depth |
| `chemistry` | RDKit | molecules and reactions |
| `all` | every extra above | |

A pack whose libraries are missing still loads. `veriphy layers primitive list` shows what can't run.

## Mathematics

The `math` pack, and its subfields `number-theory`, `group-theory` and `graph-theory`, need
[SageMath](https://doc.sagemath.org/html/en/installation/) 10 and [elan](https://leanprover-community.github.io/get_started.html)
for Lean. Install Veriphy into Sage's Python:

```sh
sage -pip install veriphy
```

Then require Veriphy's Lean library in your Lean project's `lakefile.toml`:

```toml
[[require]]
name = "veriphy"
git = "https://github.com/georgedouzas/veriphy"
rev = "0.8.2"
subDir = "src/veriphy/packs/math/lean"
```

Run `lake update && lake exe cache get && lake build`, and add `import Veriphy` to your Lean files.

## The claim graph's checker

The claim graph uses a checker, `oo-horn`, from [Open Ontologies](https://github.com/fabio-rovai/open-ontologies).
The first command that needs it fetches it and caches it in `~/.cache/veriphy/open-ontologies/`. On Linux x86_64 it
downloads a prebuilt binary. Elsewhere it builds it with Lean once, which takes a few minutes. To do this ahead of
time:

```sh
veriphy layers claims checker build
```

Set `VERIPHY_GRAPH_SETUP=off` to stop Veriphy from fetching anything, for example on an offline machine.

## Claude Code

The Veriphy plugin adds the skills `/veriphy:prove`, `/veriphy:research` and `/veriphy:reproduce`, which run the
commands for you:

```sh
claude plugin marketplace add https://github.com/georgedouzas/veriphy
claude plugin install veriphy@veriphy
```
