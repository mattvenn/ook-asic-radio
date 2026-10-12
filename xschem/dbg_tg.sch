v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {dbg_tg: transmission gate a <-> b, on when en = 1
thin 1.8 V devices (keep the pad side within 0..1.8 V); local inverter for enb} -400 -260 0 0 0.4 0.4 {}
N -40 225 -40 300 {}
N -40 300 -40 375 {}
N 0 255 0 300 {}
N 0 300 0 345 {}
N -40 300 -400 300 {}
N 0 300 100 300 {}
N 0 195 0 190 {}
N -400 190 0 190 {}
N 0 405 0 410 {}
N -400 410 0 410 {}
N -400 -30 30 -30 {}
N 30 -30 210 -30 {}
N 30 30 210 30 {}
N 210 30 450 30 {}
C {devices/iopin.sym} -400 190 0 1 {name=p3
lab=VDD}
C {devices/iopin.sym} -400 410 0 1 {name=p4
lab=VSS}
C {devices/iopin.sym} -400 300 0 1 {name=p1
lab=en}
C {devices/iopin.sym} -400 -30 0 1 {name=p7
lab=a}
C {devices/iopin.sym} 450 30 0 0 {name=p8
lab=b}
C {sky130_fd_pr/pfet3_01v8.sym} -20 225 0 0 {name=Mip
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
L=0.15
W=1
model=pfet_01v8
spiceprefix=X}
C {sky130_fd_pr/nfet3_01v8.sym} -20 375 0 0 {name=Min
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
body=VSS
L=0.15
W=0.5
model=nfet_01v8
spiceprefix=X}
C {devices/lab_pin.sym} 100 300 0 1 {name=p2
sig_type=std_logic
lab=enb}
C {sky130_fd_pr/nfet3_01v8.sym} 230 0 0 1 {name=Mn
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
body=VSS
L=0.15
W='wn'
model=nfet_01v8
spiceprefix=X}
C {sky130_fd_pr/pfet3_01v8.sym} 10 0 2 1 {name=Mp
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
L=0.15
W='wp'
model=pfet_01v8
spiceprefix=X}
C {devices/lab_pin.sym} 250 0 0 1 {name=p5
sig_type=std_logic
lab=en}
C {devices/lab_pin.sym} -10 0 0 0 {name=p6
sig_type=std_logic
lab=enb}
