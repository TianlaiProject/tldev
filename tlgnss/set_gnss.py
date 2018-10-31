import time
import serial

dev = '/dev/ttyUSB0' # serial device.
com = 'com1' # The receiver's port to use.
time_interval = 1 # time interval of data output

ser = serial.Serial(dev, baudrate = 115200)
ser.write('log {0} rangeb ontime {1}\r\n'.format(com, time_interval))
time.sleep(0.6)
ser.write('saveconfig\r\n')
ser.close()

