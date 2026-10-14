v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {log_det: 6 det_cells summed into rdet || cdet; vb from a replica diode
taps t<i>p/n: chain stage outputs, last = chain output} -700 -460 0 0 0.4 0.4 {}
T {= 1 x 1 / 0.15} -315 -37 0 0 0.25 0.25 {}
T {R = 10k (L 9.08 um)} -355 138 0 0 0.25 0.25 {}
T {R = 8k (L 15.9 um)} 2325 -182 0 0 0.25 0.25 {}
T {C = 1pF (22 x 22 um)} 2625 -182 0 0 0.25 0.25 {}
T {wd 1, rs 10k, cc 100f
rb 200k} -60 15 0 0 0.25 0.25 {}
T {wd 1, rs 10k, cc 100f
rb 200k} 340 15 0 0 0.25 0.25 {}
T {wd 1, rs 10k, cc 100f
rb 200k} 740 15 0 0 0.25 0.25 {}
T {wd 1, rs 10k, cc 100f
rb 200k} 1140 15 0 0 0.25 0.25 {}
T {wd 1, rs 10k, cc 100f
rb 200k} 1540 15 0 0 0.25 0.25 {}
T {wd 1, rs 10k, cc 100f
rb 200k} 1940 15 0 0 0.25 0.25 {}
N -700 -60 -440 -60 {}
N -440 -60 -380 -60 {}
N -440 -60 -440 0 {}
N -440 0 -420 0 {}
N -380 -60 -380 -30 {}
N -380 30 -380 50 {}
N -380 50 -380 70 {}
N 2300 -190 2300 -150 {}
N 2600 -190 2600 -150 {}
N -100 -40 -160 -40 {}
N -100 0 -160 0 {}
N 100 -40 140 -40 {}
N 140 -40 140 -150 {}
N 300 -40 240 -40 {}
N 300 0 240 0 {}
N 500 -40 540 -40 {}
N 540 -40 540 -150 {}
N 700 -40 640 -40 {}
N 700 0 640 0 {}
N 900 -40 940 -40 {}
N 940 -40 940 -150 {}
N 1100 -40 1040 -40 {}
N 1100 0 1040 0 {}
N 1300 -40 1340 -40 {}
N 1340 -40 1340 -150 {}
N 1500 -40 1440 -40 {}
N 1500 0 1440 0 {}
N 1700 -40 1740 -40 {}
N 1740 -40 1740 -150 {}
N 1900 -40 1840 -40 {}
N 1900 0 1840 0 {}
N 2100 -40 2140 -40 {}
N 2140 -40 2140 -150 {}
N 140 -150 540 -150 {}
N 540 -150 940 -150 {}
N 940 -150 1340 -150 {}
N 1340 -150 1740 -150 {}
N 1740 -150 2140 -150 {}
N 2140 -150 2300 -150 {}
N 2300 -150 2600 -150 {}
N 2600 -150 2700 -150 {}
N 2300 -250 2300 -300 {}
N 2600 -250 2600 -300 {}
N -700 -300 2300 -300 {}
N 2300 -300 2600 -300 {}
N -380 130 -380 200 {}
N -50 90 -50 200 {}
N 350 90 350 200 {}
N 750 90 750 200 {}
N 1150 90 1150 200 {}
N 1550 90 1550 200 {}
N 1950 90 1950 200 {}
N -700 200 -380 200 {}
N -380 200 -50 200 {}
N -50 200 350 200 {}
N 350 200 750 200 {}
N 750 200 1150 200 {}
N 1150 200 1550 200 {}
N 1550 200 1950 200 {}
C {devices/iopin.sym} -700 -300 0 1 {name=p25
lab=VDD}
C {devices/iopin.sym} -700 200 0 1 {name=p26
lab=VSS}
C {devices/iopin.sym} -700 -60 0 1 {name=p2
lab=ibias_det}
C {devices/iopin.sym} 2700 -150 0 0 {name=p24
lab=det}
C {devices/iopin.sym} -160 -40 0 1 {name=p6
lab=t1p}
C {devices/iopin.sym} -160 0 0 1 {name=p7
lab=t1n}
C {devices/iopin.sym} 240 -40 0 1 {name=p9
lab=t2p}
C {devices/iopin.sym} 240 0 0 1 {name=p10
lab=t2n}
C {devices/iopin.sym} 640 -40 0 1 {name=p12
lab=t3p}
C {devices/iopin.sym} 640 0 0 1 {name=p13
lab=t3n}
C {devices/iopin.sym} 1040 -40 0 1 {name=p15
lab=t4p}
C {devices/iopin.sym} 1040 0 0 1 {name=p16
lab=t4n}
C {devices/iopin.sym} 1440 -40 0 1 {name=p18
lab=t5p}
C {devices/iopin.sym} 1440 0 0 1 {name=p19
lab=t5n}
C {devices/iopin.sym} 1840 -40 0 1 {name=p21
lab=t6p}
C {devices/iopin.sym} 1840 0 0 1 {name=p22
lab=t6n}
C {sky130_fd_pr/nfet3_01v8.sym} -400 0 0 0 {name=Mbias
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
C {sky130_fd_pr/res_high_po_0p35.sym} -380 100 0 0 {name=Rs_b
L='max((rs-963)/995,0.5)'
model=res_high_po_0p35
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} -400 100 0 0 {name=p1
sig_type=std_logic
lab=VSS}
C {devices/lab_pin.sym} -380 50 0 1 {name=p3
sig_type=std_logic
lab=sb}
C {sky130_fd_pr/res_high_po_0p69.sym} 2300 -220 0 0 {name=Rdet
L='max((rdet-526)/470.9,0.5)'
model=res_high_po_0p69
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 2280 -220 0 0 {name=p4
sig_type=std_logic
lab=VSS}
C {sky130_fd_pr/cap_mim_m3_1.sym} 2600 -220 2 0 {name=Cdet
model=cap_mim_m3_1
W='sqrt((cdet)/1/2.06e-15)'
L='sqrt((cdet)/1/2.06e-15)'
MF=1
spiceprefix=X}
C {det_cell.sym} 0 0 0 0 {name=xd1
wd='wd'
rs='rs'
cc='cc'
rb='rb'}
C {devices/lab_pin.sym} -100 40 0 0 {name=p5
sig_type=std_logic
lab=ibias_det}
C {det_cell.sym} 400 0 0 0 {name=xd2
wd='wd'
rs='rs'
cc='cc'
rb='rb'}
C {devices/lab_pin.sym} 300 40 0 0 {name=p8
sig_type=std_logic
lab=ibias_det}
C {det_cell.sym} 800 0 0 0 {name=xd3
wd='wd'
rs='rs'
cc='cc'
rb='rb'}
C {devices/lab_pin.sym} 700 40 0 0 {name=p11
sig_type=std_logic
lab=ibias_det}
C {det_cell.sym} 1200 0 0 0 {name=xd4
wd='wd'
rs='rs'
cc='cc'
rb='rb'}
C {devices/lab_pin.sym} 1100 40 0 0 {name=p14
sig_type=std_logic
lab=ibias_det}
C {det_cell.sym} 1600 0 0 0 {name=xd5
wd='wd'
rs='rs'
cc='cc'
rb='rb'}
C {devices/lab_pin.sym} 1500 40 0 0 {name=p17
sig_type=std_logic
lab=ibias_det}
C {det_cell.sym} 2000 0 0 0 {name=xd6
wd='wd'
rs='rs'
cc='cc'
rb='rb'}
C {devices/lab_pin.sym} 1900 40 0 0 {name=p20
sig_type=std_logic
lab=ibias_det}
C {devices/lab_pin.sym} 2140 -150 0 0 {name=p23
sig_type=std_logic
lab=det}
