v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {decap_vdpwr: MOS caps (gate VDPWR; S/D/B VGND; L 5, thin 01v8) + MIM caps (top plate VDPWR), as laid out} -300 -330 0 0 0.4 0.4 {}
T {16 MOS, gate 993 um2 (~7.8 pF) + 4 MIM, 1327 um2 (~2.7 pF): ~11 pF} -300 -290 0 0 0.3 0.3 {}
T {Planned: n = 30 units of 2 x W10/L5 thin MOS + one 10 x 10 um MIM: 60 MOS (gate 3000 um2) + 30 MIM (3000 um2), ~30 pF.} -300 180 0 0 0.3 0.3 {}
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
N 660 -30 660 -100 {}
N -300 -100 -20 -100 {}
N -20 -100 200 -100 {}
N 200 -100 420 -100 {}
N 420 -100 660 -100 {}
N 20 30 20 100 {}
N 240 30 240 100 {}
N 460 30 460 100 {}
N 660 30 660 100 {}
N -300 100 20 100 {}
N 20 100 240 100 {}
N 240 100 460 100 {}
N 460 100 660 100 {}
C {devices/iopin.sym} -300 -100 0 1 {name=p1
lab=VDPWR}
C {devices/iopin.sym} -300 100 0 1 {name=p2
lab=VGND}
C {sky130_fd_pr/nfet3_01v8.sym} 0 0 0 0 {name=Mcap1
nf=2
mult=7
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
W=17.6
model=nfet_01v8
spiceprefix=X}
C {sky130_fd_pr/nfet3_01v8.sym} 220 0 0 0 {name=Mcap2
nf=1
mult=6
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
W=8.5
model=nfet_01v8
spiceprefix=X}
C {sky130_fd_pr/nfet3_01v8.sym} 440 0 0 0 {name=Mcap3
nf=1
mult=3
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
W=8.15
model=nfet_01v8
spiceprefix=X}
C {sky130_fd_pr/cap_mim_m3_1.sym} 660 0 0 1 {name=Cmim1
model=cap_mim_m3_1
W=17
L=19.52
MF=4
spiceprefix=X}
