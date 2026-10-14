v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {bias_gen: I = (VDD/3) / rref (high_po, same poly as the chain loads)
OTA forces x = vref; PMOS diode Mpr -> mirrors ib_chain 60 uA, ib_det 2 uA, ib_comp 1 uA; vcm = 2 VDD/3. en = 0: all off} -1300 -800 0 0 0.4 0.4 {}
T {R = 200k (L 27.1 um)} -825 -462 0 0 0.25 0.25 {}
T {R = 200k (L 27.1 um)} -825 -312 0 0 0.25 0.25 {}
T {R = 200k (L 27.1 um)} -825 -162 0 0 0.25 0.25 {}
T {C = 2pF (2 x 22 x 22 um)} -600 -414 0 0 0.25 0.25 {}
T {C = 2pF (2 x 22 x 22 um)} -600 -264 0 0 0.25 0.25 {}
T {R = 250k (L 33.9 um)} 125 -312 0 0 0.25 0.25 {}
T {C = 1pF (22 x 22 um)} 205 -270 0 0 0.25 0.25 {}
T {R = 5k (L 9.5 um)} 525 -112 0 0 0.25 0.25 {}
T {R = 5k (L 9.5 um)} 525 8 0 0 0.25 0.25 {}
T {= 60 x 2 / 1} 414 -462 0 0 0.25 0.25 {}
T {= 60 x 2 / 1} 705 -462 0 0 0.25 0.25 {}
T {= 2 x 2 / 1} 905 -462 0 0 0.25 0.25 {}
T {= 1 x 2 / 1} 1105 -462 0 0 0.25 0.25 {}
T {= 5 x 2 / 1} 1305 -445 0 0 0.25 0.25 {}
N -1140 -225 -1140 -150 {}
N -1140 -150 -1140 -75 {}
N -1100 -195 -1100 -150 {}
N -1100 -150 -1100 -105 {}
N -1140 -150 -1300 -150 {}
N -1100 -150 -1040 -150 {}
N -850 -470 -850 -430 {}
N -850 -430 -850 -380 {}
N -850 -430 -700 -430 {}
N -700 -430 -600 -430 {}
N -850 -320 -850 -280 {}
N -850 -280 -850 -230 {}
N -850 -280 -700 -280 {}
N -700 -280 -480 -280 {}
N -850 -170 -850 -120 {}
N -850 -120 -850 -80 {}
N 100 -470 100 -440 {}
N 100 -440 100 -380 {}
N 100 -320 100 -270 {}
N 100 -270 100 -230 {}
N -260 -500 0 -500 {}
N 0 -500 60 -500 {}
N 100 -440 0 -440 {}
N 0 -440 0 -500 {}
N -480 -280 -480 -350 {}
N -480 -350 -440 -350 {}
N -400 -380 -400 -420 {}
N -200 -380 -200 -420 {}
N -400 -420 -300 -420 {}
N -300 -420 -200 -420 {}
N -300 -470 -300 -420 {}
N -360 -150 -300 -150 {}
N -300 -150 -240 -150 {}
N -400 -320 -400 -250 {}
N -400 -250 -400 -180 {}
N -400 -250 -300 -250 {}
N -300 -250 -300 -150 {}
N -200 -320 -200 -250 {}
N -200 -250 -200 -180 {}
N -200 -250 200 -250 {}
N 200 -250 300 -250 {}
N 300 -250 460 -250 {}
N 300 -250 300 -180 {}
N 500 -220 500 -200 {}
N 500 -200 500 -180 {}
N 500 -120 500 -90 {}
N 500 -90 500 -60 {}
N 500 -470 500 -400 {}
N 500 -400 500 -280 {}
N 300 -420 300 -400 {}
N 300 -400 500 -400 {}
N 500 -400 600 -400 {}
N 600 -400 600 -500 {}
N 700 -470 700 -380 {}
N 900 -470 900 -380 {}
N 1100 -470 1100 -380 {}
N 540 -500 600 -500 {}
N 600 -500 660 -500 {}
N -1100 -255 -1100 -600 {}
N -850 -530 -850 -600 {}
N 100 -530 100 -600 {}
N -300 -530 -300 -600 {}
N 500 -530 500 -600 {}
N 300 -480 300 -600 {}
N 700 -530 700 -600 {}
N 900 -530 900 -600 {}
N 1100 -530 1100 -600 {}
N 1300 -530 1300 -600 {}
N -1300 -600 -1100 -600 {}
N -1100 -600 -850 -600 {}
N -850 -600 -300 -600 {}
N -300 -600 100 -600 {}
N 100 -600 300 -600 {}
N 300 -600 500 -600 {}
N 500 -600 700 -600 {}
N 700 -600 900 -600 {}
N 900 -600 1100 -600 {}
N 1100 -600 1300 -600 {}
N -1100 -45 -1100 300 {}
N -850 -20 -850 300 {}
N -700 -220 -700 300 {}
N 100 -170 100 300 {}
N -400 -120 -400 300 {}
N -200 -120 -200 300 {}
N 300 -120 300 300 {}
N 500 0 500 300 {}
N -1300 300 -1100 300 {}
N -1100 300 -850 300 {}
N -850 300 -700 300 {}
N -700 300 -400 300 {}
N -400 300 -200 300 {}
N -200 300 100 300 {}
N 100 300 300 300 {}
N 300 300 500 300 {}
C {devices/iopin.sym} -1300 -600 0 1 {name=p34
lab=VDD}
C {devices/iopin.sym} -1300 300 0 1 {name=p35
lab=VSS}
C {devices/iopin.sym} -1300 -150 0 1 {name=p1
lab=en}
C {devices/iopin.sym} -600 -430 0 0 {name=p7
lab=vcm}
C {devices/iopin.sym} 700 -380 0 0 {name=p27
lab=ib_chain}
C {devices/iopin.sym} 900 -380 0 0 {name=p29
lab=ib_det}
C {devices/iopin.sym} 1100 -380 0 0 {name=p31
lab=ib_comp}
C {sky130_fd_pr/pfet3_01v8.sym} -1120 -225 0 0 {name=Meip
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
C {sky130_fd_pr/nfet3_01v8.sym} -1120 -75 0 0 {name=Mein
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
C {devices/lab_pin.sym} -1040 -150 0 1 {name=p2
sig_type=std_logic
lab=enb}
C {sky130_fd_pr/res_xhigh_po_0p35.sym} -850 -500 0 0 {name=Rd1
L='max((rdiv-0)/7379,0.5)'
model=res_xhigh_po_0p35
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} -870 -500 0 0 {name=p3
sig_type=std_logic
lab=VSS}
C {sky130_fd_pr/res_xhigh_po_0p35.sym} -850 -350 0 0 {name=Rd2
L='max((rdiv-0)/7379,0.5)'
model=res_xhigh_po_0p35
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} -870 -350 0 0 {name=p4
sig_type=std_logic
lab=VSS}
C {sky130_fd_pr/res_xhigh_po_0p35.sym} -850 -200 0 0 {name=Rd3
L='max((rdiv-0)/7379,0.5)'
model=res_xhigh_po_0p35
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} -870 -200 0 0 {name=p5
sig_type=std_logic
lab=VSS}
C {sky130_fd_pr/nfet3_01v8.sym} -870 -50 0 0 {name=Mdsw
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
C {devices/lab_pin.sym} -890 -50 0 0 {name=p6
sig_type=std_logic
lab=en}
C {sky130_fd_pr/cap_mim_m3_1.sym} -700 -400 0 0 {name=Cvcm
model=cap_mim_m3_1
W='sqrt((2e-12)/2/2.06e-15)'
L='sqrt((2e-12)/2/2.06e-15)'
MF=2
spiceprefix=X}
C {sky130_fd_pr/cap_mim_m3_1.sym} -700 -250 0 0 {name=Cvref
model=cap_mim_m3_1
W='sqrt((2e-12)/2/2.06e-15)'
L='sqrt((2e-12)/2/2.06e-15)'
MF=2
spiceprefix=X}
C {devices/lab_pin.sym} -700 -370 0 1 {name=p8
sig_type=std_logic
lab=VSS}
C {devices/lab_pin.sym} -850 -280 0 0 {name=p9
sig_type=std_logic
lab=vref}
C {devices/lab_pin.sym} -850 -120 0 0 {name=p10
sig_type=std_logic
lab=dsw}
C {sky130_fd_pr/pfet3_01v8.sym} 80 -500 0 0 {name=Mpb
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
model=pfet_01v8
spiceprefix=X}
C {sky130_fd_pr/res_xhigh_po_0p35.sym} 100 -350 0 0 {name=Rtail
L='max((rtail-0)/7379,0.5)'
model=res_xhigh_po_0p35
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 80 -350 0 0 {name=p11
sig_type=std_logic
lab=VSS}
C {sky130_fd_pr/nfet3_01v8.sym} 80 -200 0 0 {name=Mtsw
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
C {devices/lab_pin.sym} 60 -200 0 0 {name=p12
sig_type=std_logic
lab=en}
C {devices/lab_pin.sym} 100 -440 0 1 {name=p13
sig_type=std_logic
lab=pb}
C {devices/lab_pin.sym} 100 -270 0 1 {name=p14
sig_type=std_logic
lab=tsw}
C {sky130_fd_pr/pfet3_01v8.sym} -280 -500 0 1 {name=Mpt
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
model=pfet_01v8
spiceprefix=X}
C {sky130_fd_pr/pfet3_01v8.sym} -420 -350 0 0 {name=M1
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
model=pfet_01v8
spiceprefix=X}
C {sky130_fd_pr/pfet3_01v8.sym} -180 -350 0 1 {name=M2
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
model=pfet_01v8
spiceprefix=X}
C {devices/lab_pin.sym} -160 -350 0 1 {name=p15
sig_type=std_logic
lab=x}
C {devices/lab_pin.sym} -300 -420 0 1 {name=p16
sig_type=std_logic
lab=tail}
C {sky130_fd_pr/nfet3_01v8.sym} -380 -150 0 1 {name=M3
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
C {sky130_fd_pr/nfet3_01v8.sym} -220 -150 0 0 {name=M4
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
C {devices/lab_pin.sym} -400 -250 0 0 {name=p17
sig_type=std_logic
lab=d1}
C {sky130_fd_pr/cap_mim_m3_1.sym} 200 -220 0 0 {name=Cc
model=cap_mim_m3_1
W='sqrt((cc)/1/2.06e-15)'
L='sqrt((cc)/1/2.06e-15)'
MF=1
spiceprefix=X}
C {devices/lab_pin.sym} 200 -190 0 1 {name=p18
sig_type=std_logic
lab=VSS}
C {sky130_fd_pr/nfet3_01v8.sym} 280 -150 0 0 {name=Mpd
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
C {sky130_fd_pr/nfet3_01v8.sym} 480 -250 0 0 {name=Mn
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
W=20
model=nfet_01v8
spiceprefix=X}
C {devices/lab_pin.sym} 300 -250 0 1 {name=p19
sig_type=std_logic
lab=ota}
C {devices/lab_pin.sym} 260 -150 0 0 {name=p20
sig_type=std_logic
lab=enb}
C {sky130_fd_pr/res_high_po_0p69.sym} 500 -150 0 0 {name=Rref1
L='max((rref/2-526)/470.9,0.5)'
model=res_high_po_0p69
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 480 -150 0 0 {name=p21
sig_type=std_logic
lab=VSS}
C {sky130_fd_pr/res_high_po_0p69.sym} 500 -30 0 0 {name=Rref2
L='max((rref/2-526)/470.9,0.5)'
model=res_high_po_0p69
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 480 -30 0 0 {name=p22
sig_type=std_logic
lab=VSS}
C {devices/lab_pin.sym} 500 -200 0 1 {name=p23
sig_type=std_logic
lab=x}
C {devices/lab_pin.sym} 500 -90 0 1 {name=p24
sig_type=std_logic
lab=xr}
C {sky130_fd_pr/pfet3_01v8.sym} 520 -500 0 1 {name=Mpr
nf=1
mult=60
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
W='wpu'
model=pfet_01v8
spiceprefix=X}
C {sky130_fd_pr/pfet3_01v8.sym} 280 -450 0 0 {name=Mpu
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
C {devices/lab_pin.sym} 260 -450 0 0 {name=p25
sig_type=std_logic
lab=en}
C {devices/lab_pin.sym} 600 -400 0 1 {name=p26
sig_type=std_logic
lab=pr}
C {sky130_fd_pr/pfet3_01v8.sym} 680 -500 0 0 {name=Mo_ib_chain
nf=1
mult=60
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
W='wpu'
model=pfet_01v8
spiceprefix=X}
C {sky130_fd_pr/pfet3_01v8.sym} 880 -500 0 0 {name=Mo_ib_det
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
W='wpu'
model=pfet_01v8
spiceprefix=X}
C {devices/lab_pin.sym} 860 -500 0 0 {name=p28
sig_type=std_logic
lab=pr}
C {sky130_fd_pr/pfet3_01v8.sym} 1080 -500 0 0 {name=Mo_ib_comp
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
W='wpu'
model=pfet_01v8
spiceprefix=X}
C {devices/lab_pin.sym} 1060 -500 0 0 {name=p30
sig_type=std_logic
lab=pr}
C {sky130_fd_pr/pfet3_01v8.sym} 1280 -500 0 0 {name=Mdum
nf=1
mult=5
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
W='wpu'
model=pfet_01v8
spiceprefix=X}
C {devices/lab_pin.sym} 1300 -470 0 1 {name=p32
sig_type=std_logic
lab=VDD}
C {devices/lab_pin.sym} 1260 -500 0 0 {name=p33
sig_type=std_logic
lab=VDD}
