v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {lna_shunt: low-gain strap across stage 2 outputs (a = o2p, b = o2n)
g = 0: PMOS on, Rh + Ron + Rh loads the stage (~11 dB less chain gain); g = VDD: off
params: rh (each Rh, high_po_1p41), wsw (PMOS W, L 0.15), rg (gate R, xhigh_po_0p35)} -200 -360 0 0 0.4 0.4 {}
T {R = 421 (L 0.621 um)} -30 -150 0 0 0.25 0.25 {}
T {R = 421 (L 0.621 um)} 370 -150 0 0 0.25 0.25 {}
T {= 1 x 18 / 0.15} 225 -12 0 0 0.25 0.25 {}
T {R = 20k (L 2.71 um)} 225 188 0 0 0.25 0.25 {}
C {devices/iopin.sym} -200 300 0 0 {name=p13
lab=VDD}
C {devices/iopin.sym} -200 330 0 0 {name=p14
lab=VSS}
C {devices/iopin.sym} -200 360 0 0 {name=p15
lab=a}
C {devices/iopin.sym} -200 390 0 0 {name=p16
lab=b}
C {devices/iopin.sym} -200 420 0 0 {name=p17
lab=g}
C {sky130_fd_pr/res_high_po_1p41.sym} 0 -100 1 0 {name=Rh_a
L='max((rh-278)/230.3,0.5)'
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {sky130_fd_pr/res_high_po_1p41.sym} 400 -100 1 0 {name=Rh_b
L='max((rh-278)/230.3,0.5)'
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 0 -120 0 1 {name=p1
sig_type=std_logic
lab=VSS}
C {devices/lab_pin.sym} 400 -120 0 1 {name=p2
sig_type=std_logic
lab=VSS}
C {sky130_fd_pr/pfet3_01v8.sym} 200 -50 1 0 {name=Msw
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
C {devices/lab_pin.sym} 30 -100 0 1 {name=p3
sig_type=std_logic
lab=a}
C {devices/lab_pin.sym} -30 -100 0 0 {name=p4
sig_type=std_logic
lab=sa}
C {devices/lab_pin.sym} 430 -100 0 1 {name=p5
sig_type=std_logic
lab=sb}
C {devices/lab_pin.sym} 370 -100 0 0 {name=p6
sig_type=std_logic
lab=b}
C {devices/lab_pin.sym} 230 -30 0 1 {name=p7
sig_type=std_logic
lab=sa}
C {devices/lab_pin.sym} 170 -30 0 0 {name=p8
sig_type=std_logic
lab=sb}
C {devices/lab_pin.sym} 200 -70 0 1 {name=p9
sig_type=std_logic
lab=gi}
C {sky130_fd_pr/res_xhigh_po_0p35.sym} 200 150 0 0 {name=Rg
L='max((rg-0)/7379,0.5)'
model=res_xhigh_po_0p35
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 200 120 0 1 {name=p10
sig_type=std_logic
lab=gi}
C {devices/lab_pin.sym} 200 180 0 1 {name=p11
sig_type=std_logic
lab=g}
C {devices/lab_pin.sym} 180 150 0 0 {name=p12
sig_type=std_logic
lab=VSS}
