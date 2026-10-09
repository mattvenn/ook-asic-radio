"""Build the interactive floorplan page (a claude.ai artifact) from its sources:
layout/floorplan/page/page.html + engine.js + the block data (blocks.json, tile.json).

    python3 tools/floorplan_page.py [out.html] [--dev]

--dev also embeds layout/floorplan/variants.json so the page shows the variants without the
artifact's shared store (for a local preview). The published page reads its variants from the
store, which Claude seeds from variants.json.
"""
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
FP = os.path.join(ROOT, 'layout', 'floorplan')
CELLS = ['log_det', 'lpf_rc', 'avg_sc', 'comp_ct', 'r2r', 'bias_gen', 'dbg_tg', 'tx_ring', 'tx_ls',
         'tx_ls_en', 'tx_drv', 'lna_chain']


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    out = args[0] if args else os.path.join(FP, 'page', 'floorplan.html')
    blocks = json.load(open(os.path.join(FP, 'blocks.json')))
    data = {'tile': json.load(open(os.path.join(FP, 'tile.json'))), 'cells': {k: blocks[k] for k in CELLS}}
    page = open(os.path.join(FP, 'page', 'page.html')).read()
    js = 'window.FP_DATA = ' + json.dumps(data, separators=(',', ':')) + ';'
    if '--dev' in sys.argv:
        js += '\nwindow.FP_DEV_VARIANTS = ' + json.dumps(json.load(open(os.path.join(FP, 'variants.json')))['variants']) + ';'
    page = page.replace('<script>/*DATA*/</script>', '<script>' + js + '</script>')
    page = page.replace('<script>/*ENGINE*/</script>', '<script>' + open(os.path.join(FP, 'page', 'engine.js')).read() + '</script>')
    with open(out, 'w') as fh:
        fh.write(page)
    print(out, len(page), 'bytes')


if __name__ == '__main__':
    main()
