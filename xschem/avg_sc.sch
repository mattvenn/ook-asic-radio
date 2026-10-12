v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {avg_sc: switched-cap average, tau = cavg / (cs * f_phi)
phi1: cs <- in, phi2: cs -> out (cavg). cs = ncs x wcs x wcs um, cavg = nca x 30x30 um MIM} -600 -300 0 0 0.4 0.4 {}
N -340 330 -340 405 {}
N -340 405 -340 480 {}
N -300 360 -300 405 {}
N -300 405 -300 450 {}
N -300 405 -220 405 {}
N -340 405 -500 405 {}
N 260 330 260 405 {}
N 260 405 260 480 {}
N 300 360 300 405 {}
N 300 405 300 450 {}
N 300 405 380 405 {}
N 260 405 100 405 {}
N -300 300 -300 260 {}
N 300 300 300 260 {}
N -600 260 -300 260 {}
N -300 260 300 260 {}
N -300 510 -300 560 {}
N 300 510 300 560 {}
N -600 560 -300 560 {}
N -300 560 300 560 {}
N -340 -30 -160 -30 {}
N -340 30 -160 30 {}
N 260 30 440 30 {}
N 260 -30 440 -30 {}
N -600 -30 -340 -30 {}
N -160 30 50 30 {}
N 50 30 260 30 {}
N 50 30 50 70 {}
N 440 -30 650 -30 {}
N 650 -30 850 -30 {}
N 650 -30 650 70 {}
N 50 130 50 190 {}
N 650 130 650 190 {}
N -50 190 50 190 {}
N 50 190 650 190 {}
C {devices/iopin.sym} -600 260 0 1 {name=p5
lab=VDD}
C {devices/iopin.sym} -600 560 0 1 {name=p6
lab=VSS}
C {devices/iopin.sym} -600 -30 0 1 {name=p11
lab=in}
C {devices/iopin.sym} 850 -30 0 0 {name=p13
lab=out}
C {devices/iopin.sym} -500 405 0 1 {name=p2
lab=phi1}
C {devices/iopin.sym} 100 405 0 1 {name=p4
lab=phi2}
C {sky130_fd_pr/pfet3_01v8.sym} -320 330 0 0 {name=Miphi1p
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
C {sky130_fd_pr/nfet3_01v8.sym} -320 480 0 0 {name=Miphi1n
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
C {devices/lab_pin.sym} -220 405 0 1 {name=p1
sig_type=std_logic
lab=phi1b}
C {sky130_fd_pr/pfet3_01v8.sym} 280 330 0 0 {name=Miphi2p
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
C {sky130_fd_pr/nfet3_01v8.sym} 280 480 0 0 {name=Miphi2n
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
C {devices/lab_pin.sym} 380 405 0 1 {name=p3
sig_type=std_logic
lab=phi2b}
C {sky130_fd_pr/nfet3_01v8.sym} -140 0 0 1 {name=S1n
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
C {sky130_fd_pr/pfet3_01v8.sym} -360 0 2 1 {name=S1p
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
C {devices/lab_pin.sym} -380 0 0 0 {name=p7
sig_type=std_logic
lab=phi1b}
C {devices/lab_pin.sym} -120 0 0 1 {name=p8
sig_type=std_logic
lab=phi1}
C {sky130_fd_pr/nfet3_01v8.sym} 460 0 2 0 {name=S2n
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
C {sky130_fd_pr/pfet3_01v8.sym} 240 0 0 0 {name=S2p
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
C {devices/lab_pin.sym} 220 0 0 0 {name=p9
sig_type=std_logic
lab=phi2b}
C {devices/lab_pin.sym} 480 0 0 1 {name=p10
sig_type=std_logic
lab=phi2}
C {sky130_fd_pr/cap_mim_m3_1.sym} 50 100 0 0 {name=Cs
model=cap_mim_m3_1
W='wcs'
L='wcs'
MF='ncs'
spiceprefix=X}
C {sky130_fd_pr/cap_mim_m3_1.sym} 650 100 0 0 {name=Cavg
model=cap_mim_m3_1
W=30
L=30
MF='nca'
spiceprefix=X}
C {devices/lab_pin.sym} 50 30 0 0 {name=p12
sig_type=std_logic
lab=cs}
C {devices/lab_pin.sym} -50 190 0 0 {name=p14
sig_type=std_logic
lab=VSS}
