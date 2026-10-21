# Interactive explainer: source

Generates the self-contained [`../explainer.html`](../explainer.html) (one file, ~600 kB with the layout image; the only network use is Google Analytics and the newsletter sign-up, below) from the simulations, bench data and link model in this repo. Same pattern as [metastability_explorer](https://github.com/mattvenn/metastability_explorer): `template.html` holds the page, and `gendata.py` replaces its `/*__PAYLOAD__*/` token with the data (traces resampled, quantized to 1 byte, gzipped, base64). The browser inflates it with `DecompressionStream('gzip')`.

Open it from the repo: <https://mattvenn.github.io/ook-asic-radio/docs/explainer.html> (the gds workflow adds the committed file to the gds_render artifact, which the TT viewer job deploys as the Pages site).

## Run
```
tools/osic-mac docs/explainer/sims.sh     # ~3 min; tools/osic on Linux. Raws land in build/ (gitignored)
python3 docs/explainer/gendata.py         # ~10 s; writes docs/explainer.html
```
`gendata.py` prints each source and marks any missing raw. That view then shows a "no data" note and the page still builds.

The chip page and the per-block maps draw the system diagram from the floorplan tool's "Block diagram" view (`layout/floorplan/page/page.html`, `DG`); its block boxes and wires are copied into `template.html` (`DG`). Move a block there and copy the new coordinates here.

## Sources
| View | Source |
|---|---|
| top bar: Zero to ASIC brand | `brand_header.jpg`: the Zero to ASIC header art (`brands/zerotoasic/www_header.jpeg`), cropped to a strip, 960 px JPEG; `gendata.py` puts it in place of `/*__BRAND__*/`. The logo is inline SVG in `template.html`; colours (`--z2a-*`, violet-grey neutrals) and the Avenir Next font come from the same brand kit |
| opening page: whole-design layout | `layout.jpg`: the GitHub `gds` action's `gds_render` artifact (`gds_render.png`), scaled to 1200 px wide JPEG. Refresh it from a recent run after a layout change |
| received power → estimated distance | `bench/data/sweep2/ota.csv` fit (−44 dBm at 1 m, 1/d^1.89, measured 10 cm–4 m with the old ttsky25b transmitter), shifted up by the new transmitter's simulated power (`TX_DB` = +3.5 − (−8.5) = 12 dB) up to the ground-reflection breakpoint (5.8 m for both boards 1 m up at 433.92 MHz), then the two-ray model (40 dB/decade). Constants in `template.html` (`HGT`, `DB`) |
| TX ring, level-shifter A/B, drivers, dipole | `build/tb_tx_ab.raw` from `xschem/tb_tx.sch` (tt, schematic) |
| RX antenna → 6 stages → det (−60 dBm tone, keyed) | `build/rx_rf_tone.raw`, `rx_rf_key.raw` from `sim/rx/rf.sh` |
| log detector transfer, per-tap amplitude | `sim/logdet/taps.txt`, `transfer_cw.txt` |
| baseband det → lpf → avg → comparator, trim (−70 / −94 dBm) | `build/rx_bb_<lvl>.raw` from `sim/rx/gen_det.py` + `sim/rx/bb.sh` |
| sent vs received chips, score, 2-of-3, LED rate (follows the received-power slider) | `model/` link model at 2 dB steps, −110 to −26 dBm: 12 sends of code 0x5A per level, tt with the H135 comparator as `e2e_h135_tt` in `sim/rerun/jobs_2026-10-13.py` (NF 11 dB / 450 MHz noise, 13.4 mV/dB, 1.26 mV offset, 0.127 mV trim, 0.3 mV comparator noise), bit-exact `radio.RxDigital`. The LED readouts show how many of the 12 toggled; the page replays one send per level, one whose outcome is the majority's. `MODEL` in `gendata.py`; the sweep (~2 min on 8 cores) is cached in `build/explainer_model.json` and reruns when `MODEL` changes |
| sensitivity line, margin (`SENS` in `template.html`) | −92 dBm: ≥ 99 % of chips at every corner, 10–50 °C (`docs/verify_2026-10-13.md`); the model sweep gives 12/12 at −92 and 7/12 at −94 dBm |
| block page sizes, opening-page totals | `sizes.json` from `tools/osic python3 docs/explainer/sizes.py`: analog = each `layout/*.gds` bounding box, times how many `layout/floorplan/floorplan.json` places; digital = cells per RTL module after a yosys synthesis with the hierarchy kept (sky130_fd_sc_hd tt), and the hardened macro's cells from `macros/radio_digital/radio_digital.nl.v` (fill, tap, decap and diode cells not counted). Rerun after a layout or RTL change |

`sims.sh` stubs `pyvisa` (pulled in through `bench/scope.py`) so `gen_det.py` runs in the osic image.

## Editing
**Words** (headings, page text, tour captions) are in [`text.md`](text.md), one section per page in tour order; the format and the `{placeholders}` for simulated numbers are described in `textfile.py`. Two ways to change them:
- Edit `text.md` and rebuild with `gendata.py`.
- Type into the page: `python3 docs/explainer/edit.py`, open <http://localhost:8000/>, press `e`. Headings, subtitles, page text and the tour caption (bar at the bottom) become editable; each edit saves to `text.md` and `explainer.html` is rebuilt in the background. `e` again shows the result. Commit `text.md` and `explainer.html` afterwards.

**Everything else** (figures, tour order, the block diagram) is in `template.html`: `B` (each page's plot and links), `TOUR` (order), `fig*` functions. Rebuild with `gendata.py` after editing.

## Analytics and newsletter
- **Google Analytics 4**: `GA_ID` in `template.html` is the stream zerotoasiccourse.com reports to (`G-2HQ02ESFZB`, set inside its tag manager `GTM-PL32RC6`). It loads only on a real web host, so not from `file:`, localhost or `edit.py`. Events: `explainer_step` (`page`, `step`), `explainer_power` (`dbm`, on slider release), `explainer_dip`, `explainer_zoom`, `newsletter_shown` / `newsletter_subscribe` (`result`) / `newsletter_dismiss` (`how`). To see the parameters in GA reports, register them as custom dimensions (Admin › Custom definitions).
- **Newsletter box**: after `NL_AFTER` (10) interactions (a new page, a slider release, a DIP or zoom click) the page offers the Zero to ASIC newsletter once. Closing it or subscribing keeps it away for `NL_QUIET_DAYS` (30) in that browser (`localStorage`). It posts to the same Mailchimp list, interest groups and tag as the website's form, through Mailchimp's JSONP endpoint, so the reader stays on the page. When Mailchimp answers `captcha` (it can't show one over JSONP), the box offers a Continue button that posts the same fields to its normal sign-up page in a new tab, where it shows the captcha. The footer's Newsletter link opens it any time, and `?nl` in the URL opens it on load for testing.

## Publishing
The page is served at <https://zerotoasiccourse.com/radio/>, the address its social-preview tags (`og:*`, `twitter:card`, canonical) point to. `docs/explainer/publish.sh` copies `explainer.html` and `og-image.png` (1200×630: `layout.jpg`, the chip floorplan from step 1, centred on the page background) into the website repo's `static/radio/`; commit there and deploy with its `build.sh`. The GitHub Pages copy still updates on every push, and its canonical link points search engines to the website. After a deploy, check the preview with each platform's card validator (LinkedIn Post Inspector, the Facebook Sharing Debugger): they cache the first version they see.
