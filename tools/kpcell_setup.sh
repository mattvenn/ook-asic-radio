#!/bin/bash
# The sky130 KLayout pcells (Mabrains, in the PDK) need gdsfactory 8.x; the tools image
# has 9.x. Install 8.5 into build/pyold (layout/gen/lay.py puts it first on sys.path).
# KLayout's own 'klayout' module must win, so the pip copy is removed.
# Run once: tools/osic bash tools/kpcell_setup.sh
set -e
pip install --target build/pyold "gdsfactory==8.5.0"
rm -rf build/pyold/klayout build/pyold/klayout-* build/pyold/klayout.libs
