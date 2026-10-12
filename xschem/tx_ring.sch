v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {tx_ring: nand2_2 enable + 22 x inv_2 (23 stages), cw wiring C per stage
cw 3.2 fF reproduces the ttsky25b ring extracted (598 MHz tt); en = 0 stops it with out = 1
std cell supplies are instance properties (VDD / VSS)} -500 -360 0 0 0.4 0.4 {}
N -500 -20 -360 -20 {}
N -240 0 -210 0 {}
N -210 0 -190 0 {}
N -190 0 -140 0 {}
N -210 0 -210 -80 {}
N -210 -80 -120 -80 {}
N -60 0 0 0 {}
N 0 0 60 0 {}
N 140 0 200 0 {}
N 200 0 260 0 {}
N 340 0 400 0 {}
N 400 0 460 0 {}
N 540 0 600 0 {}
N 600 0 660 0 {}
N 740 0 800 0 {}
N 800 0 860 0 {}
N 940 0 1000 0 {}
N 1000 0 1060 0 {}
N 1140 0 1200 0 {}
N 1200 0 1260 0 {}
N 1340 0 1400 0 {}
N 1400 0 1460 0 {}
N 1540 0 1600 0 {}
N 1600 0 1660 0 {}
N 1740 0 1800 0 {}
N 1800 0 1860 0 {}
N 1940 0 2000 0 {}
N 2000 0 2060 0 {}
N 2060 0 2060 300 {}
N 2060 300 1940 300 {}
N 1740 300 1800 300 {}
N 1800 300 1860 300 {}
N 1540 300 1600 300 {}
N 1600 300 1660 300 {}
N 1340 300 1400 300 {}
N 1400 300 1460 300 {}
N 1140 300 1200 300 {}
N 1200 300 1260 300 {}
N 940 300 1000 300 {}
N 1000 300 1060 300 {}
N 740 300 800 300 {}
N 800 300 860 300 {}
N 540 300 600 300 {}
N 600 300 660 300 {}
N 340 300 400 300 {}
N 400 300 460 300 {}
N 140 300 200 300 {}
N 200 300 260 300 {}
N -60 300 0 300 {}
N 0 300 60 300 {}
N -420 300 -200 300 {}
N -200 300 -140 300 {}
N -420 300 -420 20 {}
N -420 20 -360 20 {}
N -190 60 -190 100 {}
N 0 60 0 100 {}
N 200 60 200 100 {}
N 400 60 400 100 {}
N 600 60 600 100 {}
N 800 60 800 100 {}
N 1000 60 1000 100 {}
N 1200 60 1200 100 {}
N 1400 60 1400 100 {}
N 1600 60 1600 100 {}
N 1800 60 1800 100 {}
N 2000 60 2000 100 {}
N -300 100 -190 100 {}
N -190 100 0 100 {}
N 0 100 200 100 {}
N 200 100 400 100 {}
N 400 100 600 100 {}
N 600 100 800 100 {}
N 800 100 1000 100 {}
N 1000 100 1200 100 {}
N 1200 100 1400 100 {}
N 1400 100 1600 100 {}
N 1600 100 1800 100 {}
N 1800 100 2000 100 {}
N 1800 360 1800 400 {}
N 1600 360 1600 400 {}
N 1400 360 1400 400 {}
N 1200 360 1200 400 {}
N 1000 360 1000 400 {}
N 800 360 800 400 {}
N 600 360 600 400 {}
N 400 360 400 400 {}
N 200 360 200 400 {}
N 0 360 0 400 {}
N -200 360 -200 400 {}
N -500 400 -200 400 {}
N -200 400 0 400 {}
N 0 400 200 400 {}
N 200 400 400 400 {}
N 400 400 600 400 {}
N 600 400 800 400 {}
N 800 400 1000 400 {}
N 1000 400 1200 400 {}
N 1200 400 1400 400 {}
N 1400 400 1600 400 {}
N 1600 400 1800 400 {}
N 1800 400 2000 400 {}
C {devices/iopin.sym} -500 -150 0 1 {name=p1
lab=VDD}
C {devices/iopin.sym} -500 400 0 1 {name=p27
lab=VSS}
C {devices/iopin.sym} -500 -20 0 1 {name=p2
lab=en}
C {devices/iopin.sym} -120 -80 0 0 {name=p3
lab=out}
C {sky130_stdcells/nand2_2.sym} -300 0 0 0 {name=xr0
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} -190 30 0 0 {name=Cr0
value='cw'
m=1}
C {sky130_stdcells/inv_2.sym} -100 0 0 0 {name=xr1
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} 0 30 0 0 {name=Cr1
value='cw'
m=1}
C {devices/lab_pin.sym} 0 0 0 0 {name=p4
sig_type=std_logic
lab=r1}
C {sky130_stdcells/inv_2.sym} 100 0 0 0 {name=xr2
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} 200 30 0 0 {name=Cr2
value='cw'
m=1}
C {devices/lab_pin.sym} 200 0 0 0 {name=p5
sig_type=std_logic
lab=r2}
C {sky130_stdcells/inv_2.sym} 300 0 0 0 {name=xr3
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} 400 30 0 0 {name=Cr3
value='cw'
m=1}
C {devices/lab_pin.sym} 400 0 0 0 {name=p6
sig_type=std_logic
lab=r3}
C {sky130_stdcells/inv_2.sym} 500 0 0 0 {name=xr4
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} 600 30 0 0 {name=Cr4
value='cw'
m=1}
C {devices/lab_pin.sym} 600 0 0 0 {name=p7
sig_type=std_logic
lab=r4}
C {sky130_stdcells/inv_2.sym} 700 0 0 0 {name=xr5
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} 800 30 0 0 {name=Cr5
value='cw'
m=1}
C {devices/lab_pin.sym} 800 0 0 0 {name=p8
sig_type=std_logic
lab=r5}
C {sky130_stdcells/inv_2.sym} 900 0 0 0 {name=xr6
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} 1000 30 0 0 {name=Cr6
value='cw'
m=1}
C {devices/lab_pin.sym} 1000 0 0 0 {name=p9
sig_type=std_logic
lab=r6}
C {sky130_stdcells/inv_2.sym} 1100 0 0 0 {name=xr7
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} 1200 30 0 0 {name=Cr7
value='cw'
m=1}
C {devices/lab_pin.sym} 1200 0 0 0 {name=p10
sig_type=std_logic
lab=r7}
C {sky130_stdcells/inv_2.sym} 1300 0 0 0 {name=xr8
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} 1400 30 0 0 {name=Cr8
value='cw'
m=1}
C {devices/lab_pin.sym} 1400 0 0 0 {name=p11
sig_type=std_logic
lab=r8}
C {sky130_stdcells/inv_2.sym} 1500 0 0 0 {name=xr9
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} 1600 30 0 0 {name=Cr9
value='cw'
m=1}
C {devices/lab_pin.sym} 1600 0 0 0 {name=p12
sig_type=std_logic
lab=r9}
C {sky130_stdcells/inv_2.sym} 1700 0 0 0 {name=xr10
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} 1800 30 0 0 {name=Cr10
value='cw'
m=1}
C {devices/lab_pin.sym} 1800 0 0 0 {name=p13
sig_type=std_logic
lab=r10}
C {sky130_stdcells/inv_2.sym} 1900 0 0 0 {name=xr11
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} 2000 30 0 0 {name=Cr11
value='cw'
m=1}
C {devices/lab_pin.sym} 2000 0 0 0 {name=p14
sig_type=std_logic
lab=r11}
C {sky130_stdcells/inv_2.sym} 1900 300 0 1 {name=xr12
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} 1800 330 0 0 {name=Cr12
value='cw'
m=1}
C {devices/lab_pin.sym} 1800 300 0 1 {name=p15
sig_type=std_logic
lab=r12}
C {sky130_stdcells/inv_2.sym} 1700 300 0 1 {name=xr13
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} 1600 330 0 0 {name=Cr13
value='cw'
m=1}
C {devices/lab_pin.sym} 1600 300 0 1 {name=p16
sig_type=std_logic
lab=r13}
C {sky130_stdcells/inv_2.sym} 1500 300 0 1 {name=xr14
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} 1400 330 0 0 {name=Cr14
value='cw'
m=1}
C {devices/lab_pin.sym} 1400 300 0 1 {name=p17
sig_type=std_logic
lab=r14}
C {sky130_stdcells/inv_2.sym} 1300 300 0 1 {name=xr15
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} 1200 330 0 0 {name=Cr15
value='cw'
m=1}
C {devices/lab_pin.sym} 1200 300 0 1 {name=p18
sig_type=std_logic
lab=r15}
C {sky130_stdcells/inv_2.sym} 1100 300 0 1 {name=xr16
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} 1000 330 0 0 {name=Cr16
value='cw'
m=1}
C {devices/lab_pin.sym} 1000 300 0 1 {name=p19
sig_type=std_logic
lab=r16}
C {sky130_stdcells/inv_2.sym} 900 300 0 1 {name=xr17
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} 800 330 0 0 {name=Cr17
value='cw'
m=1}
C {devices/lab_pin.sym} 800 300 0 1 {name=p20
sig_type=std_logic
lab=r17}
C {sky130_stdcells/inv_2.sym} 700 300 0 1 {name=xr18
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} 600 330 0 0 {name=Cr18
value='cw'
m=1}
C {devices/lab_pin.sym} 600 300 0 1 {name=p21
sig_type=std_logic
lab=r18}
C {sky130_stdcells/inv_2.sym} 500 300 0 1 {name=xr19
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} 400 330 0 0 {name=Cr19
value='cw'
m=1}
C {devices/lab_pin.sym} 400 300 0 1 {name=p22
sig_type=std_logic
lab=r19}
C {sky130_stdcells/inv_2.sym} 300 300 0 1 {name=xr20
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} 200 330 0 0 {name=Cr20
value='cw'
m=1}
C {devices/lab_pin.sym} 200 300 0 1 {name=p23
sig_type=std_logic
lab=r20}
C {sky130_stdcells/inv_2.sym} 100 300 0 1 {name=xr21
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} 0 330 0 0 {name=Cr21
value='cw'
m=1}
C {devices/lab_pin.sym} 0 300 0 1 {name=p24
sig_type=std_logic
lab=r21}
C {sky130_stdcells/inv_2.sym} -100 300 0 1 {name=xr22
VGND=VSS
VNB=VSS
VPB=VDD
VPWR=VDD
prefix=sky130_fd_sc_hd__}
C {devices/capa.sym} -200 330 0 0 {name=Cr22
value='cw'
m=1}
C {devices/lab_pin.sym} -200 300 0 1 {name=p25
sig_type=std_logic
lab=r22}
C {devices/lab_pin.sym} -300 100 0 0 {name=p26
sig_type=std_logic
lab=VSS}
