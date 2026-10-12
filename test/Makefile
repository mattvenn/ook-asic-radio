# cocotb smoke tests at the TT level: tt_um_mattvenn_radio through its TT pins
#   make            (RTL radio_digital)
#   make GL=1       (the hardened netlist, macros/radio_digital/radio_digital.nl.v)
# The wrapper is generated from the top schematic by tools/check_pinout.py (which also
# runs the static pinout check), with radio_analog as a stub that test.py drives / reads.
# make returns success even when tests fail: check results.xml (! grep -q '<failure' results.xml)

SIM ?= icarus
TOPLEVEL_LANG ?= verilog
REPO := $(abspath $(PWD)/..)

WRAPPER := $(PWD)/sim_build/tt_um_mattvenn_radio.v
VERILOG_SOURCES += $(PWD)/tb.v $(WRAPPER)

ifeq ($(GL),1)
SKY130_PDK ?= $(firstword $(wildcard $(PDK_ROOT)/sky130A /foss/pdks/sky130A))
GL_MODELS ?= $(SKY130_PDK)/libs.ref/sky130_fd_sc_hd/verilog
VERILOG_SOURCES += $(REPO)/macros/radio_digital/radio_digital.nl.v $(GL_MODELS)/primitives.v $(GL_MODELS)/sky130_fd_sc_hd.v
COMPILE_ARGS += -DFUNCTIONAL -DUNIT_DELAY=\#1 -DGL
export GL
else
VERILOG_SOURCES += $(wildcard $(REPO)/verilog/rtl/*.v)
COMPILE_ARGS += -DSIM
endif

# test.py reuses verilog/test/test_radio.py's tests and tools/check_pinout.py's PINOUT
export PYTHONPATH := $(PWD):$(REPO)/verilog/test:$(REPO)/tools:$(PYTHONPATH)

TOPLEVEL = tb
COCOTB_TEST_MODULES = test

include $(shell cocotb-config --makefiles)/Makefile.sim

$(WRAPPER): $(REPO)/xschem/tt_um_mattvenn_radio.sch $(REPO)/info.yaml $(REPO)/tools/check_pinout.py
	python3 $(REPO)/tools/check_pinout.py --verilog $@

$(SIM_BUILD)/sim.vvp: $(WRAPPER)
