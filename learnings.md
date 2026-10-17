# what I learnt

* how useful the ring oscillator was for testing OOK
* that my scope easily picks up FM radio
* the staged amp, how that works with each stage handing over to the next
* how the slicer / detector worked
* how we could use the scope to record the RF and then inject that into the models and the tests
* using gold codes like gpds to get longer range on the toggle mode
* lower range for serial transmission, but manchester encoding and CRC helps
* using matplotlib etc to model the whole chain and make predictions about range
* using differential antennas with 2 pins each for better signal tx and rx
* flops with clock gates to avoid adding a mux to each flop for the gold code comparitors


* layout was very automatic, proceeded by each block, with parasitics, lvs, drc, antenna checks
* took guidance from Harald's courses and my own learnings
* bias generator was suprisingly the most complex
* 3 different agents built on my mac, the cloud and my desktop

* floorplanning with a vibe coded tool made it much easier to get things in good position
* classic engineering compromise with position / fit / signal 
* initial power routing was terrible, magic can't do an extraction for this, use fasthenry,
* fast henry didn't work, used a combination of tools to get impedance and IR drop, needed quite a lot of fixing

* the interactive explainer was fun, and uses all the simulation files
* I need bigger computers!
* Monte Carlo showed the comparator trim range was too narrow; a chip past the end of the trim loses sensitivity but still works
* tuning the ring was more trouble than it was worth; measured silicon from ttsky25b was enough to set the frequency
* LVS can pass while device properties are wrong, so make property errors fail the run - due to circular logic, and was caught after Mitch Bailey took a look at LVS and CVC
* a job scheduler with a CPU budget made full reruns practical, still takes ~15 hours on the big computer from Ed

# timing

Wed 7 Oct: architecture and front-end sims
- Plan, models, TT analog template; digital RTL bit-exact against the model
- RX chain, log detector, LPF, comparator and averaging reference designed; end-to-end sim holds −94 dBm

Thu 8 Oct: TX, hardening, block layout
- TX ring, level shifter and drivers designed; RX corners at 10–50 °C
- Digital hardened with LibreLane and passes GL 15/15; mixed-signal sim detects −94 dBm
- Every leaf block laid out clean (DRC/LVS/PEX); floorplan page built

Fri 9 Oct: clean tile
- Floorplan chosen; blocks repinned and macro re-hardened
- Top level routed (93 nets): LVS clean, DRC 0, precheck pass; gds/lef exported
- Power-delivery study; how_it_works and verification docs

Sat 10 Oct: power fixes and explainer
- EM hotspot found, then fixed over three rounds; power-fix merged and re-exported
- Interactive explainer built
- Before the shuttle: TX frequency, extracted-tile runs, final precheck, first submission to ttsky26d

Mon 12 Oct: re-verification and the ring decision
- Full re-verification inside the IIC-OSIC-TOOLS image on sim-0
- Gave up on tuning the ring and kept NINV 22 (~448 MHz, calibrated on both ttsky25b rings)
- Started closing the verification gaps: pinout check, TT-level cocotb, supply sweeps, comparator Monte Carlo

Tue 13 Oct: comparator trim redesign
- System-level check on the extracted chip; findings table
- SymbiYosys formal proofs (TX/RX safety, correlator timing)
- Comparator trim redesigned (H135) and the inp stub fixed; tile rebuilt and re-exported; −94 dBm now measured, not estimated

Wed 14 Oct: full rerun and polish
- Full verification rerun with a new CPU-budget job scheduler
- Schematics redrawn the classical way, with device values shown

Fri 15 Oct: LVS tightening
- LVS now fails on property errors; decap schematics match the layout; chain stability rerun with the real VDPWR decap
