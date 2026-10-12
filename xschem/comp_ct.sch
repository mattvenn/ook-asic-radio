v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {comp_ct: continuous comparator, out = 1 when inp > inn + trim offset
lvt NMOS pair + lvt PMOS mirror; degenerated trim pair (trim vs VDD/2); PMOS CS; inverter} -1000 -560 0 0 0.4 0.4 {}
T {layout matching dummies (all terminals on the rail)} -200 300 0 0 0.4 0.4 {}
N -860 70 -860 40 {}
N -1000 40 -900 40 {}
N -900 40 -860 40 {}
N -900 40 -900 100 {}
N -40 -100 -100 -100 {}
N 240 -100 300 -100 {}
N 0 -70 0 -20 {}
N 200 -70 200 -20 {}
N 0 -20 100 -20 {}
N 100 -20 200 -20 {}
N 100 -20 100 70 {}
N 40 -300 100 -300 {}
N 100 -300 160 -300 {}
N 0 -240 100 -240 {}
N 100 -240 100 -300 {}
N 0 -270 0 -240 {}
N 0 -240 0 -200 {}
N 0 -200 0 -130 {}
N 200 -270 200 -240 {}
N 200 -240 200 -200 {}
N 200 -200 200 -130 {}
N -250 -130 -250 -200 {}
N -250 -200 0 -200 {}
N -250 -70 -250 30 {}
N -250 30 -250 70 {}
N 450 -130 450 -200 {}
N 450 -200 200 -200 {}
N 450 -70 450 30 {}
N 450 30 450 70 {}
N 490 -100 550 -100 {}
N -250 30 -130 30 {}
N -70 30 450 30 {}
N -700 -220 -700 -100 {}
N -700 -100 -700 -70 {}
N -800 -70 -800 -100 {}
N -800 -100 -700 -100 {}
N -700 -100 -290 -100 {}
N 200 -240 600 -240 {}
N 600 -240 810 -240 {}
N 810 -240 810 -300 {}
N 850 -270 850 -100 {}
N 850 -100 850 70 {}
N 1010 -300 1010 -100 {}
N 1010 -100 1010 100 {}
N 850 -100 1010 -100 {}
N 1050 -270 1050 -100 {}
N 1050 -100 1050 70 {}
N 1050 -100 1150 -100 {}
N -700 -280 -700 -400 {}
N 0 -330 0 -400 {}
N 200 -330 200 -400 {}
N 850 -330 850 -400 {}
N 1050 -330 1050 -400 {}
N -1000 -400 -700 -400 {}
N -700 -400 0 -400 {}
N 0 -400 200 -400 {}
N 200 -400 850 -400 {}
N 850 -400 1050 -400 {}
N -860 130 -860 200 {}
N -800 -10 -800 200 {}
N -700 -10 -700 200 {}
N -250 130 -250 200 {}
N 100 130 100 200 {}
N 450 130 450 200 {}
N 850 130 850 200 {}
N 1050 130 1050 200 {}
N -1000 200 -860 200 {}
N -860 200 -800 200 {}
N -800 200 -700 200 {}
N -700 200 -250 200 {}
N -250 200 100 200 {}
N 100 200 450 200 {}
N 450 200 850 200 {}
N 850 200 1050 200 {}
N -80 420 -40 420 {}
N -40 420 -40 530 {}
N -120 450 -120 530 {}
N 120 420 160 420 {}
N 160 420 160 530 {}
N 80 450 80 530 {}
N 320 420 360 420 {}
N 360 420 360 530 {}
N 280 450 280 530 {}
N 520 480 560 480 {}
N 560 480 560 370 {}
N 480 450 480 370 {}
N 720 480 760 480 {}
N 760 480 760 370 {}
N 680 450 680 370 {}
N -160 530 -120 530 {}
N -120 530 -80 530 {}
N -80 530 -40 530 {}
N -40 530 80 530 {}
N 80 530 120 530 {}
N 120 530 160 530 {}
N 160 530 280 530 {}
N 280 530 320 530 {}
N 320 530 360 530 {}
N -80 480 -80 530 {}
N 120 480 120 530 {}
N 320 480 320 530 {}
N 440 370 480 370 {}
N 480 370 520 370 {}
N 520 370 560 370 {}
N 560 370 680 370 {}
N 680 370 720 370 {}
N 720 370 760 370 {}
N 520 420 520 370 {}
N 720 420 720 370 {}
C {devices/iopin.sym} -1000 -400 0 1 {name=p21
lab=VDD}
C {devices/iopin.sym} -1000 200 0 1 {name=p22
lab=VSS}
C {devices/iopin.sym} -1000 40 0 1 {name=p1
lab=ibias}
C {devices/iopin.sym} -100 -100 0 1 {name=p3
lab=inp}
C {devices/iopin.sym} 300 -100 0 0 {name=p4
lab=inn}
C {devices/iopin.sym} 550 -100 0 0 {name=p12
lab=trim}
C {devices/iopin.sym} 1150 -100 0 0 {name=p20
lab=out}
C {sky130_fd_pr/nfet3_01v8.sym} -880 100 0 0 {name=Mb
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
L=2
W=2
model=nfet_01v8
spiceprefix=X}
C {sky130_fd_pr/nfet3_01v8.sym} 80 100 0 0 {name=Mt1
nf=1
mult=4
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
L=2
W='0.455*mt1'
model=nfet_01v8
spiceprefix=X}
C {devices/lab_pin.sym} 60 100 0 0 {name=p2
sig_type=std_logic
lab=ibias}
C {sky130_fd_pr/nfet3_01v8_lvt.sym} -20 -100 0 0 {name=M1
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
L='l1'
W='w1'
model=nfet_01v8_lvt
spiceprefix=X}
C {sky130_fd_pr/nfet3_01v8_lvt.sym} 220 -100 0 1 {name=M2
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
L='l1'
W='w1'
model=nfet_01v8_lvt
spiceprefix=X}
C {devices/lab_pin.sym} 100 -20 0 1 {name=p5
sig_type=std_logic
lab=tail}
C {sky130_fd_pr/pfet3_01v8_lvt.sym} 20 -300 0 1 {name=Mp1
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
L=1
W=4
model=pfet_01v8_lvt
spiceprefix=X}
C {sky130_fd_pr/pfet3_01v8_lvt.sym} 180 -300 0 0 {name=Mp2
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
L=1
W=4
model=pfet_01v8_lvt
spiceprefix=X}
C {devices/lab_pin.sym} 0 -200 0 0 {name=p6
sig_type=std_logic
lab=d1}
C {devices/lab_pin.sym} 200 -200 0 1 {name=p7
sig_type=std_logic
lab=d2}
C {sky130_fd_pr/nfet3_01v8_lvt.sym} -270 -100 0 0 {name=M3
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
L=1
W=2
model=nfet_01v8_lvt
spiceprefix=X}
C {sky130_fd_pr/nfet3_01v8.sym} -270 100 0 0 {name=Mta_sa
nf=1
mult='mta'
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
L=2
W=2
model=nfet_01v8
spiceprefix=X}
C {devices/lab_pin.sym} -290 100 0 0 {name=p8
sig_type=std_logic
lab=ibias}
C {devices/lab_pin.sym} -250 30 0 0 {name=p9
sig_type=std_logic
lab=sa}
C {sky130_fd_pr/nfet3_01v8_lvt.sym} 470 -100 0 1 {name=M4
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
L=1
W=2
model=nfet_01v8_lvt
spiceprefix=X}
C {sky130_fd_pr/nfet3_01v8.sym} 470 100 0 1 {name=Mta_sb
nf=1
mult='mta'
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
L=2
W=2
model=nfet_01v8
spiceprefix=X}
C {devices/lab_pin.sym} 490 100 0 1 {name=p10
sig_type=std_logic
lab=ibias}
C {devices/lab_pin.sym} 450 30 0 1 {name=p11
sig_type=std_logic
lab=sb}
C {sky130_fd_pr/res_xhigh_po_0p35.sym} -100 30 1 0 {name=Rdeg
L='rdeg/7.37k'
model=res_xhigh_po_0p35
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} -100 10 0 1 {name=p13
sig_type=std_logic
lab=VSS}
C {sky130_fd_pr/res_xhigh_po_0p35.sym} -700 -250 0 0 {name=Rr1
L='lref'
model=res_xhigh_po_0p35
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} -720 -250 0 0 {name=p14
sig_type=std_logic
lab=VSS}
C {sky130_fd_pr/res_xhigh_po_0p35.sym} -700 -40 0 0 {name=Rr2
L='lref'
model=res_xhigh_po_0p35
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} -720 -40 0 0 {name=p15
sig_type=std_logic
lab=VSS}
C {sky130_fd_pr/cap_mim_m3_1.sym} -800 -40 0 0 {name=Cref
model=cap_mim_m3_1
W=10
L=10
MF=1
spiceprefix=X}
C {devices/lab_pin.sym} -700 -100 0 0 {name=p16
sig_type=std_logic
lab=vref}
C {sky130_fd_pr/cap_mim_m3_1.sym} 600 -210 0 0 {name=Cl
model=cap_mim_m3_1
W='wcl'
L='wcl/2'
MF=2
spiceprefix=X}
C {devices/lab_pin.sym} 600 -180 0 1 {name=p17
sig_type=std_logic
lab=VSS}
C {sky130_fd_pr/pfet3_01v8_lvt.sym} 830 -300 0 0 {name=Mp3
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
L=1
W=4
model=pfet_01v8_lvt
spiceprefix=X}
C {sky130_fd_pr/nfet3_01v8.sym} 830 100 0 0 {name=Mn3
nf=1
mult=2
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
L=2
W=4.55
model=nfet_01v8
spiceprefix=X}
C {devices/lab_pin.sym} 810 100 0 0 {name=p18
sig_type=std_logic
lab=ibias}
C {devices/lab_pin.sym} 850 -100 0 0 {name=p19
sig_type=std_logic
lab=o2}
C {sky130_fd_pr/pfet3_01v8.sym} 1030 -300 0 0 {name=Mip
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
W=2
model=pfet_01v8
spiceprefix=X}
C {sky130_fd_pr/nfet3_01v8.sym} 1030 100 0 0 {name=Min
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
W=1
model=nfet_01v8
spiceprefix=X}
C {sky130_fd_pr/nfet3_01v8_lvt.sym} -100 450 0 0 {name=Mdn1
nf=1
mult=2
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
L=1
W=5
model=nfet_01v8_lvt
spiceprefix=X}
C {sky130_fd_pr/nfet3_01v8_lvt.sym} 100 450 0 0 {name=Mdn2
nf=1
mult=2
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
L=1
W=1
model=nfet_01v8_lvt
spiceprefix=X}
C {sky130_fd_pr/nfet3_01v8.sym} 300 450 0 0 {name=Mdn3
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
L=2
W=2
model=nfet_01v8
spiceprefix=X}
C {sky130_fd_pr/pfet3_01v8_lvt.sym} 500 450 0 0 {name=Mdp1
nf=1
mult=2
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
L=1
W=2
model=pfet_01v8_lvt
spiceprefix=X}
C {sky130_fd_pr/pfet3_01v8_lvt.sym} 700 450 0 0 {name=Mdp2
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
L=1
W=4
model=pfet_01v8_lvt
spiceprefix=X}
C {devices/lab_pin.sym} -160 530 0 0 {name=p23
sig_type=std_logic
lab=VSS}
C {devices/lab_pin.sym} 440 370 0 0 {name=p24
sig_type=std_logic
lab=VDD}
