v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {lna_shunt: low-gain strap across stage 2 outputs (a = o2p, b = o2n)
g = 0: PMOS on, Rh + Ron + Rh loads the stage (~11 dB less chain gain); g = VDD: off
params: rh (each Rh, high_po_1p41), wsw (PMOS W, L 0.15), rg (gate R, xhigh_po_0p35); Mcap ~210 fF} -400 -480 0 0 0.4 0.4 {}
T {R = 421 (L 0.621 um)} 225 -162 0 0 0.25 0.25 {}
T {R = 421 (L 0.621 um)} 225 78 0 0 0.25 0.25 {}
T {= 1 x 18 / 0.15} 205 -42 0 0 0.25 0.25 {}
T {R = 20k (L 2.71 um)} -125 58 0 0 0.25 0.25 {}
N 200 -230 200 -260 {}
N 200 -260 400 -260 {}
N 200 -170 200 -140 {}
N 200 -140 200 -110 {}
N 200 -50 200 -20 {}
N 200 -20 200 10 {}
N 200 70 200 110 {}
N 200 110 400 110 {}
N -150 -80 0 -80 {}
N 0 -80 160 -80 {}
N -150 -80 -150 -160 {}
N -150 -80 -150 -10 {}
N -180 -200 -180 -320 {}
N -120 -200 -120 -320 {}
N -400 -320 -180 -320 {}
N -180 -320 -120 -320 {}
N -170 20 -400 20 {}
N -150 50 -150 110 {}
N -150 110 -400 110 {}
C {devices/iopin.sym} -400 -320 0 1 {name=p8
lab=VDD}
C {devices/iopin.sym} -400 20 0 1 {name=p9
lab=VSS}
C {devices/iopin.sym} 400 -260 0 0 {name=p3
lab=a}
C {devices/iopin.sym} 400 110 0 0 {name=p6
lab=b}
C {devices/iopin.sym} -400 110 0 1 {name=p10
lab=g}
C {sky130_fd_pr/res_high_po_1p41.sym} 200 -200 0 0 {name=Rh_a
L='max((rh-278)/230.3,0.5)'
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {sky130_fd_pr/res_high_po_1p41.sym} 200 40 0 0 {name=Rh_b
L='max((rh-278)/230.3,0.5)'
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {sky130_fd_pr/pfet3_01v8.sym} 180 -80 0 0 {name=Msw
nf=6
mult=1
ad="'int((nf+1)/2) * W/nf * 0.29'"
pd="'2*int((nf+1)/2) * (W/nf + 0.29)'"
as="'int((nf+2)/2) * W/nf * 0.29'"
ps="'2*int((nf+2)/2) * (W/nf + 0.29)'"
nrd="'0.29 / W'"
nrs="'0.29 / W'"
sa=0
sb=0
sd=0
body=VDD
L=0.15
W='wsw'
model=pfet_01v8
spiceprefix=X}
C {devices/lab_pin.sym} 180 -200 0 0 {name=p1
sig_type=std_logic
lab=VSS}
C {devices/lab_pin.sym} 180 40 0 0 {name=p2
sig_type=std_logic
lab=VSS}
C {devices/lab_pin.sym} 200 -140 0 0 {name=p4
sig_type=std_logic
lab=sa}
C {devices/lab_pin.sym} 200 -20 0 0 {name=p5
sig_type=std_logic
lab=sb}
C {sky130_fd_pr/res_xhigh_po_0p35.sym} -150 20 0 0 {name=Rg
L='max((rg-0)/7379,0.5)'
model=res_xhigh_po_0p35
mult=1
spiceprefix=X}
C {sky130_fd_pr/pfet3_01v8.sym} -150 -180 3 0 {name=Mcap
nf=1
mult=1
ad="'int((nf+1)/2) * W/nf * 0.29'"
pd="'2*int((nf+1)/2) * (W/nf + 0.29)'"
as="'int((nf+2)/2) * W/nf * 0.29'"
ps="'2*int((nf+2)/2) * (W/nf + 0.29)'"
nrd="'0.29 / W'"
nrs="'0.29 / W'"
sa=0
sb=0
sd=0
body=VDD
L=5
W=5
model=pfet_01v8
spiceprefix=X}
C {devices/lab_pin.sym} 0 -80 0 0 {name=p7
sig_type=std_logic
lab=gi}
