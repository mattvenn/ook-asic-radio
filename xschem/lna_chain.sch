v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {lna_chain: 6 diff-pair stages; stage 1 sized for noise, 2..6 cap-degenerated
tail current of stage i = mt x ibias (one reference diode); taps o<i>p/n = stage outputs} -1000 -400 0 0 0.4 0.4 {}
T {C = 2pF (31.2 x 31.2 um)} -625 -32 0 0 0.25 0.25 {}
T {R = 20k (L 19.1 um)} -325 -32 0 0 0.25 0.25 {}
T {C = 2pF (31.2 x 31.2 um)} -625 68 0 0 0.25 0.25 {}
T {R = 20k (L 19.1 um)} -325 68 0 0 0.25 0.25 {}
T {w 80, rl 1k, mt 20
mm 0} -60 15 0 0 0.25 0.25 {}
T {w 20, rl 4k, mt 6
cs 600f, mm 0} 340 15 0 0 0.25 0.25 {}
T {w 20, rl 4k, mt 6
cs 600f, mm 0} 740 15 0 0 0.25 0.25 {}
T {w 20, rl 4k, mt 6
cs 600f, mm 0} 1140 15 0 0 0.25 0.25 {}
T {w 20, rl 4k, mt 6
cs 600f, mm 0} 1540 15 0 0 0.25 0.25 {}
T {w 20, rl 4k, mt 6
cs 600f, mm 0} 1940 15 0 0 0.25 0.25 {}
N -1000 100 -900 100 {}
N -900 100 -840 100 {}
N -900 100 -900 150 {}
N -900 150 -880 150 {}
N -840 100 -840 120 {}
N -650 -40 -350 -40 {}
N -350 -40 -100 -40 {}
N -650 -100 -1000 -100 {}
N -350 -100 -350 -160 {}
N -350 -160 -1000 -160 {}
N -650 0 -350 0 {}
N -350 0 -100 0 {}
N -650 60 -1000 60 {}
N 100 -40 180 -40 {}
N 180 -40 300 -40 {}
N 180 -40 180 -120 {}
N 100 0 220 0 {}
N 220 0 300 0 {}
N 220 0 220 120 {}
N 500 -40 580 -40 {}
N 580 -40 700 -40 {}
N 580 -40 580 -120 {}
N 500 0 620 0 {}
N 620 0 700 0 {}
N 620 0 620 120 {}
N 900 -40 980 -40 {}
N 980 -40 1100 -40 {}
N 980 -40 980 -120 {}
N 900 0 1020 0 {}
N 1020 0 1100 0 {}
N 1020 0 1020 120 {}
N 1300 -40 1380 -40 {}
N 1380 -40 1500 -40 {}
N 1380 -40 1380 -120 {}
N 1300 0 1420 0 {}
N 1420 0 1500 0 {}
N 1420 0 1420 120 {}
N 1700 -40 1780 -40 {}
N 1780 -40 1900 -40 {}
N 1780 -40 1780 -120 {}
N 1700 0 1820 0 {}
N 1820 0 1900 0 {}
N 1820 0 1820 120 {}
N 2100 -40 2200 -40 {}
N 2100 0 2200 0 {}
N -50 -90 -50 -220 {}
N 350 -90 350 -220 {}
N 750 -90 750 -220 {}
N 1150 -90 1150 -220 {}
N 1550 -90 1550 -220 {}
N 1950 -90 1950 -220 {}
N -1000 -220 -50 -220 {}
N -50 -220 350 -220 {}
N 350 -220 750 -220 {}
N 750 -220 1150 -220 {}
N 1150 -220 1550 -220 {}
N 1550 -220 1950 -220 {}
N 1950 -220 2000 -220 {}
N -840 180 -840 220 {}
N -50 90 -50 220 {}
N 350 90 350 220 {}
N 750 90 750 220 {}
N 1150 90 1150 220 {}
N 1550 90 1550 220 {}
N 1950 90 1950 220 {}
N -1000 220 -840 220 {}
N -840 220 -50 220 {}
N -50 220 350 220 {}
N 350 220 750 220 {}
N 750 220 1150 220 {}
N 1150 220 1550 220 {}
N 1550 220 1950 220 {}
N 1950 220 2000 220 {}
C {devices/iopin.sym} -1000 -220 0 1 {name=p34
lab=VDD}
C {devices/iopin.sym} -1000 220 0 1 {name=p35
lab=VSS}
C {devices/iopin.sym} -1000 100 0 1 {name=p1
lab=ibias}
C {devices/iopin.sym} -1000 -160 0 1 {name=p5
lab=vcm}
C {devices/iopin.sym} -1000 400 0 1 {name=p33
lab=lna_lo_n}
C {devices/iopin.sym} -1000 -100 0 1 {name=p4
lab=inp}
C {devices/iopin.sym} -1000 60 0 1 {name=p8
lab=inn}
C {devices/iopin.sym} 2200 -40 0 0 {name=p26
lab=outp}
C {devices/iopin.sym} 2200 0 0 0 {name=p27
lab=outn}
C {devices/iopin.sym} 180 -120 0 0 {name=p11
lab=o1p}
C {devices/iopin.sym} 220 120 0 0 {name=p12
lab=o1n}
C {devices/iopin.sym} 580 -120 0 0 {name=p14
lab=o2p}
C {devices/iopin.sym} 620 120 0 0 {name=p15
lab=o2n}
C {devices/iopin.sym} 980 -120 0 0 {name=p17
lab=o3p}
C {devices/iopin.sym} 1020 120 0 0 {name=p18
lab=o3n}
C {devices/iopin.sym} 1380 -120 0 0 {name=p20
lab=o4p}
C {devices/iopin.sym} 1420 120 0 0 {name=p21
lab=o4n}
C {devices/iopin.sym} 1780 -120 0 0 {name=p23
lab=o5p}
C {devices/iopin.sym} 1820 120 0 0 {name=p24
lab=o5n}
C {sky130_fd_pr/nfet3_01v8.sym} -860 150 0 0 {name=Mref
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
W=6
model=nfet_01v8
spiceprefix=X}
C {sky130_fd_pr/cap_mim_m3_1.sym} -650 -70 2 0 {name=Cin_p
model=cap_mim_m3_1
W='sqrt((cin)/1/2.06e-15)'
L='sqrt((cin)/1/2.06e-15)'
MF=1
spiceprefix=X}
C {sky130_fd_pr/res_high_po_0p35.sym} -350 -70 0 0 {name=Rb_p
L='max((rb-963)/995,0.5)'
model=res_high_po_0p35
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} -370 -70 0 0 {name=p2
sig_type=std_logic
lab=VSS}
C {devices/lab_pin.sym} -650 -40 0 0 {name=p3
sig_type=std_logic
lab=g1p}
C {sky130_fd_pr/cap_mim_m3_1.sym} -650 30 0 0 {name=Cin_n
model=cap_mim_m3_1
W='sqrt((cin)/1/2.06e-15)'
L='sqrt((cin)/1/2.06e-15)'
MF=1
spiceprefix=X}
C {sky130_fd_pr/res_high_po_0p35.sym} -350 30 2 0 {name=Rb_n
L='max((rb-963)/995,0.5)'
model=res_high_po_0p35
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} -330 30 0 1 {name=p6
sig_type=std_logic
lab=VSS}
C {devices/lab_pin.sym} -650 0 0 0 {name=p7
sig_type=std_logic
lab=g1n}
C {devices/lab_pin.sym} -350 60 0 1 {name=p9
sig_type=std_logic
lab=vcm}
C {amp_dp.sym} 0 0 0 0 {name=xa1
w='w1'
l=0.15
rl='rl1'
wt=6
mt='mt1'
mm='mm'}
C {devices/lab_pin.sym} -100 40 0 0 {name=p10
sig_type=std_logic
lab=ibias}
C {amp_dpc.sym} 400 0 0 0 {name=xa2
w='w2'
l=0.15
rl='rl2'
wt=6
mt='mt2'
cs='cs'
mm='mm'}
C {devices/lab_pin.sym} 300 40 0 0 {name=p13
sig_type=std_logic
lab=ibias}
C {amp_dpc.sym} 800 0 0 0 {name=xa3
w='w2'
l=0.15
rl='rl2'
wt=6
mt='mt2'
cs='cs'
mm='mm'}
C {devices/lab_pin.sym} 700 40 0 0 {name=p16
sig_type=std_logic
lab=ibias}
C {amp_dpc.sym} 1200 0 0 0 {name=xa4
w='w2'
l=0.15
rl='rl2'
wt=6
mt='mt2'
cs='cs'
mm='mm'}
C {devices/lab_pin.sym} 1100 40 0 0 {name=p19
sig_type=std_logic
lab=ibias}
C {amp_dpc.sym} 1600 0 0 0 {name=xa5
w='w2'
l=0.15
rl='rl2'
wt=6
mt='mt2'
cs='cs'
mm='mm'}
C {devices/lab_pin.sym} 1500 40 0 0 {name=p22
sig_type=std_logic
lab=ibias}
C {amp_dpc.sym} 2000 0 0 0 {name=xa6
w='w2'
l=0.15
rl='rl2'
wt=6
mt='mt2'
cs='cs'
mm='mm'}
C {devices/lab_pin.sym} 1900 40 0 0 {name=p25
sig_type=std_logic
lab=ibias}
C {lna_shunt.sym} 400 400 0 0 {name=xsh}
C {devices/lab_pin.sym} 300 360 0 0 {name=p28
sig_type=std_logic
lab=o2p}
C {devices/lab_pin.sym} 300 400 0 0 {name=p29
sig_type=std_logic
lab=o2n}
C {devices/lab_pin.sym} 300 440 0 0 {name=p30
sig_type=std_logic
lab=lna_lo_n}
C {devices/lab_pin.sym} 350 310 0 0 {name=p31
sig_type=std_logic
lab=VDD}
C {devices/lab_pin.sym} 350 490 0 0 {name=p32
sig_type=std_logic
lab=VSS}
