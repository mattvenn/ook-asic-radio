v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {amp_dp: NMOS diff pair, resistor loads, tail gate from pin nb
params: w l rl (pair, load), mt (tail multiplier of unit W=wt, L=0.5)} -200 -560 0 0 0.4 0.4 {}
N 0 -290 0 -240 {}
N 0 -240 0 -180 {}
N 0 -240 -200 -240 {}
N -40 -150 -200 -150 {}
N 400 -290 400 -240 {}
N 400 -240 400 -180 {}
N 400 -240 600 -240 {}
N 440 -150 600 -150 {}
N 0 -350 0 -420 {}
N 400 -350 400 -420 {}
N -200 -420 0 -420 {}
N 0 -420 400 -420 {}
N 0 -120 0 -80 {}
N 400 -120 400 -80 {}
N 0 -80 200 -80 {}
N 200 -80 400 -80 {}
N 200 -80 200 -20 {}
N 160 10 -200 10 {}
N 200 40 200 100 {}
N -200 100 200 100 {}
N 200 100 400 100 {}
C {devices/iopin.sym} -200 -420 0 1 {name=p7
lab=VDD}
C {devices/iopin.sym} -200 100 0 1 {name=p10
lab=VSS}
C {devices/iopin.sym} -200 10 0 1 {name=p9
lab=nb}
C {devices/iopin.sym} -200 -150 0 1 {name=p3
lab=inp}
C {devices/iopin.sym} 600 -150 0 0 {name=p6
lab=inn}
C {devices/iopin.sym} 600 -240 0 0 {name=p5
lab=outp}
C {devices/iopin.sym} -200 -240 0 1 {name=p2
lab=outn}
C {sky130_fd_pr/res_high_po_1p41.sym} 0 -320 0 0 {name=Rl_p
L='max((rl-278)/230.3,0.5)'
model=res_high_po_1p41
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
C {sky130_fd_pr/res_high_po_1p41.sym} 400 -320 0 0 {name=Rl_n
L='max((rl-278)/230.3,0.5)'
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 380 -320 0 0 {name=p4
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
C {sky130_fd_pr/nfet3_01v8.sym} 180 10 0 0 {name=Mtail
nf=2
mult='mt'
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
C {devices/lab_pin.sym} 200 -80 0 1 {name=p8
sig_type=std_logic
lab=tail}
