PROJECT_NAME ?= tt_um_mattvenn_radio
MAGIC_RC := $(PDK_ROOT)/sky130A/libs.tech/magic/sky130A.magicrc
# 2x2 tile with the VAPWR (3.3 V) stripe, kept so a 3.3 V TX driver stays possible
TEMPLATE_FILE := tt_analog_2x2_3v3.def
DEF_URL := https://raw.githubusercontent.com/TinyTapeout/tt-support-tools/main/tech/sky130A/def/analog

.PHONY: lvs magic start

magic:
	magic -rcfile $(MAGIC_RC) $(PROJECT_NAME).mag

tt_analog_2x2.def tt_analog_2x2_3v3.def:
	wget $(DEF_URL)/$@

start: $(TEMPLATE_FILE)
	magic -rcfile $(MAGIC_RC) -noconsole -dnull tcl/tt-analog-draw.tcl $(TEMPLATE_FILE) $(PROJECT_NAME)

$(PROJECT_NAME).lvs.spice: $(PROJECT_NAME).mag
	magic -noconsole -dnull tcl/extract_for_lvs.tcl $(PROJECT_NAME)
	rm -f *.ext

antenna:
	magic -noconsole -dnull tcl/antenna.tcl $(PROJECT_NAME)
	rm -f *.ext

drc:
	magic -noconsole -dnull tcl/drc.tcl $(PROJECT_NAME)
	
$(PROJECT_NAME).sim.spice: $(PROJECT_NAME).mag
	magic -noconsole -dnull tcl/extract_for_sim.tcl $(PROJECT_NAME)
	rm -f *.ext

lvs.report: $(PROJECT_NAME).lvs.spice ../src/project.v
	netgen -batch eval "set project $(PROJECT_NAME) ; source tcl/lvs_netgen.tcl"

lvs: lvs.report
	@propOk=1; match=0; port=1; \
    if grep -q "match uniquely" lvs.report; then \
        match=1; \
    fi; \
    if grep -q "Property errors were found" lvs.report; then \
        propOk=0; \
    fi; \
    if grep -q "failed pin matching" lvs.report; then \
        match=0; \
    fi; \
    if grep -q "Final result: Netlists do not match" lvs.report; then \
        match=0; \
    fi; \
    if grep -q "port errors" lvs.report; then \
        port=0; \
    fi; \
    if grep -q "Final result: Circuits match uniquely\." lvs.report; then \
        match=1; \
    fi; \
	if [ $$match -eq 1 ] && [ $$propOk -eq 1 ] && [ $$port -eq 1 ]; then \
        echo "LVS OK"; \
	    exit 0; \
    else \
        echo "LVS FAIL: match=$$match properties=$$propOk port=$$port"; \
	    exit 1; \
    fi

update_gds:
	mkdir -p ../gds ../lef
	magic -noconsole -dnull tcl/update_gds_lef.tcl $(PROJECT_NAME)

clean:
	rm -f lvs.report *.lvs.spice *.nodes
