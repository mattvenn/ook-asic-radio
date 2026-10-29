v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {radio_analog: all analog blocks, real bias (bias_gen on rx_en)
RX: rx_p/n -> lna_chain -> log_det -> lpf_rc -> avg_sc / comp_ct (+ r2r trim) -> comp_out; det -> dbg_tg -> dbg. TX: tx_top -> tx_p/n
signal paths are wired; supplies, bias currents, clocks and enables are labelled} -900 -760 0 0 0.4 0.4 {}
T {C = 1pF (22 x 22 um)} 1316 460 0 0 0.25 0.25 {}
N -120 -220 -240 -220 {}
N -120 -180 -240 -180 {}
N 120 -140 380 -140 {}
N 120 -100 380 -100 {}
N 120 -60 380 -60 {}
N 120 -20 380 -20 {}
N 120 20 380 20 {}
N 120 60 380 60 {}
N 120 100 380 100 {}
N 120 140 380 140 {}
N 120 180 380 180 {}
N 120 220 380 220 {}
N 620 -140 700 -140 {}
N 700 -140 750 -140 {}
N 950 -140 1000 -140 {}
N 1000 -140 1000 -340 {}
N 1000 -340 1050 -340 {}
N 1000 -140 1350 -140 {}
N 1350 -140 1350 -120 {}
N 1350 -120 1400 -120 {}
N 1250 -340 1300 -340 {}
N 1300 -340 1300 -160 {}
N 1300 -160 1400 -160 {}
N 1250 360 1300 360 {}
N 1300 360 1370 360 {}
N 1370 360 1370 -80 {}
N 1370 -80 1400 -80 {}
N 1600 -160 1700 -160 {}
N 700 -140 700 130 {}
N 700 130 800 130 {}
N 1000 130 1060 130 {}
N -300 760 -150 760 {}
N -150 760 -100 760 {}
N -150 760 -150 800 {}
N -150 800 -100 800 {}
N -300 840 -100 840 {}
N 100 760 200 760 {}
N 100 800 200 800 {}
C {devices/iopin.sym} -900 -600 0 0 {name=p1
lab=VDPWR}
C {devices/iopin.sym} -900 -570 0 0 {name=p2
lab=VAPWR}
C {devices/iopin.sym} -900 -540 0 0 {name=p3
lab=VGND}
C {devices/iopin.sym} -900 -510 0 0 {name=p4
lab=rx_en}
C {devices/iopin.sym} -300 760 0 1 {name=p71
lab=tx_en}
C {devices/iopin.sym} -300 840 0 1 {name=p72
lab=tx_en_n}
C {devices/iopin.sym} -900 -480 0 0 {name=p5
lab=dbg_en}
C {devices/iopin.sym} -900 -450 0 0 {name=p6
lab=lna_lo_n}
C {devices/iopin.sym} -900 -420 0 0 {name=p7
lab=sc_phi1}
C {devices/iopin.sym} -900 -390 0 0 {name=p8
lab=sc_phi2}
C {devices/iopin.sym} -900 -360 0 0 {name=p9
lab=trim[7:0]}
C {devices/iopin.sym} 1700 -160 0 0 {name=p63
lab=comp_out}
C {devices/iopin.sym} 200 760 0 0 {name=p73
lab=tx_p}
C {devices/iopin.sym} 200 800 0 0 {name=p74
lab=tx_n}
C {devices/iopin.sym} -240 -220 0 1 {name=p34
lab=rx_p}
C {devices/iopin.sym} -240 -180 0 1 {name=p35
lab=rx_n}
C {devices/iopin.sym} 1060 130 0 0 {name=p67
lab=dbg}
C {bias_gen.sym} -500 450 0 0 {name=xbias}
C {devices/lab_pin.sym} -600 390 0 0 {name=p10
sig_type=std_logic
lab=rx_en}
C {devices/lab_pin.sym} -400 390 0 1 {name=p11
sig_type=std_logic
lab=vcm}
C {devices/lab_pin.sym} -400 430 0 1 {name=p12
sig_type=std_logic
lab=ib_chain}
C {devices/lab_pin.sym} -400 470 0 1 {name=p13
sig_type=std_logic
lab=ib_det}
C {devices/lab_pin.sym} -400 510 0 1 {name=p14
sig_type=std_logic
lab=ib_comp}
C {devices/lab_pin.sym} -550 340 0 0 {name=p15
sig_type=std_logic
lab=VDPWR}
C {devices/lab_pin.sym} -550 560 0 0 {name=p16
sig_type=std_logic
lab=VGND}
C {lna_chain.sym} 0 0 0 0 {name=xchain}
C {devices/lab_pin.sym} -120 -140 0 0 {name=p17
sig_type=std_logic
lab=ib_chain}
C {devices/lab_pin.sym} -120 -100 0 0 {name=p18
sig_type=std_logic
lab=vcm}
C {devices/lab_pin.sym} -120 -60 0 0 {name=p19
sig_type=std_logic
lab=lna_lo_n}
C {devices/lab_pin.sym} 120 -220 0 1 {name=p20
sig_type=std_logic
lab=out_p}
C {devices/lab_pin.sym} 120 -180 0 1 {name=p21
sig_type=std_logic
lab=out_n}
C {devices/lab_pin.sym} -70 -270 0 0 {name=p22
sig_type=std_logic
lab=VDPWR}
C {devices/lab_pin.sym} -70 270 0 0 {name=p23
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} 120 -140 0 1 {name=p24
sig_type=std_logic
lab=o1p}
C {devices/lab_pin.sym} 120 -100 0 1 {name=p25
sig_type=std_logic
lab=o1n}
C {devices/lab_pin.sym} 120 -60 0 1 {name=p26
sig_type=std_logic
lab=o2p}
C {devices/lab_pin.sym} 120 -20 0 1 {name=p27
sig_type=std_logic
lab=o2n}
C {devices/lab_pin.sym} 120 20 0 1 {name=p28
sig_type=std_logic
lab=o3p}
C {devices/lab_pin.sym} 120 60 0 1 {name=p29
sig_type=std_logic
lab=o3n}
C {devices/lab_pin.sym} 120 100 0 1 {name=p30
sig_type=std_logic
lab=o4p}
C {devices/lab_pin.sym} 120 140 0 1 {name=p31
sig_type=std_logic
lab=o4n}
C {devices/lab_pin.sym} 120 180 0 1 {name=p32
sig_type=std_logic
lab=o5p}
C {devices/lab_pin.sym} 120 220 0 1 {name=p33
sig_type=std_logic
lab=o5n}
C {log_det.sym} 500 100 0 0 {name=xdet}
C {devices/lab_pin.sym} 380 340 0 0 {name=p36
sig_type=std_logic
lab=ib_det}
C {devices/lab_pin.sym} 430 -190 0 0 {name=p37
sig_type=std_logic
lab=VDPWR}
C {devices/lab_pin.sym} 430 390 0 0 {name=p38
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} 380 260 0 0 {name=p39
sig_type=std_logic
lab=out_p}
C {devices/lab_pin.sym} 380 300 0 0 {name=p40
sig_type=std_logic
lab=out_n}
C {lpf_rc.sym} 850 -140 0 0 {name=xlpf}
C {devices/lab_pin.sym} 800 -90 0 0 {name=p41
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} 700 -140 0 1 {name=p42
sig_type=std_logic
lab=det}
C {avg_sc.sym} 1150 -300 0 0 {name=xavg}
C {devices/lab_pin.sym} 1050 -300 0 0 {name=p43
sig_type=std_logic
lab=sc_phi1}
C {devices/lab_pin.sym} 1050 -260 0 0 {name=p44
sig_type=std_logic
lab=sc_phi2}
C {devices/lab_pin.sym} 1100 -390 0 0 {name=p45
sig_type=std_logic
lab=VDPWR}
C {devices/lab_pin.sym} 1100 -210 0 0 {name=p46
sig_type=std_logic
lab=VGND}
C {r2r.sym} 1150 500 0 0 {name=xdac}
C {devices/lab_pin.sym} 1100 690 0 0 {name=p47
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} 1050 360 0 0 {name=p48
sig_type=std_logic
lab=trim[0]}
C {devices/lab_pin.sym} 1050 400 0 0 {name=p49
sig_type=std_logic
lab=trim[1]}
C {devices/lab_pin.sym} 1050 440 0 0 {name=p50
sig_type=std_logic
lab=trim[2]}
C {devices/lab_pin.sym} 1050 480 0 0 {name=p51
sig_type=std_logic
lab=trim[3]}
C {devices/lab_pin.sym} 1050 520 0 0 {name=p52
sig_type=std_logic
lab=trim[4]}
C {devices/lab_pin.sym} 1050 560 0 0 {name=p53
sig_type=std_logic
lab=trim[5]}
C {devices/lab_pin.sym} 1050 600 0 0 {name=p54
sig_type=std_logic
lab=trim[6]}
C {devices/lab_pin.sym} 1050 640 0 0 {name=p55
sig_type=std_logic
lab=trim[7]}
C {sky130_fd_pr/cap_mim_m3_1.sym} 1300 390 0 1 {name=Ctrim
model=cap_mim_m3_1
W='sqrt((1e-12)/1/2.06e-15)'
L='sqrt((1e-12)/1/2.06e-15)'
MF=1
spiceprefix=X}
C {devices/lab_pin.sym} 1300 420 0 1 {name=p56
sig_type=std_logic
lab=VGND}
C {comp_ct.sym} 1500 -100 0 0 {name=xcomp}
C {devices/lab_pin.sym} 1400 -40 0 0 {name=p57
sig_type=std_logic
lab=ib_comp}
C {devices/lab_pin.sym} 1450 -210 0 0 {name=p58
sig_type=std_logic
lab=VDPWR}
C {devices/lab_pin.sym} 1450 10 0 0 {name=p59
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} 1000 -140 0 1 {name=p60
sig_type=std_logic
lab=lpf}
C {devices/lab_pin.sym} 1250 -340 0 1 {name=p61
sig_type=std_logic
lab=avg}
C {devices/lab_pin.sym} 1300 360 0 0 {name=p62
sig_type=std_logic
lab=trim}
C {dbg_tg.sym} 900 150 0 0 {name=xdbg}
C {devices/lab_pin.sym} 800 170 0 0 {name=p64
sig_type=std_logic
lab=dbg_en}
C {devices/lab_pin.sym} 850 80 0 0 {name=p65
sig_type=std_logic
lab=VDPWR}
C {devices/lab_pin.sym} 850 220 0 0 {name=p66
sig_type=std_logic
lab=VGND}
C {tx_top.sym} 0 800 0 0 {name=xtx}
C {devices/lab_pin.sym} -50 710 0 0 {name=p68
sig_type=std_logic
lab=VDPWR}
C {devices/lab_pin.sym} -50 890 0 0 {name=p69
sig_type=std_logic
lab=VGND}
C {devices/lab_pin.sym} -10 710 0 1 {name=p70
sig_type=std_logic
lab=VAPWR}
C {decap_vapwr.sym} 450 800 0 0 {name=xdeca}
C {devices/lab_pin.sym} 420 750 0 0 {name=p75
sig_type=std_logic
lab=VAPWR}
C {devices/lab_pin.sym} 420 850 0 0 {name=p76
sig_type=std_logic
lab=VGND}
C {decap_vdpwr.sym} 650 800 0 0 {name=xdecd}
C {devices/lab_pin.sym} 620 750 0 0 {name=p77
sig_type=std_logic
lab=VDPWR}
C {devices/lab_pin.sym} 620 850 0 0 {name=p78
sig_type=std_logic
lab=VGND}
