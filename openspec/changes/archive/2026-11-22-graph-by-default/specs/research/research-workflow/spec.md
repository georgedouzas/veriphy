## MODIFIED Requirements

### Requirement: Research skill
The plugin SHALL ship a `research` skill that leads the agent through extraction, triage, proving, export and
reporting for one source, using the graph CLI at each step, and SHALL work with Veriphy installed and Sage absent for
every step except proving.

#### Scenario: Running the skill on a chapter
- **WHEN** a user asks the agent to verify `chapter9.tex` with the research skill
- **THEN** the agent extracts the claims, triages them, proves what it can, exports the Lean claims, and writes the
  appendix for `chapter9`
