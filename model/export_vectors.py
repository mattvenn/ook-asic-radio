"""
Export cocotb test vectors from the bit-exact model (radio.py).

RX digital vectors (verilog/test/vectors/rx_<name>.npz):
  comp    uint8[n]  comparator bit presented to the RTL at sample i
  trim    uint8[n]  trim DAC code the RTL must output after sample i
  events  int[k,2]  (chip time, max score) of each detection event, in order
  toggles int[m]    chip times at which the LED toggles
  code    int       the RX's DIP code
Because the digital is deterministic given the comparator bits, replaying
`comp` open-loop must reproduce `trim`, `events` and `toggles` exactly.

TX vectors (verilog/test/vectors/tx_codes.npz):
  chips   uint8[128,127]  chip sequence for each code
  lfsr2   uint8[128]      LFSR2 start state after `code` steps from SEED

Timing contract (see verilog/test/vectors/README.md): sample i is taken at clock
130*i after reset release; the chip counter increments on samples where
i % 8 == 0 (before that sample is processed); phase p's 8-sample window
ends on samples where (i % 8 - p) % 8 == 7.

    python model/export_vectors.py
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'bench'))
import radio
import e2e
from gold import gold, LEN

OUT = os.path.join(os.path.dirname(HERE), 'verilog', 'test', 'vectors')


def clean_comps(code, lead=40, tail=300, sends=1, spacing=None):
    one = radio.tx_chips(code)
    parts = [np.zeros(lead, np.uint8)]
    for i in range(sends):
        parts.append(one)
        if i < sends - 1:
            parts.append(np.zeros((spacing or 0) - len(one), np.uint8))
    parts.append(np.zeros(tail, np.uint8))
    return np.repeat(np.concatenate(parts), radio.S)


def replay(comp, code):
    rx = radio.RxDigital(code)
    trims = np.array([rx.step(c) for c in comp], np.uint8)
    return rx, trims


def save_rx(name, comp, code, note):
    rx, trims = replay(comp, code)
    np.savez_compressed(os.path.join(OUT, f'rx_{name}.npz'), comp=comp.astype(np.uint8),
                        trim=trims, events=np.array(rx.events, int).reshape(-1, 2),
                        toggles=np.array(rx.toggles, int), code=code)
    summary = {'name': name, 'code': code, 'samples': int(len(comp)),
               'events': rx.events, 'toggles': rx.toggles, 'note': note}
    print(json.dumps(summary))
    return summary


def main():
    os.makedirs(OUT, exist_ok=True)
    rng = np.random.default_rng(99)
    code, wrong = e2e.CODE, e2e.WRONG
    sums = []
    # 1. ideal comparator bits, one send
    sums.append(save_rx('clean', clean_comps(code), code, 'ideal bits, one send: 3 events, 1 toggle'))
    # 2. two sends inside the holdoff, then one after it
    sp = radio.PERIOD * radio.BURSTS + 200
    sums.append(save_rx('holdoff', clean_comps(code, sends=2, spacing=sp), code,
                        'second send inside holdoff: still 1 toggle'))
    sp2 = radio.HOLDOFF + 400
    sums.append(save_rx('two_sends', clean_comps(code, sends=2, spacing=sp2), code,
                        'second send after holdoff: 2 toggles'))
    # 3. through the channel + analog model (closed loop -> comparator bits)
    on = e2e.send_onoff(code)
    for name, lvl, case, rxcode, note in (
            ('strong', -70, 'noise', code, 'strong signal'),
            ('weak', -94, 'noise', code, 'near sensitivity'),
            ('wrong_code', -70, 'noise', wrong, 'strong signal, different code: no toggle'),
            ('bursty', -66, 'bursty', code, 'bursty -60 dBm interferer'),
            ('fading', -86, 'fading', code, '+/-10 dB fading'),
            ('no_signal', None, 'noise', code, 'noise only: no toggle')):
        p = 0.0 if lvl is None else 10 ** ((lvl - 30) / 10)
        v = e2e.run_record(on, p, case, rng)
        _, comp, _ = radio.run_rx(v, code)          # comparator bits from the closed loop
        sums.append(save_rx(name, comp, rxcode, note))
    # TX table
    chips = np.array([gold(k) for k in range(128)], np.uint8)
    l2 = np.array([radio.lfsr2_start_state(k) for k in range(128)], np.uint8)
    np.savez_compressed(os.path.join(OUT, 'tx_codes.npz'), chips=chips, lfsr2=l2)
    with open(os.path.join(OUT, 'summary.json'), 'w') as fh:
        json.dump(sums, fh, indent=1)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
