#!/bin/bash

verilator --lint-only -DSIM -Wall -Wno-DECLFILENAME -Wno-MULTITOP *.v
