v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {tx_ls: 1.8 -> 3.3 V level shifter (R2R DAC dac_drive, skewed core)
in -> thin inverter (wpi/wni) -> ctrl; core NMOS kn x 0.42, PMOS kp x 0.42, L 0.5 thick. A = in, B = not in} -500 -460 0 0 0.4 0.4 {}
T {Placed 3 times in tx_top at two sizes, so each value note (= m x W / L) has one line per size:
  (tx_ls)     xls: ring -> driver arms, switches at the carrier: kn 14, kp 8, wpi 9, wni 3
  (tx_ls_en)  xlse_p / xlse_n: the arm enables, static: kn 1, kp 1, wpi 1, wni 0.42} -500 -370 0 0 0.3 0.3 {}
T {= 1 x 9 / 0.15 (tx_ls)
= 1 x 1 / 0.15 (tx_ls_en)} -295 -37 0 0 0.25 0.25 {}
T {= 1 x 3 / 0.15 (tx_ls)
= 1 x 0.42 / 0.15 (tx_ls_en)} -295 113 0 0 0.25 0.25 {}
T {= 1 x 5.88 / 0.5 (tx_ls)
= 1 x 0.42 / 0.5 (tx_ls_en)} 190 88 0 0 0.25 0.25 {}
T {= 1 x 5.88 / 0.5 (tx_ls)
= 1 x 0.42 / 0.5 (tx_ls_en)} 645 88 0 0 0.25 0.25 {}
T {= 1 x 3.36 / 0.5 (tx_ls)
= 1 x 0.42 / 0.5 (tx_ls_en)} 212.75 -112 0 0 0.25 0.25 {}
T {= 1 x 3.36 / 0.5 (tx_ls)
= 1 x 0.42 / 0.5 (tx_ls_en)} 605 -112 0 0 0.25 0.25 {}
N -340 -75 -340 0 {}
N -340 0 -340 75 {}
N -300 -45 -300 0 {}
N -300 0 -300 45 {}
N -500 0 -340 0 {}
N -40 -75 -40 0 {}
N -40 0 -40 75 {}
N 0 -45 0 0 {}
N 0 0 0 45 {}
N -300 0 -200 0 {}
N -200 0 -40 0 {}
N 0 0 80 0 {}
N 400 -120 400 -60 {}
N 400 -60 400 -20 {}
N 400 -20 400 20 {}
N 600 -120 600 -90 {}
N 600 -90 600 -20 {}
N 600 -20 600 20 {}
N 560 -150 530 -150 {}
N 530 -150 530 -60 {}
N 530 -60 400 -60 {}
N 440 -150 470 -150 {}
N 470 -150 470 -90 {}
N 470 -90 600 -90 {}
N 400 -20 330 -20 {}
N 600 -20 700 -20 {}
N -300 -105 -300 -200 {}
N 0 -105 0 -200 {}
N -500 -200 -300 -200 {}
N -300 -200 0 -200 {}
N 400 -180 400 -260 {}
N 600 -180 600 -260 {}
N -500 -260 400 -260 {}
N 400 -260 600 -260 {}
N -300 105 -300 180 {}
N 0 105 0 180 {}
N 400 80 400 180 {}
N 600 80 600 180 {}
N -500 180 -300 180 {}
N -300 180 0 180 {}
N 0 180 400 180 {}
N 400 180 600 180 {}
C {devices/iopin.sym} -500 -200 0 1 {name=p8
lab=VDD}
C {devices/iopin.sym} -500 -260 0 1 {name=p9
lab=VAPWR}
C {devices/iopin.sym} -500 180 0 1 {name=p10
lab=VSS}
C {devices/iopin.sym} -500 0 0 1 {name=p1
lab=in}
C {devices/iopin.sym} 330 -20 0 1 {name=p6
lab=A}
C {devices/iopin.sym} 700 -20 0 0 {name=p7
lab=B}
C {sky130_fd_pr/pfet3_01v8.sym} -320 -75 0 0 {name=Mi1p
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
W='wpi'
model=pfet_01v8
spiceprefix=X}
C {sky130_fd_pr/nfet3_01v8.sym} -320 75 0 0 {name=Mi1n
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
W='wni'
model=nfet_01v8
spiceprefix=X}
C {sky130_fd_pr/pfet3_01v8_hvt.sym} -20 -75 0 0 {name=M8
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
W=4
model=pfet_01v8_hvt
spiceprefix=X}
C {sky130_fd_pr/nfet3_01v8.sym} -20 75 0 0 {name=M7
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
W=1.68
model=nfet_01v8
spiceprefix=X}
C {devices/lab_pin.sym} -200 0 0 0 {name=p2
sig_type=std_logic
lab=ctrl}
C {devices/lab_pin.sym} 80 0 0 1 {name=p3
sig_type=std_logic
lab=ctrl_n}
C {sky130_fd_pr/nfet3_g5v0d10v5.sym} 380 50 0 0 {name=M9
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
W='0.42*kn'
model=nfet_g5v0d10v5
spiceprefix=X}
C {sky130_fd_pr/nfet3_g5v0d10v5.sym} 620 50 0 1 {name=M10
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
W='0.42*kn'
model=nfet_g5v0d10v5
spiceprefix=X}
C {devices/lab_pin.sym} 360 50 0 0 {name=p4
sig_type=std_logic
lab=ctrl}
C {devices/lab_pin.sym} 640 50 0 1 {name=p5
sig_type=std_logic
lab=ctrl_n}
C {sky130_fd_pr/pfet3_g5v0d10v5.sym} 420 -150 0 1 {name=M11
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
W='0.42*kp'
model=pfet_g5v0d10v5
spiceprefix=X}
C {sky130_fd_pr/pfet3_g5v0d10v5.sym} 580 -150 0 0 {name=M12
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
W='0.42*kp'
model=pfet_g5v0d10v5
spiceprefix=X}
