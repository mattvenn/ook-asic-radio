![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/lvs/badge.svg)

# 433 MHz OOK radio on Tiny Tapeout (sky130, ttsky26d)

[![Made with Claude](https://img.shields.io/badge/Made%20with-Claude-D97757?logo=anthropic&logoColor=white)](https://claude.com/claude-code)

A mixed-signal Tiny Tapeout project: two demo boards with the same chip talk over the air with
bare-wire dipole antennas and no external components.

- **TX:** an on-chip ring oscillator at ~433 MHz, keyed on and off (OOK), with antiphase drivers into a dipole.
- **RX:** a 6-stage NMOS differential-pair limiting chain with a successive-detection log detector, and one comparator with an averaged, trimmed threshold. A digital Gold-code correlator detects the transmitter's code and toggles an LED.

Docs:
- [docs/how_it_works.md](docs/how_it_works.md): **start here**: theory, specs, schematics and layout.
- [Interactive explainer](https://raw.githack.com/mattvenn/ook-asic-radio/main/docs/explainer.html): click through the link, TX and RX chains with simulated waveforms ([source](docs/explainer)).
- [docs/verification.md](docs/verification.md): testing and verification, with links to every test.
- [PLAN.md](PLAN.md): the design plan and the measurements behind each decision.
- [docs/slicer.md](docs/slicer.md): how the receiver's comparator and trim servo work.
- [docs/info.md](docs/info.md): the datasheet (short test instructions).

## Layout of this repo
Follows the TT analog template flow used for `mattvenn/tt08-analog-r2r-dac-3v3`:

| Path | Contents |
|---|---|
| `info.yaml`, `docs/info.md`, `src/project.v` | TT project files; `src/project.v` is the LVS stub |
| `mag/` | Magic layout and the `make start / drc / lvs` flow (2x2 + VAPWR template) |
| `gds/`, `lef/` | Layout outputs |
| `xschem/`, `sim/` | Analog schematics, testbenches, ngspice runs |
| `verilog/rtl`, `verilog/test` | Digital macro `radio_digital` and its cocotb tests (vectors from the model) |
| `openlane/radio_digital` | Hardening config for the digital macro |
| `model/` | Bit-exact Python model and the RX performance studies |
| `bench/`, `stim/` | Phase-0 bench tools, measurements and recorded RF stimuli |
| `tools/osic` | Runs IIC-OSIC-TOOLS commands headless from this repo |

## Resources
- [Analog specs](https://tinytapeout.com/specs/analog/)
- [Tiny Tapeout](https://tinytapeout.com)
