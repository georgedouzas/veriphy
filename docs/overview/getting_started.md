# Getting started

Three short sessions, one for each kind of work: reproducing a study, checking a mathematical statement, and checking
how a paper's claims fit together. Each shows the commands and what they print.

Every command runs in a workspace: a directory with a `veriphy.yaml` naming its packs, or a Lean project. Veriphy keeps
its records in the workspace's `.veriphy/` directory.

## 1. Reproduce a study

Install Veriphy (`pip install veriphy`) and copy the example study from
[`docs/examples/social-science/`](https://github.com/georgedouzas/veriphy/tree/main/docs/examples/social-science)
into a new directory. Then select the pack:

```sh
printf 'version: 1\npacks: [social-science]\n' > veriphy.yaml
```

The study reports that each extra year of education raises social trust by 0.127 points. Rerun its analysis:

```console
$ veriphy layers step reproduce analysis.py survey.csv --claimed 0.127 --claim trust-education
reproduce analysis.py: agrees
  found 0.1265132608543874, the claim says 0.127 (tolerance 0.0005)
  level: reproduced (reproduction)
  record: .veriphy/runs/reproduce/39da61d5….json
```

Try a figure the analysis doesn't support:

```console
$ veriphy layers step reproduce analysis.py survey.csv --claimed 0.2
reproduce analysis.py: differs from the claim
  found 0.1265132608543874, the claim says 0.2 (tolerance 0.0005)
```

The command exits with status 1, and the record keeps both values. Then test the estimate under the study's declared
variations:

```console
$ veriphy layers step robustness analysis.py survey.csv --claim trust-education \
    --variation "trust_index ~ education_years + age" --variation "trust_index ~ education_years + income"
robustness analysis.py: robust under every variation
  level: robust (reproduction)
```

`veriphy layers step records` lists what you have checked. The [`social-science` pack](../packs/social_science.md)
covers the rest: data digests, the thesaurus check, and clashes between measures.

## 2. Check a mathematical statement

This needs the `math` pack: SageMath, Lean, and a Lean project that requires Veriphy, as in the
[pack's page](../packs/math.md). In that project, write `Claim.lean`:

```lean
import Mathlib.Analysis.SpecialFunctions.Pow.Real

theorem sqrt_sq_eq_abs' (x : ℝ) : Real.sqrt (x ^ 2) = |x| := Real.sqrt_sq_eq_abs x

/-- A misreading: the square root of x squared is -x. -/
def wrong : Prop := ∀ x : ℝ, 0 ≤ x → Real.sqrt (x ^ 2) = -x
```

Lean checks the file, and the record lists the axioms each declaration uses:

```console
$ veriphy layers step check Claim.lean
check Claim.lean: accepted
```

Lean can't tell you whether `wrong` says what you meant, but sampling it can:

```console
$ veriphy layers step sample Claim.lean wrong --informal "the square root of x squared is -x"
sample Claim.lean: counterexample found
  at x = 1: √(x ^ 2) = -x gives 1 and -1
```

To prove a statement with an agent, let the `prove-claim` workflow say what comes next:

```console
$ veriphy layers workflow next prove-claim Claim.lean
prove-claim on Claim.lean: next is record-statement, an agent step: …
  write the file, then record it:
  veriphy layers step record-statement Claim.lean --by <your name>
```

## 3. Check how a paper's claims fit together

The claim graph comes with every workspace. In the example study, an agent has written the chapter's claims to
`.veriphy/graph/sources/chapter3.agent.ttl`. Copy that file there, then:

```console
$ veriphy layers step validate
validate: conforms
$ veriphy layers claims excludes --confirm
trust-index excludes trust-single-item
$ veriphy layers step reason
reason: entailed: oo-horn accepted the derivation
$ veriphy layers claims clashes
- policy assumes trust-index and trust-single-item
$ veriphy layers claims levels --source chapter3
| claim | own | effective | capped by | Lean |
|---|---|---|---|---|
| policy | none | none |  |  |
| trust-education | robust (reproduction) | robust (reproduction) |  |  |
| trust-item | none | none |  |  |
```

The policy claim rests on two incompatible ways of measuring social trust, so it's reported as a clash.
`trust-education` has the level its records earned. `veriphy layers step appendix chapter3 --format latex` writes all
of this as an appendix for the paper.

## Next

- The [guide](user_guide.md) explains records, levels, workflows and the claim graph.
- [Packs](../packs/index.md) explains how to choose, combine and write packs.
