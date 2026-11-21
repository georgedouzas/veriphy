# Playbook: verify a research source with the claim graph

Agent-agnostic instructions. Per-agent adapters (`skills/research/`, `.claude/skills/research/`) point at this file.

The caller supplies one source: a LaTeX or Markdown draft, a chapter, or a paper, and the workspace it belongs to.
The playbook records the source's claims in the research claim graph, proves or tests what it can, and ends by
reporting the verification of every claim. What happens to the report is the caller's decision.

Paths in this playbook are relative to its directory, which `sage -python -m veriphy agents path` prints. The
playbooks ship with the installed `veriphy` package, at the version of its toolkit.

## Preconditions

- The graph extra is installed: `sage -pip install 'veriphy[graph]'`. The first `reason` sets up the reasoner and the
  checker by itself and says so. When `VERIPHY_GRAPH_SETUP=off` forbids that, run
  `sage -python -m veriphy claims checker build` first.
- The workspace is a Lean workspace that requires Veriphy. Every graph command runs from inside it.
- Only step 4 needs Sage. Without a checker the playbook still runs, and every graph result is reported `unchecked`.

## Loop

1. **Extract.** Follow `research/extraction.md`. Write the source's claims, conventions, concepts and
   dependencies to `.veriphy/graph/sources/<source>.agent.ttl`. Never write to a `.human.ttl` file: those are the
   caller's.

2. **Validate.** Run `sage -python -m veriphy claims validate` and fix every violation in the agent file. The SHACL
   report is a measurement, so a clean report means the file is complete, not that it is right.

3. **Triage.** Follow `research/triage.md`. Record each claim's group with `vp:triage`. Do not try to prove a
   `suspect` claim.

4. **Prove.** For each claim in the `recipe`, `test` or `formalize` group, in dependency order (a claim after the
   claims it uses):
   1. Print its context: `sage -python -m veriphy claims slice <source> <label>`. The slice names the conventions the
      claim assumes and the Lean definitions that realize them. State the claim in Lean under exactly those
      definitions. If the command refuses the slice, report the lost consequences to the caller and stop on this
      claim.
   2. Follow `prove.md` (and `certify.md` for certificates) to prove it, or `#veriphy test` it when no
      certificate is feasible.
   3. Link it: add `vp:formalizedBy <urn:veriphy:lean:<Lean name>>` to the claim in the agent file.

5. **Export.** In a Lean file of the workspace, run `#veriphy export <prefix>` for the prefix of the new declarations.
   It writes `.veriphy/graph/lean/<prefix>.nt` with the levels and dependencies Lean knows.

6. **Reason and report.** Run, in order:
   - `sage -python -m veriphy claims reason`, which must print `verdict: entailed`, else report the status;
   - `sage -python -m veriphy claims excludes` and show the proposals to the caller, who confirms them with `--confirm`;
   - `sage -python -m veriphy claims clashes`;
   - `sage -python -m veriphy claims levels --source <source>`;
   - `sage -python -m veriphy claims appendix <source> --format latex` (or `markdown`).

7. **Report to the caller.** Give the appendix path and, per claim, its group and effective level. Name every clash,
   every `suspect` claim with its counterexample, and every claim capped below its own level with the claim that caps
   it. Say whether the run was checked. Never report a claim as proved when its effective level is below
   `lean-proof`, and never call an unchecked result checked.

## Rules

- The agent writes only `.agent.ttl` files. Confirming an assertion, which moves it to the `.human.ttl` file, is the
  caller's act through `veriphy claims confirm`.
- A graph conclusion is reported with the checker's verdict word, or as `unchecked`. The absence of a clash is never
  reported as checked.
- `formalizedBy` claims that the Lean statement says what the prose says. Make that claim only after the round-trip
  check of `prove.md` step 1.
