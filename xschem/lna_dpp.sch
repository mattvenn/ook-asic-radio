v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {lna_dpp: PMOS diff pair, resistor loads to ground, mirrored tail (x10 of ibias)} -300 -620 0 0 0.5 0.5 {}
N -100 -360 -100 -420 {}
N 200 -360 200 -420 {}
N -300 -420 -100 -420 {}
N -100 -420 200 -420 {}
N 200 -420 400 -420 {}
N -100 -300 -100 -270 {}
N -100 -270 -40 -270 {}
N -40 -270 -40 -330 {}
N -60 -330 -40 -330 {}
N -40 -330 160 -330 {}
N -100 -270 -300 -270 {}
N 200 -300 200 -240 {}
N 0 -240 200 -240 {}
N 200 -240 400 -240 {}
N 0 -180 0 -240 {}
N 0 -120 0 -60 {}
N 0 -60 0 0 {}
N 0 -60 -300 -60 {}
N -40 -150 -300 -150 {}
N 400 -180 400 -240 {}
N 400 -120 400 -60 {}
N 400 -60 400 0 {}
N 400 -60 600 -60 {}
N 440 -150 600 -150 {}
N 0 60 0 120 {}
N 400 60 400 120 {}
N -300 120 0 120 {}
N 0 120 400 120 {}
C {devices/iopin.sym} -300 -420 0 1 {name=p1
lab=VDD}
C {devices/iopin.sym} -300 120 0 1 {name=p8
lab=VSS}
C {devices/iopin.sym} -300 -270 0 1 {name=p2
lab=ibias}
C {devices/iopin.sym} -300 -150 0 1 {name=p5
lab=inp}
C {devices/iopin.sym} 600 -150 0 0 {name=p7
lab=inn}
C {devices/iopin.sym} 600 -60 0 0 {name=p6
lab=outp}
C {devices/iopin.sym} -300 -60 0 1 {name=p4
lab=outn}
C {sky130_fd_pr/pfet3_01v8.sym} 180 -330 0 0 {name=Mtail
nf=2
mult=10
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
L=0.5
W='wt_dpp'
model=pfet_01v8
spiceprefix=X}
C {sky130_fd_pr/pfet3_01v8.sym} -80 -330 0 1 {name=Mdiode
nf=2
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
L=0.5
W='wt_dpp'
model=pfet_01v8
spiceprefix=X}
C {devices/lab_pin.sym} 200 -240 0 1 {name=p3
sig_type=std_logic
lab=tail}
C {sky130_fd_pr/pfet3_01v8.sym} -20 -150 0 0 {name=Mp
nf=8
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
body=tail
L='l_dpp'
W='w_dpp*(1+mm/2)'
model=pfet_01v8
spiceprefix=X}
C {devices/res.sym} 0 30 0 0 {name=Rl_p
value='rl_dpp'
m=1}
C {sky130_fd_pr/pfet3_01v8.sym} 420 -150 0 1 {name=Mn
nf=8
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
body=tail
L='l_dpp'
W='w_dpp*(1-mm/2)'
model=pfet_01v8
spiceprefix=X}
C {devices/res.sym} 400 30 0 0 {name=Rl_n
value='rl_dpp'
m=1}
