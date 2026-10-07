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

ifeq ($(SIM),verilator)
EXTRA_ARGS += --public-flat-rw -Wno-fatal
endif

TOPLEVEL = radio_digital
COCOTB_TEST_MODULES = test_radio

COCOTB_CONFIG ?= $(HOME)/work/asic-workshop/venv/bin/cocotb-config
include $(shell $(COCOTB_CONFIG) --makefiles)/Makefile.sim
