v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {r2r: 8-bit R-2R ladder, matches the reused tt08 r2r layout
unit R = res_high_po_1p41 L 45 (~10.6 k); 2R = two units; out = code/256 x V(bits)} -500 -560 0 0 0.4 0.4 {}
N 0 -300 0 -230 {}
N 0 -170 0 -140 {}
N 0 -140 0 -110 {}
N 0 -50 0 0 {}
N -250 -300 -250 -230 {}
N -250 -170 -250 -140 {}
N -250 -140 -250 -110 {}
N -250 -50 -250 80 {}
N -500 170 -500 80 {}
N 0 -300 95 -300 {}
N 155 -300 250 -300 {}
N 250 -300 250 -230 {}
N 250 -170 250 -140 {}
N 250 -140 250 -110 {}
N 250 -50 250 0 {}
N 250 -300 345 -300 {}
N 405 -300 500 -300 {}
N 500 -300 500 -230 {}
N 500 -170 500 -140 {}
N 500 -140 500 -110 {}
N 500 -50 500 0 {}
N 500 -300 595 -300 {}
N 655 -300 750 -300 {}
N 750 -300 750 -230 {}
N 750 -170 750 -140 {}
N 750 -140 750 -110 {}
N 750 -50 750 0 {}
N 750 -300 845 -300 {}
N 905 -300 1000 -300 {}
N 1000 -300 1000 -230 {}
N 1000 -170 1000 -140 {}
N 1000 -140 1000 -110 {}
N 1000 -50 1000 0 {}
N 1000 -300 1095 -300 {}
N 1155 -300 1250 -300 {}
N 1250 -300 1250 -230 {}
N 1250 -170 1250 -140 {}
N 1250 -140 1250 -110 {}
N 1250 -50 1250 0 {}
N 1250 -300 1345 -300 {}
N 1405 -300 1500 -300 {}
N 1500 -300 1500 -230 {}
N 1500 -170 1500 -140 {}
N 1500 -140 1500 -110 {}
N 1500 -50 1500 0 {}
N 1500 -300 1595 -300 {}
N 1655 -300 1750 -300 {}
N 1750 -300 1750 -230 {}
N 1750 -170 1750 -140 {}
N 1750 -140 1750 -110 {}
N 1750 -50 1750 0 {}
N 1750 -300 1900 -300 {}
N -250 -300 0 -300 {}
N 1900 170 1900 80 {}
N -500 80 -250 80 {}
N -250 80 1900 80 {}
C {devices/iopin.sym} 0 0 0 0 {name=p4
lab=b0}
C {devices/iopin.sym} 250 0 0 0 {name=p15
lab=b1}
C {devices/iopin.sym} 500 0 0 0 {name=p21
lab=b2}
C {devices/iopin.sym} 750 0 0 0 {name=p27
lab=b3}
C {devices/iopin.sym} 1000 0 0 0 {name=p33
lab=b4}
C {devices/iopin.sym} 1250 0 0 0 {name=p39
lab=b5}
C {devices/iopin.sym} 1500 0 0 0 {name=p45
lab=b6}
C {devices/iopin.sym} 1750 0 0 0 {name=p51
lab=b7}
C {devices/iopin.sym} 1900 -300 0 0 {name=p52
lab=out}
C {devices/iopin.sym} -500 80 0 1 {name=p55
lab=VGND}
C {sky130_fd_pr/res_high_po_1p41.sym} 0 -80 2 0 {name=R1
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 20 -80 0 1 {name=p1
sig_type=std_logic
lab=VGND}
C {sky130_fd_pr/res_high_po_1p41.sym} 0 -200 2 0 {name=R2
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 20 -200 0 1 {name=p2
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} 0 -140 0 1 {name=p3
sig_type=std_logic
lab=s0}
C {sky130_fd_pr/res_high_po_1p41.sym} -250 -200 0 0 {name=R3
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} -270 -200 0 0 {name=p5
sig_type=std_logic
lab=VGND}
C {sky130_fd_pr/res_high_po_1p41.sym} -250 -80 0 0 {name=R4
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} -270 -80 0 0 {name=p6
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} -250 -140 0 0 {name=p7
sig_type=std_logic
lab=s1}
C {sky130_fd_pr/res_high_po_1p41.sym} -500 200 0 0 {name=R5
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} -520 200 0 0 {name=p8
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} -500 230 0 1 {name=p9
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} 0 -300 0 1 {name=p10
sig_type=std_logic
lab=a0}
C {sky130_fd_pr/res_high_po_1p41.sym} 125 -300 3 0 {name=R6
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 125 -280 0 1 {name=p11
sig_type=std_logic
lab=VGND}
C {sky130_fd_pr/res_high_po_1p41.sym} 250 -200 0 0 {name=R7
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 230 -200 0 0 {name=p12
sig_type=std_logic
lab=VGND}
C {sky130_fd_pr/res_high_po_1p41.sym} 250 -80 0 0 {name=R8
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 230 -80 0 0 {name=p13
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} 250 -140 0 1 {name=p14
sig_type=std_logic
lab=t1}
C {devices/lab_pin.sym} 250 -300 0 1 {name=p16
sig_type=std_logic
lab=a1}
C {sky130_fd_pr/res_high_po_1p41.sym} 375 -300 3 0 {name=R9
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 375 -280 0 1 {name=p17
sig_type=std_logic
lab=VGND}
C {sky130_fd_pr/res_high_po_1p41.sym} 500 -200 0 0 {name=R10
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 480 -200 0 0 {name=p18
sig_type=std_logic
lab=VGND}
C {sky130_fd_pr/res_high_po_1p41.sym} 500 -80 0 0 {name=R11
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 480 -80 0 0 {name=p19
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} 500 -140 0 1 {name=p20
sig_type=std_logic
lab=t2}
C {devices/lab_pin.sym} 500 -300 0 1 {name=p22
sig_type=std_logic
lab=a2}
C {sky130_fd_pr/res_high_po_1p41.sym} 625 -300 3 0 {name=R12
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 625 -280 0 1 {name=p23
sig_type=std_logic
lab=VGND}
C {sky130_fd_pr/res_high_po_1p41.sym} 750 -200 0 0 {name=R13
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 730 -200 0 0 {name=p24
sig_type=std_logic
lab=VGND}
C {sky130_fd_pr/res_high_po_1p41.sym} 750 -80 0 0 {name=R14
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 730 -80 0 0 {name=p25
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} 750 -140 0 1 {name=p26
sig_type=std_logic
lab=t3}
C {devices/lab_pin.sym} 750 -300 0 1 {name=p28
sig_type=std_logic
lab=a3}
C {sky130_fd_pr/res_high_po_1p41.sym} 875 -300 3 0 {name=R15
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 875 -280 0 1 {name=p29
sig_type=std_logic
lab=VGND}
C {sky130_fd_pr/res_high_po_1p41.sym} 1000 -200 0 0 {name=R16
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 980 -200 0 0 {name=p30
sig_type=std_logic
lab=VGND}
C {sky130_fd_pr/res_high_po_1p41.sym} 1000 -80 0 0 {name=R17
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 980 -80 0 0 {name=p31
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} 1000 -140 0 1 {name=p32
sig_type=std_logic
lab=t4}
C {devices/lab_pin.sym} 1000 -300 0 1 {name=p34
sig_type=std_logic
lab=a4}
C {sky130_fd_pr/res_high_po_1p41.sym} 1125 -300 3 0 {name=R18
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 1125 -280 0 1 {name=p35
sig_type=std_logic
lab=VGND}
C {sky130_fd_pr/res_high_po_1p41.sym} 1250 -200 0 0 {name=R19
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 1230 -200 0 0 {name=p36
sig_type=std_logic
lab=VGND}
C {sky130_fd_pr/res_high_po_1p41.sym} 1250 -80 0 0 {name=R20
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 1230 -80 0 0 {name=p37
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} 1250 -140 0 1 {name=p38
sig_type=std_logic
lab=t5}
C {devices/lab_pin.sym} 1250 -300 0 1 {name=p40
sig_type=std_logic
lab=a5}
C {sky130_fd_pr/res_high_po_1p41.sym} 1375 -300 3 0 {name=R21
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 1375 -280 0 1 {name=p41
sig_type=std_logic
lab=VGND}
C {sky130_fd_pr/res_high_po_1p41.sym} 1500 -200 0 0 {name=R22
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 1480 -200 0 0 {name=p42
sig_type=std_logic
lab=VGND}
C {sky130_fd_pr/res_high_po_1p41.sym} 1500 -80 0 0 {name=R23
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 1480 -80 0 0 {name=p43
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} 1500 -140 0 1 {name=p44
sig_type=std_logic
lab=t6}
C {devices/lab_pin.sym} 1500 -300 0 1 {name=p46
sig_type=std_logic
lab=a6}
C {sky130_fd_pr/res_high_po_1p41.sym} 1625 -300 3 0 {name=R24
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 1625 -280 0 1 {name=p47
sig_type=std_logic
lab=VGND}
C {sky130_fd_pr/res_high_po_1p41.sym} 1750 -200 0 0 {name=R25
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 1730 -200 0 0 {name=p48
sig_type=std_logic
lab=VGND}
C {sky130_fd_pr/res_high_po_1p41.sym} 1750 -80 0 0 {name=R26
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 1730 -80 0 0 {name=p49
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} 1750 -140 0 1 {name=p50
sig_type=std_logic
lab=t7}
C {sky130_fd_pr/res_high_po_1p41.sym} 1900 200 0 0 {name=R27
L=45
model=res_high_po_1p41
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 1880 200 0 0 {name=p53
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} 1900 230 0 1 {name=p54
sig_type=std_logic
lab=VGND}
