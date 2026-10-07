# asic-radio bench: start transmitting at power-up.
# MODE 'on' = steady carrier, 'uart' = repeated OOK packet (ringkey.PACKET).
# Delete this file from the board to boot normally. Writes /autorun.log.
import time
MODE, RATE = 'on', 0
with open('/autorun.log', 'w') as fh:
    fh.write('autorun start %d %s %d\n' % (time.ticks_ms(), MODE, RATE))
    fh.flush()
try:
    import ringkey
    ringkey.main(MODE, RATE)          # 'uart' loops forever
except Exception as e:
    import sys
    with open('/autorun.log', 'a') as fh:
        sys.print_exception(e, fh)
