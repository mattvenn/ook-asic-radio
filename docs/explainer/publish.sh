#!/bin/sh
# Copy the built explainer and its social-preview image into the Zero to ASIC website,
# where it is served at https://zerotoasiccourse.com/radio/ (static/radio/ in the Hugo site).
# Then deploy the website as usual (its build.sh: hugo, then rsync to the server).
#   docs/explainer/publish.sh [path to zero-to-asic-www]     default: ../zero-to-asic-www next to this repo
set -e
here=$(cd "$(dirname "$0")" && pwd)
www=${1:-$here/../../../zero-to-asic-www}
[ -f "$www/config.toml" ] || { echo "no Hugo site at $www (pass its path)"; exit 1; }
mkdir -p "$www/static/radio"
cp "$here/../explainer.html" "$www/static/radio/index.html"
cp "$here/og-image.png" "$www/static/radio/og-image.png"
echo "copied to $www/static/radio/ ($(git -C "$here" log -1 --format='%h %s' -- ../explainer.html | cut -c1-70))"
echo "next: commit there, then run its build.sh to deploy"
