#!/bin/bash
# One-shot setup for a fresh pod running inside the IIC-OSIC-TOOLS image (e.g. sim-0): everything
# under $HOME is lost with the pod, so rerun this on each new one. Idempotent.
#   bash tools/pod_setup.sh
# - git identity and push credentials for this repo. The token comes from $GITHUB_TOKEN (a fine-grained
#   token for this repo, Contents read/write, set in the pod spec from a k8s Secret); nothing is stored.
# - magic 8.3.642 in ~/.local/magic642 (the 2026.09 image's 8.3.684 drops node-to-substrate C from
#   ext2spice; extract with OSIC_MAGIC=$HOME/.local/magic642/bin, see docs/verification.md). ~5 min.
# - pyvisa (sim/rx/gen_det.py imports bench/, which needs it).
set -e
REPO=$(cd "$(dirname "$0")/.." && pwd -P)
cd "$REPO"

git config user.name "Matthew Venn"
git config user.email "matt@mattvenn.com"
git config credential.helper '!f(){ echo username=x-access-token; echo "password=$GITHUB_TOKEN"; }; f'
[ -n "${GITHUB_TOKEN:-}" ] || echo "WARNING: GITHUB_TOKEN not set: git push will fail until it is"

P=$HOME/.local/magic642
if [ "$("$P/bin/magic" --version 2>/dev/null)" != 8.3.642 ]; then
  S=$HOME/src; mkdir -p "$S"; cd "$S"
  [ -d tcl8.6.14 ] || curl -sSfL https://prdownloads.sourceforge.net/tcl/tcl8.6.14-src.tar.gz | tar xz
  [ -d tk8.6.14 ] || curl -sSfL https://prdownloads.sourceforge.net/tcl/tk8.6.14-src.tar.gz | tar xz
  (cd tcl8.6.14/unix && ./configure --prefix="$P" --enable-shared && make -j8 && make install) > build_tcl.log 2>&1
  (cd tk8.6.14/unix && ./configure --prefix="$P" --with-tcl="$P/lib" --enable-shared && make -j8 && make install) > build_tk.log 2>&1
  [ -d magic ] || git clone -q https://github.com/RTimothyEdwards/magic.git
  (cd magic && git checkout -q 8.3.642 && git clean -fdxq &&
   ./configure --prefix="$P" --with-tcl="$P/lib" --with-tk="$P/lib" --disable-cairo &&
   make -j8 && make install) > build_magic.log 2>&1
  cd "$REPO"
fi
echo "magic: $("$P/bin/magic" --version) in $P/bin"

python3 -c 'import pyvisa' 2>/dev/null || pip install --user -q pyvisa
python3 -c 'import numpy, cocotb, pyvisa; print("python: numpy", numpy.__version__, "cocotb", cocotb.__version__, "pyvisa ok")'

# CPU quota: nproc shows the node, not the pod. Each ngspice uses 8 threads: run ~quota/3 at once.
q=$(cat /sys/fs/cgroup/cpu.max 2>/dev/null || echo max)
case $q in max*) echo "CPU quota: none (nproc $(nproc))";;
  *) echo "CPU quota: $(( ${q% *} / ${q#* } )) CPUs (nproc $(nproc)): keep ngspice runs to about a third of that";;
esac
