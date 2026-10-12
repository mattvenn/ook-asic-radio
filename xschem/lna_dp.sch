v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {lna_dp: NMOS diff pair, resistor loads, mirrored tail (x10 of ibias)} -300 -560 0 0 0.5 0.5 {}
N 0 -290 0 -240 {}
N 0 -240 0 -180 {}
N 0 -240 -300 -240 {}
N -40 -150 -300 -150 {}
N 0 -120 0 -80 {}
N 400 -290 400 -240 {}
N 400 -240 400 -180 {}
N 400 -240 600 -240 {}
N 440 -150 600 -150 {}
N 400 -120 400 -80 {}
N 0 -350 0 -420 {}
N 400 -350 400 -420 {}
N -300 -420 0 -420 {}
N 0 -420 400 -420 {}
N 0 -80 200 -80 {}
N 200 -80 400 -80 {}
N 200 -80 200 -20 {}
N -100 -20 -100 -50 {}
N -100 -50 -40 -50 {}
N -40 -50 -40 10 {}
N -60 10 -40 10 {}
N -40 10 160 10 {}
N -100 -50 -300 -50 {}
N -100 40 -100 100 {}
N 200 40 200 100 {}
N -300 100 -100 100 {}
N -100 100 200 100 {}
N 200 100 400 100 {}
C {devices/iopin.sym} -300 -420 0 1 {name=p5
lab=VDD}
C {devices/iopin.sym} -300 100 0 1 {name=p8
lab=VSS}
C {devices/iopin.sym} -300 -50 0 1 {name=p7
lab=ibias}
C {devices/iopin.sym} -300 -150 0 1 {name=p2
lab=inp}
C {devices/iopin.sym} 600 -150 0 0 {name=p4
lab=inn}
C {devices/iopin.sym} 600 -240 0 0 {name=p3
lab=outp}
C {devices/iopin.sym} -300 -240 0 1 {name=p1
lab=outn}
C {devices/res.sym} 0 -320 0 0 {name=Rl_p
value='rl_dp'
m=1}
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
L='l_dp'
W='w_dp*(1+mm/2)'
model=nfet_01v8
spiceprefix=X}
C {devices/res.sym} 400 -320 0 0 {name=Rl_n
value='rl_dp'
m=1}
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
L='l_dp'
W='w_dp*(1-mm/2)'
model=nfet_01v8
spiceprefix=X}
C {devices/lab_pin.sym} 200 -80 0 1 {name=p6
sig_type=std_logic
lab=tail}
C {sky130_fd_pr/nfet3_01v8.sym} 180 10 0 0 {name=Mtail
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
body=VSS
L=0.5
W='wt_dp'
model=nfet_01v8
spiceprefix=X}
C {sky130_fd_pr/nfet3_01v8.sym} -80 10 0 1 {name=Mdiode
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
body=VSS
L=0.5
W='wt_dp'
model=nfet_01v8
spiceprefix=X}
