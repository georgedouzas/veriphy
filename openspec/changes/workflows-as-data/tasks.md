# Tasks

## 1. Engine

- [ ] 1.1 Add the workflow schema and its checks (D1). Verify with pytest: an undefined step, an unreachable entry and a transition to an unknown status are refused.
- [ ] 1.2 Add `next`, computed from records alone (D2, D4). Verify with pytest on record fixtures: each transition, an attempt limit, a `when` condition, and the same records giving the same answer.
- [ ] 1.3 Add `run`, stopping at agent steps (D3). Verify with pytest on fake steps: it runs evidence and check steps in order and stops at the first agent step with its request.

## 2. Workflows and skills

- [ ] 2.1 Define `prove-claim` and `verify-paper` in the `math` pack, and `reproduce-analysis` in the `reproduction` pack. Verify with `config check`, and with a test that each workflow's steps exist.
- [ ] 2.2 Rewrite the skills and playbooks to follow `next` and `run`, keeping guidance for agent steps only. Verify with the document tests and the research workflow fixture run through `run`.

## 3. Integration

- [ ] 3.1 Run the gate and CI. Verify that every session and job is green.

## Workflow follow-up

- Archive, and release as a minor version.
