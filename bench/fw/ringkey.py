"""
On-board (RP2350 MicroPython) helper: select the ttsky25b ring oscillator
project and key its enable pin (ui_in[0] = ring 1, ui_in[1] = ring 2).

Keying runs on a PIO state machine so timing is exact and independent of
Python. The board's carrier detect may fail, so the shuttle is forced.

Usage (from host, see bench/board.py):
    import ringkey
    ringkey.main('on')                  # ring 1 steady on
    ringkey.main('off')
    ringkey.main('square', 1000)        # OOK square wave, Hz
    ringkey.main('uart', 9600)          # repeated OOK packet, baud
"""
import time
import rp2
from machine import Pin
from ttboard.demoboard import DemoBoard
from ttboard.project_mux import HardcodedShuttle
from ttboard.mode import RPMode

PROJECT = 'tt_um_mattvenn_analog_ring_osc'
SHUTTLE = 'ttsky25b'

# preamble, sync word, payload: shared with the host analysis (bench/rf.py)
PACKET = bytes([0x55] * 4) + bytes([0x2D, 0xD4]) + b'HELLO TT'
PACKET_GAP_MS = 10


@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def square():
    # half-period count in X; pull(noblock) re-loads X when FIFO is empty
    pull(noblock)
    mov(x, osr)
    set(pins, 1)
    mov(y, x)
    label('hi')
    jmp(y_dec, 'hi')
    set(pins, 0)
    mov(y, x)
    label('lo')
    jmp(y_dec, 'lo')


@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_init=rp2.PIO.OUT_LOW,
             out_shiftdir=rp2.PIO.SHIFT_RIGHT)
def uart_tx():
    # 8N1 UART, 8 PIO cycles per bit. Idle = 0 = carrier off, so each
    # byte is a burst: start bit = carrier on, data bits inverted
    # (host sends ~byte), stop bit = carrier off.
    pull()
    set(x, 7).side(1)[7]
    label('bitloop')
    out(pins, 1)[6]
    jmp(x_dec, 'bitloop')
    nop().side(0)[6]


def setup(ring=1):
    tt = DemoBoard.get()
    # at power-up the carrier can be mis-detected as FPGA, which selects
    # manual (DIP switch) inputs; we need the RP2350 to drive ui_in
    tt.mode = RPMode.ASIC_RP_CONTROL
    s = tt.shuttle
    if s.run != SHUTTLE:
        s._shuttle_props = HardcodedShuttle(SHUTTLE)
        s._design_index = None
    s.enable(s.get(PROJECT), force=True)
    tt.ui_in.value = 0
    gpio = getattr(tt.pins, 'ui_in%d' % (ring - 1)).gpio_num
    return tt, gpio


def main(mode='on', rate=1000, ring=1):
    tt, gpio = setup(ring)
    bit = 1 << (ring - 1)
    if mode == 'on':
        tt.ui_in.value = bit
        print('ring', ring, 'on, gpio', gpio)
        return
    if mode == 'off':
        tt.ui_in.value = 0
        print('ring', ring, 'off')
        return

    pin = Pin(gpio, Pin.OUT, value=0)
    if mode == 'square':
        sm_freq = 1_000_000
        # loop overhead is ~3 cycles per half period
        half = max(1, sm_freq // (2 * rate) - 3)
        sm = rp2.StateMachine(0, square, freq=sm_freq, set_base=pin)
        sm.put(half)
        sm.active(1)
        print('square keying ring', ring, rate, 'Hz on gpio', gpio)
        while True:
            time.sleep(1)
    elif mode == 'uart':
        sm = rp2.StateMachine(0, uart_tx, freq=8 * rate,
                              sideset_base=pin, out_base=pin)
        sm.active(1)
        print('uart keying ring', ring, rate, 'baud on gpio', gpio)
        while True:
            for b in PACKET:
                sm.put(~b & 0xFF)
            time.sleep_ms(PACKET_GAP_MS + len(PACKET) * 10 * 1000 // rate)
    else:
        print('unknown mode', mode)
