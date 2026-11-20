# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- insertion marker -->
## [0.7.0](https://github.com/georgedouzas/veriphy/releases/tag/0.7.0) - 2026-11-20

<small>[Compare with 0.6.0](https://github.com/georgedouzas/veriphy/compare/0.6.0...0.7.0)</small>

### Features

- Ship the playbooks, recipes, templates and recipe assets in the Python package, with python -m veriphy.prompts; the skills read them from the installed package instead of a clone ([a035ffd](https://github.com/georgedouzas/veriphy/commit/a035ffdb483b4bc8e1ce8ee04021be8b4366fbff) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

### Docs

- README and plugin pin 0.7.0 ([9817f4b](https://github.com/georgedouzas/veriphy/commit/9817f4bed2a5ed590f17eacfe293b932b42d9e58) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Write the purpose of the packaged-playbooks spec ([a767535](https://github.com/georgedouzas/veriphy/commit/a767535ef16bf22d57f40614f2cabdbbffb36a8a) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Archive packaged-playbooks with its specs synced ([9bd590d](https://github.com/georgedouzas/veriphy/commit/9bd590d40fa83e1a0afca6d7dda833e8251d3158) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Propose the target architecture, with D2 diagrams: deterministic steps and records, trust classes, veriphy.yaml with packs, workflows as data ([5c59451](https://github.com/georgedouzas/veriphy/commit/5c594517497923f1a862ea92a28623fe2d61aeb6) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Mark the prompts command task done ([54fa279](https://github.com/georgedouzas/veriphy/commit/54fa279201acfc8867a258f73192abfbf90cc3c8) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- packaged-playbooks tasks complete, CI green with the templates run from the package ([0a33da0](https://github.com/georgedouzas/veriphy/commit/0a33da0ec3d6b0e9f0060789783cb425a131d382) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Archive lean-sources-dir with its specs synced ([e07edc8](https://github.com/georgedouzas/veriphy/commit/e07edc81a6fab6c190b201c771702a9397b90741) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- lean-sources-dir tasks complete, CI green with the Lean sources under lean/ ([be9808f](https://github.com/georgedouzas/veriphy/commit/be9808f947574e9c04b44943e486ed5c4fbefc5f) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

### Code Refactoring

- Move the Lean sources under lean/, keeping the Lake configuration at the root so dependents require the repository unchanged ([bea3785](https://github.com/georgedouzas/veriphy/commit/bea3785e4365cab1a01b367764613d6d77a1342b) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

## [0.6.0](https://github.com/georgedouzas/veriphy/releases/tag/0.6.0) - 2026-11-02

<small>[Compare with 0.5.0](https://github.com/georgedouzas/veriphy/compare/0.5.0...0.6.0)</small>

### Features

- Add the verification level lean-proof, and require the standard axioms for certificate and lean-proof ([110c9d6](https://github.com/georgedouzas/veriphy/commit/110c9d66b208065129c48fdae735ba0263178cbe) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

### Docs

- Archive lean-proof-level with its specs synced; README and plugin pin 0.6.0 ([359f519](https://github.com/georgedouzas/veriphy/commit/359f519435c444a23f36bc7bf4e052f56e1a1327) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Center the README and user guide on the skill workflows, for a theorem and for a paper ([154d0ad](https://github.com/georgedouzas/veriphy/commit/154d0adb81da33b170750e2a0c4dd70066fdfc04) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

### Chore

- Release 0.6.0 ([b85488e](https://github.com/georgedouzas/veriphy/commit/b85488e7b7657c9cab1456292eecde83534fc1e4) by georgedouzas).

## [0.5.0](https://github.com/georgedouzas/veriphy/releases/tag/0.5.0) - 2026-11-01

<small>[Compare with 0.4.0](https://github.com/georgedouzas/veriphy/compare/0.4.0...0.5.0)</small>

### Features

- One install command for the research graph: reasoner and checker set up on first use from the pinned release, prebuilt checker on Linux, pinned commit and hash; README covers the graph ([949ddcd](https://github.com/georgedouzas/veriphy/commit/949ddcd55c4f50301fb1553e48ae04f003144456) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

### Docs

- Archive graph-first-use-setup with its specs synced; README and plugin pin 0.5.0 ([94ec41f](https://github.com/georgedouzas/veriphy/commit/94ec41fcbd50e64be677df29b4bb9e195b2f952b) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- graph-first-use-setup tasks complete, CI green with first-use setup from an empty cache ([08e2f17](https://github.com/georgedouzas/veriphy/commit/08e2f17cc8c87331fb44b1c6679de958a908cf4a) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Plan graph-first-use-setup: one install command for the research graph ([1c7c513](https://github.com/georgedouzas/veriphy/commit/1c7c5132fdbffe465be2755727b17bee21fdcd87) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

### Chore

- Release 0.5.0 ([33adcb0](https://github.com/georgedouzas/veriphy/commit/33adcb0ea6f4e7203725b4db3fab251615543bc3) by georgedouzas).

## [0.4.0](https://github.com/georgedouzas/veriphy/releases/tag/0.4.0) - 2026-11-01

<small>[Compare with 0.3.1](https://github.com/georgedouzas/veriphy/compare/0.3.1...0.4.0)</small>

### Features

- Lean export #veriphy_graph, the research skill and playbook, the graph in CI, and the research graph documented ([7f51354](https://github.com/georgedouzas/veriphy/commit/7f51354ee2581aa9e505078ba74a7ba9191f98b7) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Research claim graph: vocabulary, project graph with provenance, certified reasoning checked by oo-horn, levels, impact, plans, clashes, slices and appendix ([d4b7e5e](https://github.com/georgedouzas/veriphy/commit/d4b7e5edd2b80331871353ed5333eef003d3e1d1) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

### Docs

- Archive research-claim-graph with its specs synced; README and plugin pin 0.4.0 ([d0d3cea](https://github.com/georgedouzas/veriphy/commit/d0d3ceafd9169d2856a6489b972887250236e191) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- research-claim-graph tasks complete, CI green with the checker ([90f2806](https://github.com/georgedouzas/veriphy/commit/90f280614e3a1b11097f149389e847c42f911adb) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Changelog for the research claim graph; Project Profile names veriphy.graph ([a171285](https://github.com/georgedouzas/veriphy/commit/a171285cece8899dfaf275d8dad29c46ce96491c) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Plan research-claim-graph: a certified research claim graph with Open Ontologies ([07b2f76](https://github.com/georgedouzas/veriphy/commit/07b2f76664952274c88b0dcf6f7ea10a32352396) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

### Chore

- Release 0.4.0 ([5c9b87f](https://github.com/georgedouzas/veriphy/commit/5c9b87f9d3f87e3edad56560d2a37fda58b9f5bc) by georgedouzas).

## [0.3.1](https://github.com/georgedouzas/veriphy/releases/tag/0.3.1) - 2026-10-18

<small>[Compare with 0.3.0](https://github.com/georgedouzas/veriphy/compare/0.3.0...0.3.1)</small>

### Bug Fixes

- Re-parse a replacement only when a line ends in ';' and the text is small ([da8bc16](https://github.com/georgedouzas/veriphy/commit/da8bc16c5c56a32ab5c3e517c48987aef6137cd1) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Exact algebraic values in oracle instances, boolean edge flags, supplied proofs override stated conditions ([1267025](https://github.com/georgedouzas/veriphy/commit/12670258b9ea8c98713c15275fd202d3db6326d0) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Translation and emission bugs found by the book's certification ([d9e241f](https://github.com/georgedouzas/veriphy/commit/d9e241f8d12300ee40fda5bda6aa8f9778cf5186) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

### Chore

- Release 0.3.1 ([90e84fb](https://github.com/georgedouzas/veriphy/commit/90e84fb0a132f8dc6ca70b17cde343f3413b6db9) by georgedouzas).

## [0.3.0](https://github.com/georgedouzas/veriphy/releases/tag/0.3.0) - 2026-10-16

<small>[Compare with 0.2.0](https://github.com/georgedouzas/veriphy/compare/0.2.0...0.3.0)</small>

### Features

- sage_test fallback: claims tested at kernel-checked or oracle instances, independent of the claim, with levels, records, #veriphy_levels and the test_fallback recipe ([afa84e6](https://github.com/georgedouzas/veriphy/commit/afa84e6d8e30167fdf23d4cb2f5aa9aac50fc4a4) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Linear-algebra certificates: independence, spans and kernels, matrix rank, dimensions (spans, intersections, kernels, products), non-linearity, signatures; packaging lemmas with the standard axioms ([85758cf](https://github.com/georgedouzas/veriphy/commit/85758cf86bdd1a63bf878e6c21fcac78386be620) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- definite_integral recipe: interval integrals in the translation, antiderivatives from Sage, endpoint facts at multiples of pi ([824efd9](https://github.com/georgedouzas/veriphy/commit/824efd9701a42d2a668c39cb03ee6b74e8462892) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Trigonometric power-reduction, multiple-angle and Pythagorean rewrites in the core table; transcendental_rewrite tries every candidate ([4e756a5](https://github.com/georgedouzas/veriphy/commit/4e756a5d8ea14250bc2b83b098e65ecccb4c1f02) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- matrix_from_goal for any size, transposes, vectors and side relations (cofactors over opaque functions) ([d9e00ec](https://github.com/georgedouzas/veriphy/commit/d9e00ec0b490ed37c75f9b24cb27b2fe9f367735) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Replacement only for accepted blocks; vectors, named matrices and polynomials in the translation ([74abb66](https://github.com/georgedouzas/veriphy/commit/74abb6687b25a5567477d7cbfe6e5b40defd5eba) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

### Bug Fixes

- Endpoint values at zero by simp; the pilot's remaining goal shapes as tests; task 6.1 states Veriphy's part ([eab4d61](https://github.com/georgedouzas/veriphy/commit/eab4d616e331feba41edc492da2ef6ccd3ed6b27) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Wrap the parsed block in veriphy_certified, keeping parse errors at the script's own columns ([1a803d2](https://github.com/georgedouzas/veriphy/commit/1a803d280020cb5f45691d43b88116c283d135d2) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Align multi-line certified blocks; order-robust doctests; numpy as a Sage-provided module; coverage after book coverage ([08c2061](https://github.com/georgedouzas/veriphy/commit/08c2061a0377f3d367a343b36baa9719e8adba90) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Blocks declare the goals they leave open (rewrite steps); probes see integrals; typing ([2c49ddc](https://github.com/georgedouzas/veriphy/commit/2c49ddc0325717a864614754b652a3e84c70ef07) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

### Docs

- Archive kk-csdr-book-coverage with its specs synced; README pins 0.3.0 ([afb5914](https://github.com/georgedouzas/veriphy/commit/afb5914f0b7bbbfb2b26dd609a7957818d8a3b3a) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Test fallback and verification levels, linear algebra, matrix goals and integrals in the guide and the components page; changelog ([e88c563](https://github.com/georgedouzas/veriphy/commit/e88c563210b5e5238a50e9b8fd5388562a94a5bb) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Propose the book coverage change (recipes the KK/CSDR book needs) ([b912a19](https://github.com/georgedouzas/veriphy/commit/b912a19bb01ae154387a056a4c1a41b821873fd7) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

### Chore

- Release 0.3.0 ([d85b562](https://github.com/georgedouzas/veriphy/commit/d85b5624e0af3df7039d18026c7105a1bbc08e7c) by georgedouzas).

## [0.2.0](https://github.com/georgedouzas/veriphy/releases/tag/0.2.0) - 2026-10-13

<small>[Compare with 0.1.0](https://github.com/georgedouzas/veriphy/compare/0.1.0...0.2.0)</small>

### Features

- Symbolic coverage: translation tables, coverage measurement, kernel checkers and components for Lie theory, representations, superalgebras, algebraic certificates, operators, geometry, summation, numerics and fusion categories ([2482bf8](https://github.com/georgedouzas/veriphy/commit/2482bf8efec7b52a277bf5df9e816662e01286f9) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

### Docs

- Pin the 0.2.0 release in the setup instructions ([1441ecb](https://github.com/georgedouzas/veriphy/commit/1441ecb00db4a0437ff6723d60e9b136f3bc1b04) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

### Chore

- Release 0.2.0 ([7dd25bc](https://github.com/georgedouzas/veriphy/commit/7dd25bcfe5eaec767577b7b412c60a105b5f344d) by georgedouzas).

## [0.1.0](https://github.com/georgedouzas/veriphy/releases/tag/0.1.0) - 2026-10-12

<small>[Compare with first commit](https://github.com/georgedouzas/veriphy/compare/1429e93b13a61dec8d7a6b6bdb0271bc346a56c1...0.1.0)</small>

### Docs

- Pin the first release, 0.1.0, in the setup instructions ([6aba0ca](https://github.com/georgedouzas/veriphy/commit/6aba0cac92951bd71d93b5ff3436bd72e534b8b3) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- record the founding design discussion as DESIGN.md ([5271a5e](https://github.com/georgedouzas/veriphy/commit/5271a5e4fa3bafe371bc1dd6f793ddfcd413417a) by georgedouzas). Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>

### Chore

- Release 0.1.0 ([e276264](https://github.com/georgedouzas/veriphy/commit/e276264c72e88389cbfe6414e3ad4d0f15873537) by georgedouzas).

