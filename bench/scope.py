"""
Keysight HD304MSO helper (InfiniiVision SCPI over LAN).
"""
import os
import time

import numpy as np
import pyvisa

# raw SCPI socket: faster than VXI-11 for big transfers, and VXI-11 can
# wedge if a client dies mid-transfer
RESOURCE = os.environ.get('SCOPE_RESOURCE', 'TCPIP0::192.168.50.11::5025::SOCKET')


class Scope:
    def __init__(self, resource=RESOURCE):
        self.rm = pyvisa.ResourceManager('@py')
        self.s = self.rm.open_resource(resource)
        self.s.timeout = 60000
        self.s.read_termination = '\n'
        self.s.write_termination = '\n'
        self.s.chunk_size = 1 << 20
        self.idn = self.s.query('*IDN?').strip()

    def w(self, cmd):
        self.s.write(cmd)

    def q(self, cmd):
        return self.s.query(cmd).strip()

    def setup_channel(self, ch=1, scale=0.05, fifty=True, offset=0.0):
        """fifty=True only with a coax lead; a passive probe must stay at 1M."""
        self.w(f':CHAN{ch}:DISP 1')
        self.w(f':CHAN{ch}:IMP {"FIFT" if fifty else "ONEM"}')
        # ring output sits at ~0.7 V DC; AC coupling is only available at 1M
        self.w(f':CHAN{ch}:COUP {"DC" if fifty else "AC"}')
        self.w(f':CHAN{ch}:BWL 0')
        self.w(f':CHAN{ch}:SCAL {scale}')
        self.w(f':CHAN{ch}:OFFS {offset}')

    def probe_atten(self, ch=1):
        return float(self.q(f':CHAN{ch}:PROB?'))

    def impedance(self, ch=1):
        return self.q(f':CHAN{ch}:IMP?')

    def autorange(self, ch=1, timebase=2e-9, settle=1.5):
        """Centre the trace on its mean and scale to fit the swing (8 divs)."""
        self.w(f':CHAN{ch}:SCAL 0.2')
        self.w(f':CHAN{ch}:OFFS 0')
        self.w(f':TIM:SCAL {timebase}')
        self.w(':RUN')
        time.sleep(settle)
        vavg = float(self.q(f':MEAS:VAV? CHAN{ch}'))
        vpp = float(self.q(f':MEAS:VPP? CHAN{ch}'))
        if vavg > 1e30 or vpp > 1e30:
            return None
        self.w(f':CHAN{ch}:OFFS {vavg}')
        self.w(f':CHAN{ch}:SCAL {max(vpp / 6, 0.002):.4g}')
        time.sleep(settle)
        return vavg, vpp

    def measure(self, ch=1, timebase=2e-9, settle=1.5):
        self.w(f':TIM:SCAL {timebase}')
        self.w(f':TRIG:EDGE:SOUR CHAN{ch}')
        self.w(f':TRIG:EDGE:LEV {self.q(f":CHAN{ch}:OFFS?")}')
        self.w(':TRIG:SWE AUTO')
        self.w(':RUN')
        time.sleep(settle)
        out = {}
        for m in ('FREQ', 'VPP', 'VRMS'):
            v = float(self.q(f':MEAS:{m}? CHAN{ch}'))
            out[m] = None if v > 1e30 else v
        return out

    def trigger_burst(self, ch=1, level=0.002, holdoff=12e-3):
        """Normal-mode edge trigger on an RF burst: the holdoff makes it fire
        on the first carrier cycle after a quiet gap, i.e. a packet start."""
        self.w(f':TRIG:EDGE:SOUR CHAN{ch}')
        self.w(f':TRIG:EDGE:LEV {level}')
        self.w(':TRIG:EDGE:SLOP POS')
        self.w(f':TRIG:HOLD {holdoff}')

    def capture(self, ch=1, duration=1e-6, points=None, triggered=False):
        """Single acquisition of `duration` seconds; returns (t, v, fs).
        triggered=True waits for the configured trigger, with t=0 at the
        left edge of the screen."""
        self.w(':TRIG:SWE ' + ('NORM' if triggered else 'AUTO'))
        self.w(f':TIM:REF {"LEFT" if triggered else "CENT"}')
        self.w(f':TIM:SCAL {duration / 10}')
        self.w(f':DIG CHAN{ch}')
        self.q('*OPC?')
        self.w(f':WAV:SOUR CHAN{ch}')
        self.w(':WAV:FORM WORD')
        self.w(':WAV:BYT LSBF')
        self.w(':WAV:UNS 0')
        self.w(':WAV:POIN:MODE RAW')
        self.w(f':WAV:POIN {points or "MAX"}')
        pre = self.q(':WAV:PRE?').split(',')
        xinc, xorg, xref = float(pre[4]), float(pre[5]), float(pre[6])
        yinc, yorg, yref = float(pre[7]), float(pre[8]), float(pre[9])
        raw = self.s.query_binary_values(':WAV:DATA?', datatype='h',
                                         is_big_endian=False, container=np.array)
        v = (raw.astype(np.float64) - yref) * yinc + yorg
        t = (np.arange(len(v)) - xref) * xinc + xorg
        self.w(':RUN')
        return t, v, 1.0 / xinc

    def close(self):
        self.s.close()
        self.rm.close()
