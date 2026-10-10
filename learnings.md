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
