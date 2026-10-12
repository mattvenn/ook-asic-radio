v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {tx_top: ring -> level shifter -> antiphase arms (A -> out_p, B -> out_n)
en_p / en_n (1.8 V) gate each arm: both = key normally (off: both arms low); en_n = 0: single-ended fallback
supplies and the arm enables enh_p / enh_n are labelled} -500 -460 0 0 0.4 0.4 {}
N -600 0 -500 0 {}
N -300 0 -200 0 {}
N -200 0 -200 -20 {}
N -200 -20 -100 -20 {}
N 100 -20 250 -20 {}
N 250 -20 250 -120 {}
N 250 -120 400 -120 {}
N 100 20 300 20 {}
N 300 20 300 180 {}
N 300 180 400 180 {}
N -600 280 -100 280 {}
N 600 -120 700 -120 {}
N -600 580 -100 580 {}
N 600 180 700 180 {}
C {devices/iopin.sym} -500 -300 0 0 {name=p1
lab=VDPWR}
C {devices/iopin.sym} -500 -270 0 0 {name=p2
lab=VAPWR}
C {devices/iopin.sym} -500 -240 0 0 {name=p3
lab=VSS}
C {devices/iopin.sym} -600 0 0 1 {name=p6
lab=key}
C {devices/iopin.sym} -600 280 0 1 {name=p18
lab=en_p}
C {devices/iopin.sym} -600 580 0 1 {name=p28
lab=en_n}
C {devices/iopin.sym} 700 -120 0 0 {name=p22
lab=out_p}
C {devices/iopin.sym} 700 180 0 0 {name=p32
lab=out_n}
C {tx_ring.sym} -400 0 0 0 {name=xring}
C {devices/lab_pin.sym} -450 -50 0 0 {name=p4
sig_type=std_logic
lab=VDPWR}
C {devices/lab_pin.sym} -450 50 0 0 {name=p5
sig_type=std_logic
lab=VSS}
C {tx_ls.sym} 0 0 0 0 {name=xls}
C {devices/lab_pin.sym} -50 -70 0 0 {name=p7
sig_type=std_logic
lab=VDPWR}
C {devices/lab_pin.sym} -50 70 0 0 {name=p8
sig_type=std_logic
lab=VSS}
C {devices/lab_pin.sym} -10 -70 0 1 {name=p9
sig_type=std_logic
lab=VAPWR}
C {devices/lab_pin.sym} -200 0 0 0 {name=p10
sig_type=std_logic
lab=ring}
C {devices/lab_pin.sym} 100 -20 0 1 {name=p11
sig_type=std_logic
lab=a}
C {devices/lab_pin.sym} 100 20 0 1 {name=p12
sig_type=std_logic
lab=b}
C {tx_ls.sym} 0 300 0 0 {name=xlse_p
kn=1
kp=1
wpi=1
wni=0.42}
C {devices/lab_pin.sym} -50 230 0 0 {name=p13
sig_type=std_logic
lab=VDPWR}
C {devices/lab_pin.sym} -50 370 0 0 {name=p14
sig_type=std_logic
lab=VSS}
C {devices/lab_pin.sym} 100 280 0 1 {name=p15
sig_type=std_logic
lab=enh_p}
C {devices/lab_pin.sym} 100 320 0 1 {name=p16
sig_type=std_logic
lab=enhb_p}
C {devices/lab_pin.sym} -10 230 0 1 {name=p17
sig_type=std_logic
lab=VAPWR}
C {tx_drv.sym} 500 -100 0 0 {name=xdrv_p}
C {devices/lab_pin.sym} 400 -80 0 0 {name=p19
sig_type=std_logic
lab=enh_p}
C {devices/lab_pin.sym} 450 -170 0 0 {name=p20
sig_type=std_logic
lab=VAPWR}
C {devices/lab_pin.sym} 450 -30 0 0 {name=p21
sig_type=std_logic
lab=VSS}
C {tx_ls.sym} 0 600 0 0 {name=xlse_n
kn=1
kp=1
wpi=1
wni=0.42}
C {devices/lab_pin.sym} -50 530 0 0 {name=p23
sig_type=std_logic
lab=VDPWR}
C {devices/lab_pin.sym} -50 670 0 0 {name=p24
sig_type=std_logic
lab=VSS}
C {devices/lab_pin.sym} 100 580 0 1 {name=p25
sig_type=std_logic
lab=enh_n}
C {devices/lab_pin.sym} 100 620 0 1 {name=p26
sig_type=std_logic
lab=enhb_n}
C {devices/lab_pin.sym} -10 530 0 1 {name=p27
sig_type=std_logic
lab=VAPWR}
C {tx_drv.sym} 500 200 0 0 {name=xdrv_n}
C {devices/lab_pin.sym} 400 220 0 0 {name=p29
sig_type=std_logic
lab=enh_n}
C {devices/lab_pin.sym} 450 130 0 0 {name=p30
sig_type=std_logic
lab=VAPWR}
C {devices/lab_pin.sym} 450 270 0 0 {name=p31
sig_type=std_logic
lab=VSS}
