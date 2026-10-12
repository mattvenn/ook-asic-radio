v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {decap_vdpwr: n units of MOS cap (gate VDPWR; S/D/B VGND; 2 x W10/L5, thin 01v8) + 10x10 um MIM above (top plate VDPWR)} -300 -260 0 0 0.4 0.4 {}
N -20 0 -20 -100 {}
N 20 -30 180 -30 {}
N 180 -30 180 30 {}
N 180 30 20 30 {}
N 350 -30 350 -100 {}
N -300 -100 -20 -100 {}
N -20 -100 350 -100 {}
N 20 30 20 100 {}
N 350 30 350 100 {}
N -300 100 20 100 {}
N 20 100 350 100 {}
C {devices/iopin.sym} -300 -100 0 1 {name=p1
lab=VDPWR}
C {devices/iopin.sym} -300 100 0 1 {name=p2
lab=VGND}
C {sky130_fd_pr/nfet3_01v8.sym} 0 0 0 0 {name=Mcap
nf=1
mult='2*n'
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
W=10
model=nfet_01v8
spiceprefix=X}
C {sky130_fd_pr/cap_mim_m3_1.sym} 350 0 0 1 {name=Cmim
model=cap_mim_m3_1
W=10
L=10
MF='n'
spiceprefix=X}
