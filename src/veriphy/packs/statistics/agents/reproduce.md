# Reproduce an analysis

Reproduce the published estimates of a paper from its own Python script and data, test them under variations fixed
in advance, and report each claim's level with its trust class. A reproduced estimate is not a proved claim: it is the
same estimate from the same code and data, and nothing more.

The workspace selects the pack in `veriphy.yaml`:

```yaml
version: 1
packs: [social-science]
```

## 1. Extract

For each estimate the paper reports, write down, before running anything:

- the claim: its label and its statement, in the paper's words;
- the data: the file the authors published, as CSV, and its SHA-256 (`shasum -a 256 <file>`);
- the script: a Python file defining `run(data, inputs)`, where `data` is a list of rows (each a mapping from column
  to value, numbers as floats), returning `{'estimate': ..., 'se': ...}` for the authors' model; `inputs['variation']`
  is the model to fit instead, empty for the model as published;
- the variations to test, fixed now, before any result is seen: other controls, another period;
- the identification assumption it rests on, such as `parallel-trends`, as a convention in the claim graph.

Record the extraction: `veriphy layers step record-claims claims.md --by agent`.

## 2. Reproduce

```
veriphy layers step reproduce analysis.py data.csv --sha256 <digest> --claimed <estimate> --claim <label>
```

The step refuses data whose digest differs from the one written down. It runs the script in a fresh Python process,
compares the estimate with the claimed one, and records both: `agrees` grants `reproduced`, `differs` grants nothing
and keeps both estimates for the report.

## 3. Vary

```
veriphy layers step robustness analysis.py data.csv --sha256 <digest> --variation "<variation>" --claim <label>
```

Give `--variation` once per declared variation. `robust` when the estimate keeps its sign and its significance under
every one; `fragile` names the variations that break it. Never add a variation after seeing a result.

## 4. Reason and report

`veriphy layers step reason` has `oo-horn` check the claim graph: a claim resting on a fragile estimate is capped, and
a claim citing an estimate that assumes the opposite identification is reported as a clash. `veriphy layers step
appendix <source>` writes the appendix.

Report every claim as its level with its class, as `reproduced (reproduction)`, with the estimates, the seed and the
data's digest from its record. Never call a reproduced claim proved or true.
