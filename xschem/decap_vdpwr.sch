v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {decap_vdpwr: n units of MOS cap (gate VDPWR; S/D/B VGND; 2 x W10/L5, thin 01v8) + 10x10 um MIM above (top plate VDPWR)} -500 -460 0 0 0.4 0.4 {}
C {devices/iopin.sym} -500 -360 0 0 {name=p1
lab=VDPWR}
C {devices/iopin.sym} -500 -330 0 0 {name=p2
lab=VGND}
C {sky130_fd_pr/nfet_01v8.sym} 0 0 0 0 {name=Mcap
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
L=5
W=10
model=nfet_01v8
spiceprefix=X}
C {devices/lab_pin.sym} 20 -30 0 1 {name=p3
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} -20 0 0 0 {name=p4
sig_type=std_logic
lab=VDPWR}
C {devices/lab_pin.sym} 20 30 0 1 {name=p5
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} 20 0 0 1 {name=p6
sig_type=std_logic
lab=VGND}
C {sky130_fd_pr/cap_mim_m3_1.sym} 200 0 0 0 {name=Cmim
model=cap_mim_m3_1
W=10
L=10
MF='n'
spiceprefix=X}
C {devices/lab_pin.sym} 200 -30 0 1 {name=p7
sig_type=std_logic
lab=VDPWR}
C {devices/lab_pin.sym} 200 30 0 1 {name=p8
sig_type=std_logic
lab=VGND}
