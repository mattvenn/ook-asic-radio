v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {lpf_rc: xhigh poly R (L=lr um, 0.35 um wide) + nc x 30x30 um MIM caps
defaults ~2.95 MOhm, ~3.7 pF -> ~14.6 kHz} -400 -460 0 0 0.4 0.4 {}
C {devices/iopin.sym} -400 -360 0 0 {name=p1
lab=VSS}
C {devices/iopin.sym} -400 -330 0 0 {name=p2
lab=in}
C {devices/iopin.sym} -400 -300 0 0 {name=p3
lab=out}
C {sky130_fd_pr/res_xhigh_po_0p35.sym} 0 -150 1 0 {name=R1
L='lr'
model=res_xhigh_po_0p35
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 30 -150 0 1 {name=p4
sig_type=std_logic
lab=out}
C {devices/lab_pin.sym} -30 -150 0 0 {name=p5
sig_type=std_logic
lab=in}
C {devices/lab_pin.sym} 0 -170 0 1 {name=p6
sig_type=std_logic
lab=VSS}
C {sky130_fd_pr/cap_mim_m3_1.sym} 200 -100 0 0 {name=C1
model=cap_mim_m3_1
W=30
L=30
MF='nc'
spiceprefix=X}
C {devices/lab_pin.sym} 200 -130 0 1 {name=p7
sig_type=std_logic
lab=out}
C {devices/lab_pin.sym} 200 -70 0 1 {name=p8
sig_type=std_logic
lab=VSS}
