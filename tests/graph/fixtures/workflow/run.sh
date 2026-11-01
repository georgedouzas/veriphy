#!/bin/sh
# The research workflow end to end on the fixture chapter, from a workspace whose Lean export holds GraphTest.
# Usage: run.sh <python running veriphy.graph>
set -eu
PY="$1"
FIXTURES="$(dirname "$0")"
mkdir -p .veriphy/graph/sources
cp "$FIXTURES/chapter.agent.ttl" .veriphy/graph/sources/chapter.agent.ttl
$PY -m veriphy.graph validate
$PY -m veriphy.graph reason
$PY -m veriphy.graph levels --source chapter
$PY -m veriphy.graph impact chapter metric-three | grep -q 'eq-2'
$PY -m veriphy.graph slice chapter thm-3 | grep -q 'metric-three'
$PY -m veriphy.graph appendix chapter --format latex
grep -q 'verdict entailed' .veriphy/graph/appendix/chapter.tex
echo 'research workflow: every step succeeded, appendix verdict entailed'
