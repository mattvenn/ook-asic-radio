v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {det_cell: full-wave rectifier, gates AC coupled and biased at ~Vth from vb
params: wd (W, L=0.15), rs (source degeneration), cc/rb (coupling)} -300 -460 0 0 0.4 0.4 {}
N -200 -70 -200 -100 {}
N -200 -100 -80 -100 {}
N -80 -100 -40 -100 {}
N -80 -170 -80 -100 {}
N -200 -10 -200 40 {}
N -200 40 -400 40 {}
N 0 -70 0 -40 {}
N 0 -40 0 -10 {}
N 0 -130 0 -180 {}
N 600 -70 600 -100 {}
N 440 -100 480 -100 {}
N 480 -100 600 -100 {}
N 480 -170 480 -100 {}
N 600 -10 600 40 {}
N 600 40 800 40 {}
N 400 -70 400 -40 {}
N 400 -40 400 -10 {}
N 400 -130 400 -180 {}
N 0 -180 200 -180 {}
N 200 -180 400 -180 {}
N 200 -180 200 -220 {}
N 200 -220 300 -220 {}
N -80 -230 -80 -260 {}
N 480 -230 480 -260 {}
N -400 -260 -80 -260 {}
N -80 -260 480 -260 {}
N 0 50 0 120 {}
N 400 50 400 120 {}
N -400 120 0 120 {}
N 0 120 400 120 {}
C {devices/iopin.sym} -400 120 0 1 {name=p13
lab=VSS}
C {devices/iopin.sym} -400 -260 0 1 {name=p12
lab=vb}
C {devices/iopin.sym} -400 40 0 1 {name=p4
lab=inp}
C {devices/iopin.sym} 800 40 0 0 {name=p9
lab=inn}
C {devices/iopin.sym} 300 -220 0 0 {name=p11
lab=out}
C {sky130_fd_pr/cap_mim_m3_1.sym} -200 -40 0 0 {name=Cc_p
model=cap_mim_m3_1
W='sqrt((cc)/1/2.06e-15)'
L='sqrt((cc)/1/2.06e-15)'
MF=1
spiceprefix=X}
C {sky130_fd_pr/res_xhigh_po_0p35.sym} -80 -200 0 0 {name=Rb_p
L='max((rb-0)/7379,0.5)'
model=res_xhigh_po_0p35
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} -100 -200 0 0 {name=p1
sig_type=std_logic
lab=VSS}
C {sky130_fd_pr/nfet3_01v8.sym} -20 -100 0 0 {name=Mp
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
W='wd'
model=nfet_01v8
spiceprefix=X}
C {sky130_fd_pr/res_high_po_0p35.sym} 0 20 0 0 {name=Rs_p
L='max((rs-963)/995,0.5)'
model=res_high_po_0p35
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} -20 20 0 0 {name=p2
sig_type=std_logic
lab=VSS}
C {devices/lab_pin.sym} -80 -100 0 0 {name=p3
sig_type=std_logic
lab=gp}
C {devices/lab_pin.sym} 0 -40 0 0 {name=p5
sig_type=std_logic
lab=sp}
C {sky130_fd_pr/cap_mim_m3_1.sym} 600 -40 0 1 {name=Cc_n
model=cap_mim_m3_1
W='sqrt((cc)/1/2.06e-15)'
L='sqrt((cc)/1/2.06e-15)'
MF=1
spiceprefix=X}
C {sky130_fd_pr/res_xhigh_po_0p35.sym} 480 -200 0 0 {name=Rb_n
L='max((rb-0)/7379,0.5)'
model=res_xhigh_po_0p35
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 460 -200 0 0 {name=p6
sig_type=std_logic
lab=VSS}
C {sky130_fd_pr/nfet3_01v8.sym} 420 -100 0 1 {name=Mn
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
W='wd'
model=nfet_01v8
spiceprefix=X}
C {sky130_fd_pr/res_high_po_0p35.sym} 400 20 0 0 {name=Rs_n
L='max((rs-963)/995,0.5)'
model=res_high_po_0p35
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 380 20 0 0 {name=p7
sig_type=std_logic
lab=VSS}
C {devices/lab_pin.sym} 480 -100 0 1 {name=p8
sig_type=std_logic
lab=gn}
C {devices/lab_pin.sym} 400 -40 0 1 {name=p10
sig_type=std_logic
lab=sn}
