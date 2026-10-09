# pin_order.cfg

LibreLane io_place syntax: `#N`/`#S`/`#E`/`#W` sides (N/S left → right, E/W bottom → top; `#NR` etc. reversed), one anchored regex per line, `$n` = n empty slots, `@min_distance=x`. **No comment lines**: anything starting with `#` is read as a side directive.

radio_digital pin order (LibreLane io_place: N/S left -> right, E/W bottom -> top;
names are anchored regexes; $n = n empty slots).
Assumed floorplan (3x2 tile, 493 x 226 um): the macro at the right end of the
tile, the analog to its west. In the tile, the TT digital pins are along the
top edge at x 15..131 um and ua[0..7] along the bottom at x 1..137 um, so
everything the macro talks to is north-west / west of it.
North: the TT pins, in the template's left-to-right order (uio_oe[7] at
x 15 ... clk at x 128; ena unused), clustered at the west end so the wires
fan in from the top-left without crossing. clk is the east-most of them,
nearest its TT pin.
West: the analog interface, bottom -> top roughly as the analog blocks sit:
TX enables lowest (TX next to ua[0]/ua[1] under the old pin map; since 2026-10-09 TX is on ua[3]/ua[4] and RX on ua[0]/ua[1]), then the RX bias / debug
enables, then the comparator and averager (comp_in, sc_phi1/2), then the
trim DAC bits contiguous in the ladder's b0 -> b7 order. Empty slots above
keep them in the lower part of the edge, away from the top-edge channel
where the TT signals and clk arrive.
