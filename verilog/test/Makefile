# cocotb tests for radio_digital
#   PATH=/home/matt/oss-cad-suite/bin:$PATH make            (icarus)
#   make SIM=verilator
# make returns success even when tests fail: check results.xml
#   ! grep -q '<failure' results.xml   (NB: 'failure' alone matches failures="0")
# Select tests with COCOTB_TEST_FILTER, e.g. COCOTB_TEST_FILTER=test_tx_codes

SIM ?= icarus
# oss-cad-suite vvp + system python: use the wrappers in icarus_bin/
ifneq ($(wildcard $(HOME)/oss-cad-suite/libexec/vvp),)
ICARUS_BIN_DIR ?= $(PWD)/icarus_bin
endif
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES += $(wildcard $(PWD)/../rtl/*.v)

# RTL: behavioural clock gate (rd_cg.v). GL=1: the hardened netlist with the
# sky130 cell models instead (set GL_NETLIST to override the default run).
ifeq ($(GL),1)
GL_NETLIST ?= $(PWD)/../../macros/radio_digital/radio_digital.nl.v
# cell models from the PDK in the tools image (the one the harden used); copy once with
#   tools/osic bash -c 'mkdir -p build/gl_models && cp $PDK_ROOT/$PDK/libs.ref/sky130_fd_sc_hd/verilog/{primitives,sky130_fd_sc_hd}.v build/gl_models/'
GL_MODELS ?= $(PWD)/../../build/gl_models
VERILOG_SOURCES := $(GL_NETLIST) $(GL_MODELS)/primitives.v $(GL_MODELS)/sky130_fd_sc_hd.v
COMPILE_ARGS += -DFUNCTIONAL -DUNIT_DELAY=\#1 -DGL
export GL
else
COMPILE_ARGS += -DSIM
endif

ifeq ($(SIM),verilator)
EXTRA_ARGS += --public-flat-rw -Wno-fatal
endif

TOPLEVEL = radio_digital
COCOTB_TEST_MODULES = test_radio

COCOTB_CONFIG ?= $(HOME)/work/asic-workshop/venv/bin/cocotb-config
include $(shell $(COCOTB_CONFIG) --makefiles)/Makefile.sim
