#!/bin/sh
# Render the D2 sources of the architecture documentation to the SVG files the docs embed. Files starting with `_`
# or named `legend.d2` are imports, not diagrams.
set -e
cd "$(dirname "$0")/../docs/architecture/diagrams"
for source in *.d2; do
  case "$source" in _*|legend.d2) continue ;; esac
  d2 --layout elk --theme 0 --pad 24 "$source" "${source%.d2}.svg"
done
