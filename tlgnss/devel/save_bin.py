import serial

ser = serial.Serial('/dev/ttyUSB0', baudrate=115200)

f = open('linux_gps.bin', 'wb')

try:
    while 1:
        print 'Got'
        f.write(ser.read(200))
except KeyboardInterrupt:
    f.close()

