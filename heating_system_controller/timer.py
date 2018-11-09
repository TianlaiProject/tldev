import os
import time
import sys

try:
    sec = int(sys.argv[1])
except IndexError:
    sec = 3600*3 + 10

while sec > 0:
    #print 'Time left: % 5d seconds.' % sec
    h, s = divmod(sec, 3600)
    m, s = divmod(s, 60)
    sys.stdout.write('\rTime left: %02d h %02d m %02d sec.' % (h,m,s))
    sys.stdout.flush()
    time.sleep(1)
    sec -= 1
print
os.system('python heating_system.py poweroff')
print time.strftime('%Y/%m/%d %H:%M:%S')

