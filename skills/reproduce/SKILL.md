---
name: reproduce
description: Reproduce the published estimates of a paper from its own script and data with Veriphy's reproduction pack — extract each claim, its data's digest, its script and its declared variations, rerun the analysis in a pinned R image, test the variations, and report each claim's level with its trust class (reproduced or robust, never proved). Use when asked to reproduce, replicate or check the empirical results of a paper.
---

Find the playbook once per session: `sage -python -m veriphy layers agents path --pack reproduction` prints
the directory, written `<prompts>` below. It ships with the installed `veriphy`
package. If the command fails, ask the user to run `sage -pip install veriphy` and stop.

Check the workspace once per session: `veriphy config check` passes with `packs: [reproduction]` in `veriphy.yaml`,
and podman or docker runs, since the analysis runs in a pinned image.

Sequence the work with the `reproduce-analysis` workflow: `veriphy layers workflow next reproduce-analysis <script>` names the next
step, and `veriphy layers workflow run reproduce-analysis <script> --input data=<file> --input sha256=<digest>` runs the steps that
are not yours until it needs you.

Then follow `<prompts>/reproduce.md` exactly as written:
extract → reproduce → vary → reason and report.

Hard rules:
- Fix the variations before running anything, and never add one after seeing a result.
- Report a level with its class, as `reproduced (reproduction)`, and never call a claim proved or true.
