"""
Bit-exact model of the radio's code-mode digital, structured like the RTL,
plus a behavioural model of the analog receive chain to close the loop.

Timing (10 MHz clock):
  chip   = CHIP_CLKS   = 1040 clocks  (9615 chip/s)
  sample = SAMPLE_CLKS = 130 clocks   (8 samples per chip)
TX code mode: on a send request, BURSTS bursts of 127 chips, each followed
by GAP chips of silence (burst period PERIOD = 127 + GAP chips).

RX digital, per comparator sample c (0/1):
  trim servo  : trim = clamp(trim + (c ? +1 : -1), 0, 255)   -> R2R fine-trim DAC
  chip slicer : 4 phases (sample offsets 0,2,4,6); each phase counts c over
                8 samples; chip bit = count > 4, or (count == 4 and last c)
  register    : per phase, 127-bit shift register; reg bit 0 = newest chip
  correlator  : after each shift, score = #matches between reg[126-j] and
                code chip j (j = 0..126), computed with the LFSR pair
  events      : score >= THRESH starts an event; further detections within
                DEDUP chips belong to the same event; the event time is the
                chip count of its first detection and its score the maximum
  pairing     : an event PERIOD or 2*PERIOD (+/- TOL chips) after one of the
                two previous events confirms a send -> toggle LED, then ignore
                events for HOLDOFF chips
"""
import numpy as np

from gold import gold, lfsr, TAPS1, TAPS2, SEED, LEN

CLK = 10_000_000
CHIP_CLKS = 1040
SAMPLE_CLKS = 130
S = CHIP_CLKS // SAMPLE_CLKS          # 8
PHASES = (0, 2, 4, 6)
BURSTS = 3
GAP = 64
PERIOD = LEN + GAP                    # 191 chips
THRESH = 97                           # z = 6 over 127 chips
DEDUP = 8                             # chips
TOL = 2                               # chips
HOLDOFF = 9615                        # chips (~1 s)


# ------------------------------------------------------------------ TX
def tx_chips(code, bursts=BURSTS, gap=GAP):
    """Chip stream (1 = carrier on) for one code-mode send."""
    g = gold(code)
    one = np.concatenate([g, np.zeros(gap, np.uint8)])
    return np.tile(one, bursts)


def lfsr2_start_state(code):
    """State of LFSR2 after `code` steps from SEED (what the RTL precomputes)."""
    _, states = lfsr(TAPS2, SEED, n=LEN + 1)
    return states[code % LEN]


# ------------------------------------------------------------------ RX digital
class RxDigital:
    def __init__(self, code):
        self.code = code
        self.template = gold(code)            # what the LFSR pair produces, chip j = 0..126
        self.trim = 128
        self.counts = {p: 0 for p in PHASES}
        self.regs = {p: np.zeros(LEN, np.uint8) for p in PHASES}   # [0] = newest
        self.n = 0                             # sample counter
        self.chip_ctr = 0                      # chips since start (for event timing)
        self.ev_open = None                    # (time, score) of the event being built
        self.ev_close_at = None
        self.events = []                       # finished events (time, score)
        self.recent = []                       # last two event times for pairing
        self.holdoff_until = -1
        self.led = 0
        self.toggles = []                      # chip times of LED toggles
        self.last_score = 0

    def step(self, c):
        """One comparator sample. Returns the trim DAC code for the next sample."""
        c = int(c)
        self.trim = min(255, self.trim + 1) if c else max(0, self.trim - 1)
        k = self.n % S
        if k == 0:
            self.chip_ctr += 1
        for p in PHASES:
            pos = (k - p) % S                 # position of this sample in phase p's window
            self.counts[p] += c
            if pos == S - 1:                  # window complete
                cnt = self.counts[p]
                bit = 1 if (cnt > S // 2 or (cnt == S // 2 and c)) else 0
                self.counts[p] = 0
                self._shift(p, bit)
        self.n += 1
        self._close_event()
        return self.trim

    def _shift(self, p, bit):
        r = self.regs[p]
        r[1:] = r[:-1].copy()
        r[0] = bit
        # reg[126 - j] is chip j of a burst that has fully arrived
        score = int(np.sum(r[::-1] == self.template))
        self.last_score = max(self.last_score, score) if self.ev_open else score
        if score >= THRESH:
            t = self.chip_ctr
            if self.ev_open is None:
                self.ev_open = [t, score]
                self.ev_close_at = t + DEDUP
            else:
                self.ev_open[1] = max(self.ev_open[1], score)

    def _close_event(self):
        if self.ev_open is not None and self.chip_ctr >= self.ev_close_at:
            t, sc = self.ev_open
            self.ev_open = None
            self.events.append((t, sc))
            if t >= self.holdoff_until:
                for prev in self.recent:
                    d = t - prev
                    if abs(d - PERIOD) <= TOL or abs(d - 2 * PERIOD) <= TOL:
                        self.led ^= 1
                        self.toggles.append(t)
                        self.holdoff_until = t + HOLDOFF
                        self.recent = []
                        return
                self.recent = (self.recent + [t])[-2:]


# ------------------------------------------------------------------ analog behaviour
class AfeModel:
    """Behavioural receive chain after the log detector + LPF:
    comparator(+) = v (detector, in 0.44 dB 'LSB' units)
    comparator(-) = switched-cap average of v + offset + trim_gain*(trim-128)"""
    def __init__(self, tau=0.5e-3, offset_db=0.125, trim_lsb_db=0.005, lsb_db=0.44):
        fs = CLK / SAMPLE_CLKS
        self.a = 1.0 / (tau * fs)
        self.off = offset_db / lsb_db
        self.tg = trim_lsb_db / lsb_db
        self.avg = None

    def compare(self, v, trim):
        if self.avg is None:
            self.avg = v
        self.avg += self.a * (v - self.avg)
        return 1 if v > self.avg + self.off + self.tg * (trim - 128) else 0


def run_rx(v_samples, code, afe=None):
    """Closed loop: analog model + bit-exact digital. Returns (rx, comp bits, trims)."""
    afe = afe or AfeModel()
    rx = RxDigital(code)
    trim = rx.trim
    comps = np.empty(len(v_samples), np.uint8)
    trims = np.empty(len(v_samples), np.uint8)
    for i, v in enumerate(v_samples):
        c = afe.compare(v, trim)
        comps[i] = c
        trim = rx.step(c)
        trims[i] = trim
    return rx, comps, trims


if __name__ == '__main__':
    # noiseless sanity: ideal comparator bits straight from the chip stream
    code = 0x5A
    chips = np.concatenate([np.zeros(50, np.uint8), tx_chips(code), np.zeros(300, np.uint8)])
    comp = np.repeat(chips, S)
    rx = RxDigital(code)
    for c in comp:
        rx.step(c)
    print('events (chip time, score):', rx.events)
    print('LED toggles at chips:', rx.toggles, ' LED =', rx.led)
    wrong = RxDigital(0x11)
    for c in comp:
        wrong.step(c)
    print('wrong-code RX events:', wrong.events, ' toggles:', wrong.toggles)
    print('LFSR2 start state for code 0x5A:', format(lfsr2_start_state(code), '07b'))
