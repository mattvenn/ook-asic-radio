v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {lna_pinv: pseudo-differential self-biased inverters (Rf out->in)} -300 -560 0 0 0.5 0.5 {}
N 0 -200 0 -150 {}
N 0 -150 0 -110 {}
N -40 -230 -40 -150 {}
N -40 -150 -40 -80 {}
N -120 -150 -40 -150 {}
N -120 -330 -120 -150 {}
N 0 -150 60 -150 {}
N 60 -150 120 -150 {}
N 60 -150 60 -330 {}
N 60 -330 -60 -330 {}
N -300 -150 -120 -150 {}
N 500 -200 500 -150 {}
N 500 -150 500 -110 {}
N 460 -230 460 -150 {}
N 460 -150 460 -80 {}
N 380 -150 460 -150 {}
N 380 -330 380 -150 {}
N 500 -150 560 -150 {}
N 560 -150 620 -150 {}
N 560 -150 560 -330 {}
N 560 -330 440 -330 {}
N 0 -260 0 -400 {}
N 500 -260 500 -400 {}
N -300 -400 0 -400 {}
N 0 -400 500 -400 {}
N 0 -50 0 50 {}
N 500 -50 500 50 {}
N -300 50 0 50 {}
N 0 50 500 50 {}
C {devices/iopin.sym} -300 -400 0 1 {name=p5
lab=VDD}
C {devices/iopin.sym} -300 50 0 1 {name=p6
lab=VSS}
C {devices/iopin.sym} -300 -150 0 1 {name=p1
lab=inp}
C {devices/iopin.sym} 380 -150 0 1 {name=p3
lab=inn}
C {devices/iopin.sym} 620 -150 0 0 {name=p4
lab=outp}
C {devices/iopin.sym} 120 -150 0 0 {name=p2
lab=outn}
C {sky130_fd_pr/pfet3_01v8.sym} -20 -230 0 0 {name=Mp_p
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
body=VDD
L=0.15
W='wp_inv*(1+mm/2)'
model=pfet_01v8
spiceprefix=X}
C {sky130_fd_pr/nfet3_01v8.sym} -20 -80 0 0 {name=Mn_p
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
L=0.15
W='wn_inv*(1+mm/2)'
model=nfet_01v8
spiceprefix=X}
C {devices/res.sym} -90 -330 1 0 {name=Rf_p
value='rf_inv'
m=1}
C {sky130_fd_pr/pfet3_01v8.sym} 480 -230 0 0 {name=Mp_n
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
body=VDD
L=0.15
W='wp_inv*(1-mm/2)'
model=pfet_01v8
spiceprefix=X}
C {sky130_fd_pr/nfet3_01v8.sym} 480 -80 0 0 {name=Mn_n
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
L=0.15
W='wn_inv*(1-mm/2)'
model=nfet_01v8
spiceprefix=X}
C {devices/res.sym} 410 -330 1 0 {name=Rf_n
value='rf_inv'
m=1}
