# Tasks

## 1. Engine

- [x] 1.1 Add the workflow schema and its checks (D1). Verify with pytest: an undefined step and a transition to an entry the workflow does not have are refused.
- [x] 1.2 Add `next`, computed from records alone, in time order (D2, D4, D5). Verify with pytest on record fixtures: each transition, a return to an earlier entry, an attempt limit, a `when` condition, and the same records giving the same answer.
- [x] 1.3 Add `run`, stopping at agent steps (D3). Verify with pytest on a fixture pack: it runs evidence and check steps in order and stops at the first agent step with its request.

## 2. Workflows and skills

- [x] 2.1 Define `prove-claim` (with the agent step `prove`) and `verify-paper` in the `math` pack, and `reproduce-analysis` in the `reproduction` pack. Verify with `config check`, and with a test that each workflow's steps exist.
- [x] 2.2 Have the skills follow `next` and `run`, the playbooks keeping the guidance for agent steps. Verify with the document tests.

## 3. Integration

- [x] 3.1 Run the gate and CI. Verify that every session and job is green.

## Workflow follow-up

- Archive, and release as a minor version.
