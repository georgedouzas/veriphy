# Tasks

## 1. Levels

- [x] 1.1 Add `lean-proof` and the axiom check to `levelOf`, and move `standardAxioms` to `Levels` (D2). Verify with `lake build VeriphyTest.Kit VeriphyTest.Graph`: a plain proof is `lean-proof`, and a proof on `sorry` or another axiom is `none`, with or without the recipe marker.
- [x] 1.2 Add the level to the vocabulary and its order. Verify with `tests/graph/test_vocabulary.py` and `tests/graph/test_levels.py`, including the property test on random graphs.

## 2. Documents

- [x] 2.1 Update the recipe, the research playbook and both copies of the `research` skill. Verify that no document says a claim is proved only at `certificate`, with `git grep 'below .certificate'`.

## 3. Integration

- [x] 3.1 Run the gate on the changed files (formatting, checks, docs, tests). Verify that every session is green and that the change passes `openspec validate --strict`.

## Workflow follow-up

- Decide the open question in design.md, then archive the change and release it.
