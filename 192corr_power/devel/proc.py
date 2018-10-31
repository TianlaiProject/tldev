import time
import sys

print
for i in xrange(60):
    perc = 10*i/6
    proc = int(40.*i/60)
    sys.stdout.write('\r[%s%s]%d%%' % ('#'*proc, ' '*(40-proc), perc))
    sys.stdout.flush()
    time.sleep(0.05)
print
sys.stdout.write('11111111111111111 PROCESS 111111111111111111111111111111111111\r')
sys.stdout.write('start one.\n')

