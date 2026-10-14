v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {amp_dpc: NMOS diff pair, resistor loads, split tail + cs between sources
params: w l rl (pair, load), mt (total tail multiplier, mt/2 per side), cs} -200 -560 0 0 0.4 0.4 {}
T {R = 4k (L 7.38 um)} 25 -282 0 0 0.25 0.25 {}
T {= 1 x 20 / 0.15} 5 -112 0 0 0.25 0.25 {}
T {= 3 x 6 / 0.5} 5 48 0 0 0.25 0.25 {}
T {R = 4k (L 7.38 um)} 425 -282 0 0 0.25 0.25 {}
T {= 1 x 20 / 0.15} 293.75 -112 0 0 0.25 0.25 {}
T {= 3 x 6 / 0.5} 307.25 48 0 0 0.25 0.25 {}
T {C = 300fF (12.1 x 12.1 um)} 110 -118 0 0 0.25 0.25 {}
T {C = 300fF (12.1 x 12.1 um)} 110 -12 0 0 0.25 0.25 {}
N 0 -120 0 -30 {}
N 0 -30 0 -20 {}
N 0 -290 0 -240 {}
N 0 -240 0 -180 {}
N 0 -240 -200 -240 {}
N -40 -150 -200 -150 {}
N 400 -120 400 -90 {}
N 400 -90 400 -20 {}
N 400 -290 400 -240 {}
N 400 -240 400 -180 {}
N 400 -240 600 -240 {}
N 440 -150 600 -150 {}
N 0 -350 0 -420 {}
N 400 -350 400 -420 {}
N -200 -420 0 -420 {}
N 0 -420 400 -420 {}
N 0 -30 120 -30 {}
N 120 -30 280 -30 {}
N 120 -90 280 -90 {}
N 280 -90 400 -90 {}
N -40 10 -200 10 {}
N 0 40 0 100 {}
N 400 40 400 100 {}
N -200 100 0 100 {}
N 0 100 400 100 {}
C {devices/iopin.sym} -200 -420 0 1 {name=p9
lab=VDD}
C {devices/iopin.sym} -200 100 0 1 {name=p12
lab=VSS}
C {devices/iopin.sym} -200 10 0 1 {name=p10
lab=nb}
C {devices/iopin.sym} -200 -150 0 1 {name=p4
lab=inp}
C {devices/iopin.sym} 600 -150 0 0 {name=p8
lab=inn}
C {devices/iopin.sym} 600 -240 0 0 {name=p7
lab=outp}
C {devices/iopin.sym} -200 -240 0 1 {name=p3
lab=outn}
C {sky130_fd_pr/res_high_po_0p69.sym} 0 -320 0 0 {name=Rl_p
L='max((rl-526)/470.9,0.5)'
model=res_high_po_0p69
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} -20 -320 0 0 {name=p1
sig_type=std_logic
lab=VSS}
C {sky130_fd_pr/nfet3_01v8.sym} -20 -150 0 0 {name=Mp
nf=4
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
body=VSS
L='l'
W='w*(1+mm/2)'
model=nfet_01v8
spiceprefix=X}
C {sky130_fd_pr/nfet3_01v8.sym} -20 10 0 0 {name=Mtail_p
nf=2
mult='mt/2'
ad="'int((nf+1)/2) * W/nf * 0.29'"
pd="'2*int((nf+1)/2) * (W/nf + 0.29)'"
as="'int((nf+2)/2) * W/nf * 0.29'"
ps="'2*int((nf+2)/2) * (W/nf + 0.29)'"
nrd="'0.29 / W'"
nrs="'0.29 / W'"
sa=0
sb=0
sd=0
body=VSS
L=0.5
W='wt'
model=nfet_01v8
spiceprefix=X}
C {devices/lab_pin.sym} 0 -30 0 0 {name=p2
sig_type=std_logic
lab=sp}
C {sky130_fd_pr/res_high_po_0p69.sym} 400 -320 0 0 {name=Rl_n
L='max((rl-526)/470.9,0.5)'
model=res_high_po_0p69
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 380 -320 0 0 {name=p5
sig_type=std_logic
lab=VSS}
C {sky130_fd_pr/nfet3_01v8.sym} 420 -150 0 1 {name=Mn
nf=4
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
body=VSS
L='l'
W='w*(1-mm/2)'
model=nfet_01v8
spiceprefix=X}
C {sky130_fd_pr/nfet3_01v8.sym} 420 10 0 1 {name=Mtail_n
nf=2
mult='mt/2'
ad="'int((nf+1)/2) * W/nf * 0.29'"
pd="'2*int((nf+1)/2) * (W/nf + 0.29)'"
as="'int((nf+2)/2) * W/nf * 0.29'"
ps="'2*int((nf+2)/2) * (W/nf + 0.29)'"
nrd="'0.29 / W'"
nrs="'0.29 / W'"
sa=0
sb=0
sd=0
body=VSS
L=0.5
W='wt'
model=nfet_01v8
spiceprefix=X}
C {devices/lab_pin.sym} 400 -90 0 1 {name=p6
sig_type=std_logic
lab=sn}
C {sky130_fd_pr/cap_mim_m3_1.sym} 120 -60 0 0 {name=Cs_a
model=cap_mim_m3_1
W='sqrt((cs/2)/1/2.06e-15)'
L='sqrt((cs/2)/1/2.06e-15)'
MF=1
spiceprefix=X}
C {sky130_fd_pr/cap_mim_m3_1.sym} 280 -60 2 0 {name=Cs_b
model=cap_mim_m3_1
W='sqrt((cs/2)/1/2.06e-15)'
L='sqrt((cs/2)/1/2.06e-15)'
MF=1
spiceprefix=X}
C {devices/lab_pin.sym} 440 10 0 1 {name=p11
sig_type=std_logic
lab=nb}
