v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {decap_vapwr: MOS caps (gate VAPWR; S/D/B VGND; L 5, thick g5v0d10v5) + MIM caps (top plate VAPWR), as laid out} -300 -330 0 0 0.4 0.4 {}
T {87 MOS, gate 6748 um2 (~19.6 pF) + 46 MIM, 11159 um2 (~23.0 pF): ~43 pF} -300 -290 0 0 0.3 0.3 {}
T {Planned: n = 100 units of 2 x W10/L5 thick MOS + one 10 x 10 um MIM: 200 MOS (gate 10000 um2) + 100 MIM (10000 um2), ~50 pF.} -300 180 0 0 0.3 0.3 {}
T {Reduced to what fits the 6-tile area (layout/gen/decap.py fills the floorplan's decap parts).} -300 210 0 0 0.3 0.3 {}
N -20 0 -20 -100 {}
N 20 -30 80 -30 {}
N 80 -30 80 30 {}
N 80 30 20 30 {}
N 200 0 200 -100 {}
N 240 -30 300 -30 {}
N 300 -30 300 30 {}
N 300 30 240 30 {}
N 420 0 420 -100 {}
N 460 -30 520 -30 {}
N 520 -30 520 30 {}
N 520 30 460 30 {}
N 640 0 640 -100 {}
N 680 -30 740 -30 {}
N 740 -30 740 30 {}
N 740 30 680 30 {}
N 880 -30 880 -100 {}
N 1100 -30 1100 -100 {}
N 1320 -30 1320 -100 {}
N 1540 -30 1540 -100 {}
N 1760 -30 1760 -100 {}
N -300 -100 -20 -100 {}
N -20 -100 200 -100 {}
N 200 -100 420 -100 {}
N 420 -100 640 -100 {}
N 640 -100 880 -100 {}
N 880 -100 1100 -100 {}
N 1100 -100 1320 -100 {}
N 1320 -100 1540 -100 {}
N 1540 -100 1760 -100 {}
N 20 30 20 100 {}
N 240 30 240 100 {}
N 460 30 460 100 {}
N 680 30 680 100 {}
N 880 30 880 100 {}
N 1100 30 1100 100 {}
N 1320 30 1320 100 {}
N 1540 30 1540 100 {}
N 1760 30 1760 100 {}
N -300 100 20 100 {}
N 20 100 240 100 {}
N 240 100 460 100 {}
N 460 100 680 100 {}
N 680 100 880 100 {}
N 880 100 1100 100 {}
N 1100 100 1320 100 {}
N 1320 100 1540 100 {}
N 1540 100 1760 100 {}
C {devices/iopin.sym} -300 -100 0 1 {name=p1
lab=VAPWR}
C {devices/iopin.sym} -300 100 0 1 {name=p2
lab=VGND}
C {sky130_fd_pr/nfet3_g5v0d10v5.sym} 0 0 0 0 {name=Mcap1
nf=2
mult=32
ad="'int((nf+1)/2) * W/nf * 0.29'"
pd="'2*int((nf+1)/2) * (W/nf + 0.29)'"
as="'int((nf+2)/2) * W/nf * 0.29'"
ps="'2*int((nf+2)/2) * (W/nf + 0.29)'"
nrd="'0.29 / W'"
nrs="'0.29 / W'"
sa=0
sb=0
sd=0
body=VGND
L=5
W=19.8
model=nfet_g5v0d10v5
spiceprefix=X}
C {sky130_fd_pr/nfet3_g5v0d10v5.sym} 220 0 0 0 {name=Mcap2
nf=2
mult=8
ad="'int((nf+1)/2) * W/nf * 0.29'"
pd="'2*int((nf+1)/2) * (W/nf + 0.29)'"
as="'int((nf+2)/2) * W/nf * 0.29'"
ps="'2*int((nf+2)/2) * (W/nf + 0.29)'"
nrd="'0.29 / W'"
nrs="'0.29 / W'"
sa=0
sb=0
sd=0
body=VGND
L=5
W=16.6
model=nfet_g5v0d10v5
spiceprefix=X}
C {sky130_fd_pr/nfet3_g5v0d10v5.sym} 440 0 0 0 {name=Mcap3
nf=2
mult=38
ad="'int((nf+1)/2) * W/nf * 0.29'"
pd="'2*int((nf+1)/2) * (W/nf + 0.29)'"
as="'int((nf+2)/2) * W/nf * 0.29'"
ps="'2*int((nf+2)/2) * (W/nf + 0.29)'"
nrd="'0.29 / W'"
nrs="'0.29 / W'"
sa=0
sb=0
sd=0
body=VGND
L=5
W=12.6
model=nfet_g5v0d10v5
spiceprefix=X}
C {sky130_fd_pr/nfet3_g5v0d10v5.sym} 660 0 0 0 {name=Mcap4
nf=2
mult=9
ad="'int((nf+1)/2) * W/nf * 0.29'"
pd="'2*int((nf+1)/2) * (W/nf + 0.29)'"
as="'int((nf+2)/2) * W/nf * 0.29'"
ps="'2*int((nf+2)/2) * (W/nf + 0.29)'"
nrd="'0.29 / W'"
nrs="'0.29 / W'"
sa=0
sb=0
sd=0
body=VGND
L=5
W=11.6
model=nfet_g5v0d10v5
spiceprefix=X}
C {sky130_fd_pr/cap_mim_m3_1.sym} 880 0 0 1 {name=Cmim1
model=cap_mim_m3_1
W=15.44
L=19.8
MF=3
spiceprefix=X}
C {sky130_fd_pr/cap_mim_m3_1.sym} 1100 0 0 1 {name=Cmim2
model=cap_mim_m3_1
W=14.08
L=11.48
MF=4
spiceprefix=X}
C {sky130_fd_pr/cap_mim_m3_1.sym} 1320 0 0 1 {name=Cmim3
model=cap_mim_m3_1
W=19.05
L=15.8
MF=11
spiceprefix=X}
C {sky130_fd_pr/cap_mim_m3_1.sym} 1540 0 0 1 {name=Cmim4
model=cap_mim_m3_1
W=14.47
L=16.25
MF=12
spiceprefix=X}
C {sky130_fd_pr/cap_mim_m3_1.sym} 1760 0 0 1 {name=Cmim5
model=cap_mim_m3_1
W=11.58
L=18.69
MF=16
spiceprefix=X}
