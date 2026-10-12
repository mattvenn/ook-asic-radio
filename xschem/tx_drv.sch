v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {tx_drv: one antenna arm on VAPWR, out = in & en
thick NAND2 then inverters x4 per stage: N 0.42 / 1.68 / 6.72 / 26.88 / 48 um, P = 3 N, L 0.5} -600 -460 0 0 0.4 0.4 {}
N -400 -120 -400 -50 {}
N -200 -120 -200 -50 {}
N -400 -50 -300 -50 {}
N -300 -50 -200 -50 {}
N -300 -50 -300 -30 {}
N -300 30 -300 50 {}
N -300 50 -300 70 {}
N -600 0 -340 0 {}
N -440 -150 -460 -150 {}
N -460 -150 -460 0 {}
N -600 100 -340 100 {}
N 110 -150 110 -50 {}
N 110 -50 110 50 {}
N 150 -120 150 -50 {}
N 150 -50 150 20 {}
N -200 -50 110 -50 {}
N 360 -150 360 -50 {}
N 360 -50 360 50 {}
N 400 -120 400 -50 {}
N 400 -50 400 20 {}
N 150 -50 360 -50 {}
N 610 -150 610 -50 {}
N 610 -50 610 50 {}
N 650 -120 650 -50 {}
N 650 -50 650 20 {}
N 400 -50 610 -50 {}
N 860 -150 860 -50 {}
N 860 -50 860 50 {}
N 900 -120 900 -50 {}
N 900 -50 900 20 {}
N 650 -50 860 -50 {}
N 1110 -150 1110 -50 {}
N 1110 -50 1110 50 {}
N 1150 -120 1150 -50 {}
N 1150 -50 1150 20 {}
N 900 -50 1110 -50 {}
N 1150 -50 1250 -50 {}
N -400 -180 -400 -260 {}
N -200 -180 -200 -260 {}
N 150 -180 150 -260 {}
N 400 -180 400 -260 {}
N 650 -180 650 -260 {}
N 900 -180 900 -260 {}
N 1150 -180 1150 -260 {}
N -600 -260 -400 -260 {}
N -400 -260 -200 -260 {}
N -200 -260 150 -260 {}
N 150 -260 400 -260 {}
N 400 -260 650 -260 {}
N 650 -260 900 -260 {}
N 900 -260 1150 -260 {}
N -300 130 -300 200 {}
N 150 80 150 200 {}
N 400 80 400 200 {}
N 650 80 650 200 {}
N 900 80 900 200 {}
N 1150 80 1150 200 {}
N -600 200 -300 200 {}
N -300 200 150 200 {}
N 150 200 400 200 {}
N 400 200 650 200 {}
N 650 200 900 200 {}
N 900 200 1150 200 {}
C {devices/iopin.sym} -600 -260 0 1 {name=p11
lab=VAPWR}
C {devices/iopin.sym} -600 200 0 1 {name=p12
lab=VSS}
C {devices/iopin.sym} -600 0 0 1 {name=p2
lab=in}
C {devices/iopin.sym} -600 100 0 1 {name=p3
lab=en}
C {devices/iopin.sym} 1250 -50 0 0 {name=p10
lab=out}
C {sky130_fd_pr/pfet3_g5v0d10v5.sym} -420 -150 0 0 {name=Mnap
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
body=VAPWR
L=0.5
W=1.26
model=pfet_g5v0d10v5
spiceprefix=X}
C {sky130_fd_pr/pfet3_g5v0d10v5.sym} -220 -150 0 0 {name=Mnbp
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
body=VAPWR
L=0.5
W=1.26
model=pfet_g5v0d10v5
spiceprefix=X}
C {sky130_fd_pr/nfet3_g5v0d10v5.sym} -320 0 0 0 {name=Mnan
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
L=0.5
W=0.84
model=nfet_g5v0d10v5
spiceprefix=X}
C {sky130_fd_pr/nfet3_g5v0d10v5.sym} -320 100 0 0 {name=Mnbn
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
L=0.5
W=0.84
model=nfet_g5v0d10v5
spiceprefix=X}
C {devices/lab_pin.sym} -300 50 0 1 {name=p1
sig_type=std_logic
lab=ns}
C {devices/lab_pin.sym} -240 -150 0 0 {name=p4
sig_type=std_logic
lab=en}
C {devices/lab_pin.sym} -200 -50 0 1 {name=p5
sig_type=std_logic
lab=y0}
C {sky130_fd_pr/pfet3_g5v0d10v5.sym} 130 -150 0 0 {name=M1p
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
body=VAPWR
L=0.5
W=1.26
model=pfet_g5v0d10v5
spiceprefix=X}
C {sky130_fd_pr/nfet3_g5v0d10v5.sym} 130 50 0 0 {name=M1n
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
L=0.5
W=0.42
model=nfet_g5v0d10v5
spiceprefix=X}
C {devices/lab_pin.sym} 150 -50 0 1 {name=p6
sig_type=std_logic
lab=y1}
C {sky130_fd_pr/pfet3_g5v0d10v5.sym} 380 -150 0 0 {name=M2p
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
body=VAPWR
L=0.5
W=5.04
model=pfet_g5v0d10v5
spiceprefix=X}
C {sky130_fd_pr/nfet3_g5v0d10v5.sym} 380 50 0 0 {name=M2n
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
L=0.5
W=1.68
model=nfet_g5v0d10v5
spiceprefix=X}
C {devices/lab_pin.sym} 400 -50 0 1 {name=p7
sig_type=std_logic
lab=y2}
C {sky130_fd_pr/pfet3_g5v0d10v5.sym} 630 -150 0 0 {name=M3p
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
body=VAPWR
L=0.5
W=20.16
model=pfet_g5v0d10v5
spiceprefix=X}
C {sky130_fd_pr/nfet3_g5v0d10v5.sym} 630 50 0 0 {name=M3n
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
L=0.5
W=6.72
model=nfet_g5v0d10v5
spiceprefix=X}
C {devices/lab_pin.sym} 650 -50 0 1 {name=p8
sig_type=std_logic
lab=y3}
C {sky130_fd_pr/pfet3_g5v0d10v5.sym} 880 -150 0 0 {name=M4p
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
body=VAPWR
L=0.5
W=80.64
model=pfet_g5v0d10v5
spiceprefix=X}
C {sky130_fd_pr/nfet3_g5v0d10v5.sym} 880 50 0 0 {name=M4n
nf=3
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
W=26.88
model=nfet_g5v0d10v5
spiceprefix=X}
C {devices/lab_pin.sym} 900 -50 0 1 {name=p9
sig_type=std_logic
lab=y4}
C {sky130_fd_pr/pfet3_g5v0d10v5.sym} 1130 -150 0 0 {name=M5p
nf=14
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
body=VAPWR
L=0.5
W=144
model=pfet_g5v0d10v5
spiceprefix=X}
C {sky130_fd_pr/nfet3_g5v0d10v5.sym} 1130 50 0 0 {name=M5n
nf=5
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
W=48
model=nfet_g5v0d10v5
spiceprefix=X}
