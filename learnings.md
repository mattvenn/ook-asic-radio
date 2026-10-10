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
