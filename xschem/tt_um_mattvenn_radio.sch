v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {tt_um_mattvenn_radio: radio_analog + radio_digital (hardened macro) on the TT pins
ua[0]/ua[1] RX dipole, ua[2] debug (det, dbg_en only), ua[3]/ua[4] TX dipole
enables / clocks wired across; rx_en, trim and comp are labelled} -700 -560 0 0 0.4 0.4 {}
N -440 -180 -500 -180 {}
N -440 -140 -500 -140 {}
N -440 -100 -500 -100 {}
N -440 -60 -500 -60 {}
N -160 -180 -100 -180 {}
N -160 -140 -100 -140 {}
N -160 -100 -100 -100 {}
N -160 -20 260 -20 {}
N -160 20 260 20 {}
N -160 100 0 100 {}
N 0 100 0 60 {}
N 0 60 260 60 {}
N -160 140 40 140 {}
N 40 140 40 100 {}
N 40 100 260 100 {}
N -160 180 80 180 {}
N 80 180 80 140 {}
N 80 140 260 140 {}
C {devices/iopin.sym} -700 -400 0 0 {name=p1
lab=VGND}
C {devices/iopin.sym} -700 -370 0 0 {name=p2
lab=VDPWR}
C {devices/iopin.sym} -700 -340 0 0 {name=p3
lab=VAPWR}
C {devices/iopin.sym} -500 -100 0 1 {name=p13
lab=ui_in[7:0]}
C {devices/iopin.sym} -100 -180 0 0 {name=p15
lab=uo_out[7:0]}
C {devices/iopin.sym} -500 -60 0 1 {name=p14
lab=uio_in[7:0]}
C {devices/iopin.sym} -100 -140 0 0 {name=p16
lab=uio_out[7:0]}
C {devices/iopin.sym} -100 -100 0 0 {name=p17
lab=uio_oe[7:0]}
C {devices/iopin.sym} -700 -310 0 0 {name=p4
lab=ua[7:0]}
C {devices/iopin.sym} -700 -280 0 0 {name=p5
lab=ena}
C {devices/iopin.sym} -500 -180 0 1 {name=p11
lab=clk}
C {devices/iopin.sym} -500 -140 0 1 {name=p12
lab=rst_n}
C {radio_digital.sym} -300 0 0 0 {name=xdig}
C {devices/lab_pin.sym} -440 -20 0 0 {name=p6
sig_type=std_logic
lab=comp}
C {devices/lab_pin.sym} -160 60 0 1 {name=p7
sig_type=std_logic
lab=rx_en}
C {devices/lab_pin.sym} -390 -230 0 0 {name=p8
sig_type=std_logic
lab=VDPWR}
C {devices/lab_pin.sym} -390 230 0 0 {name=p9
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} -160 -60 0 1 {name=p10
sig_type=std_logic
lab=trim[7:0]}
C {radio_analog.sym} 400 60 0 0 {name=xana}
C {devices/lab_pin.sym} 350 -110 0 1 {name=p18
sig_type=std_logic
lab=VAPWR}
C {devices/lab_pin.sym} 260 -60 0 0 {name=p19
sig_type=std_logic
lab=rx_en}
C {devices/lab_pin.sym} 540 -60 0 1 {name=p20
sig_type=std_logic
lab=comp}
C {devices/lab_pin.sym} 310 -110 0 0 {name=p21
sig_type=std_logic
lab=VDPWR}
C {devices/lab_pin.sym} 310 230 0 0 {name=p22
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} 540 60 0 1 {name=p23
sig_type=std_logic
lab=ua[0]}
C {devices/lab_pin.sym} 540 100 0 1 {name=p24
sig_type=std_logic
lab=ua[1]}
C {devices/lab_pin.sym} 540 140 0 1 {name=p25
sig_type=std_logic
lab=ua[2]}
C {devices/lab_pin.sym} 540 -20 0 1 {name=p26
sig_type=std_logic
lab=ua[3]}
C {devices/lab_pin.sym} 540 20 0 1 {name=p27
sig_type=std_logic
lab=ua[4]}
C {devices/lab_pin.sym} 260 180 0 0 {name=p28
sig_type=std_logic
lab=trim[7:0]}
C {devices/lab_pin.sym} -160 -20 0 1 {name=p29
sig_type=std_logic
lab=tx_en}
C {devices/lab_pin.sym} -160 20 0 1 {name=p30
sig_type=std_logic
lab=tx_en_n}
C {devices/lab_pin.sym} -160 100 0 1 {name=p31
sig_type=std_logic
lab=dbg_en}
C {devices/lab_pin.sym} -160 140 0 1 {name=p32
sig_type=std_logic
lab=sc_phi1}
C {devices/lab_pin.sym} -160 180 0 1 {name=p33
sig_type=std_logic
lab=sc_phi2}
