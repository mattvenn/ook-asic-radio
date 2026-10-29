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
N -440 -200 -500 -200 {}
N -440 -160 -500 -160 {}
N -440 -120 -500 -120 {}
N -440 -80 -500 -80 {}
N -160 -200 -100 -200 {}
N -160 -160 -100 -160 {}
N -160 -120 -100 -120 {}
N -160 -40 260 -40 {}
N -160 0 260 0 {}
N -160 80 0 80 {}
N 0 80 0 40 {}
N 0 40 260 40 {}
N -160 120 20 120 {}
N 20 120 20 80 {}
N 20 80 260 80 {}
N -160 160 40 160 {}
N 40 160 40 120 {}
N 40 120 260 120 {}
N -160 200 80 200 {}
N 80 200 80 160 {}
N 80 160 260 160 {}
C {devices/iopin.sym} -700 -400 0 0 {name=p1
lab=VGND}
C {devices/iopin.sym} -700 -370 0 0 {name=p2
lab=VDPWR}
C {devices/iopin.sym} -700 -340 0 0 {name=p3
lab=VAPWR}
C {devices/iopin.sym} -500 -120 0 1 {name=p13
lab=ui_in[7:0]}
C {devices/iopin.sym} -100 -200 0 0 {name=p15
lab=uo_out[7:0]}
C {devices/iopin.sym} -500 -80 0 1 {name=p14
lab=uio_in[7:0]}
C {devices/iopin.sym} -100 -160 0 0 {name=p16
lab=uio_out[7:0]}
C {devices/iopin.sym} -100 -120 0 0 {name=p17
lab=uio_oe[7:0]}
C {devices/iopin.sym} -700 -310 0 0 {name=p4
lab=ua[7:0]}
C {devices/iopin.sym} -700 -280 0 0 {name=p5
lab=ena}
C {devices/iopin.sym} -500 -200 0 1 {name=p11
lab=clk}
C {devices/iopin.sym} -500 -160 0 1 {name=p12
lab=rst_n}
C {radio_digital.sym} -300 0 0 0 {name=xdig}
C {devices/lab_pin.sym} -440 -40 0 0 {name=p6
sig_type=std_logic
lab=comp}
C {devices/lab_pin.sym} -160 40 0 1 {name=p7
sig_type=std_logic
lab=rx_en}
C {devices/lab_pin.sym} -390 -250 0 0 {name=p8
sig_type=std_logic
lab=VDPWR}
C {devices/lab_pin.sym} -390 250 0 0 {name=p9
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} -160 -80 0 1 {name=p10
sig_type=std_logic
lab=trim[7:0]}
C {radio_analog.sym} 400 60 0 0 {name=xana}
C {devices/lab_pin.sym} 350 -130 0 1 {name=p18
sig_type=std_logic
lab=VAPWR}
C {devices/lab_pin.sym} 260 -80 0 0 {name=p19
sig_type=std_logic
lab=rx_en}
C {devices/lab_pin.sym} 540 -80 0 1 {name=p20
sig_type=std_logic
lab=comp}
C {devices/lab_pin.sym} 310 -130 0 0 {name=p21
sig_type=std_logic
lab=VDPWR}
C {devices/lab_pin.sym} 310 250 0 0 {name=p22
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} 540 40 0 1 {name=p23
sig_type=std_logic
lab=ua[0]}
C {devices/lab_pin.sym} 540 80 0 1 {name=p24
sig_type=std_logic
lab=ua[1]}
C {devices/lab_pin.sym} 540 120 0 1 {name=p25
sig_type=std_logic
lab=ua[2]}
C {devices/lab_pin.sym} 540 -40 0 1 {name=p26
sig_type=std_logic
lab=ua[3]}
C {devices/lab_pin.sym} 540 0 0 1 {name=p27
sig_type=std_logic
lab=ua[4]}
C {devices/lab_pin.sym} 260 200 0 0 {name=p28
sig_type=std_logic
lab=trim[7:0]}
C {devices/lab_pin.sym} -160 -40 0 1 {name=p29
sig_type=std_logic
lab=tx_en}
C {devices/lab_pin.sym} -160 0 0 1 {name=p30
sig_type=std_logic
lab=tx_en_n}
C {devices/lab_pin.sym} -160 80 0 1 {name=p31
sig_type=std_logic
lab=dbg_en}
C {devices/lab_pin.sym} -160 120 0 1 {name=p32
sig_type=std_logic
lab=lna_lo_n}
C {devices/lab_pin.sym} -160 160 0 1 {name=p33
sig_type=std_logic
lab=sc_phi1}
C {devices/lab_pin.sym} -160 200 0 1 {name=p34
sig_type=std_logic
lab=sc_phi2}
