########################################
# Version 1.0                          #
# Any problems, contact jxli@bao.ac.cn #
# Last modified: 2015/11/30            #
########################################

import socket
import time

class WeatherStation(object):
    '''TianLai site weather station.'''
    def __init__(self, localIP, localPort=5555):
        '''Initialize with localIP.'''
        self.remoteIP = '192.168.1.109'
        self.remotePort = 5555
        self.localIP = localIP
        self.localPort = localPort
        self.cmd = ''
        self.header = '#'   # Command header
        self.devno = '9FCF' # Device numbe:40911
        self.cmd_getdata = '030C' # command of get data
        self.cmd_settime = '010A' # command of set time
        self.cmd_setdevno= '140O' # command of set device No.
        self.cmd_chkmem  = '020B' # command of check records in device memory
        self.settailer = 'G'  # Command tailer for set
        self.gettailer = 'GG' # Command tailer for get
        self.returnData = ''

    def unpackData(self, data):
        '''Unpack returned hex string to decimal.'''
        data = int('%s%s' % ('0x', data), base=16)
        return (0x8000 - data) if data>32767 else data

    def parseData(self, data):
        '''Parse returned data into weather data dictionary.'''
        if data[0] != self.header or data[-2:] != self.gettailer:
            print 'Invalid weather data.'
            return
        if data[1:5] != self.devno.lower():
            print 'Weather data from unknown device.'
        if data[5:9] == self.cmd_getdata:
        # Information is:
        # 5116160414 Time:MMHHddmmyy
        # 00000000   Total radiation 1
        # 00000000   Total radiation 2
        # 80008000800080008000 Temperature 1,2,3,4,5
        # 0106       Temperature
        # 022d       Humidity
        # 0681       Dew point
        # 24f5       Pressure
        # 024b       Height
        # 0000       Current wind speed
        # 0000       Wind speed in 2 minute average
        # 0000       Wind speed in 10minute average
        # 0008       Wind direction
        # 0000       Current radiation 1
        # 0000       Current radiation 2
        # 0000       Precipitation
        # 000000     Evaporation
        # 0086       Power capacity
        # 00         Sunshine hours
            weather_data = {}
            weather_data['devtime'] = time.strftime('%Y/%m/%d_%H:%M', time.strptime(data[9:19], '%M%H%d%m%y'))
            #weather_data['radia1_total'] = data[19:27]
            #weather_data['radia2_total'] = data[27:35]
            #weather_data['temperature_1to5'] = data[35:55]
            weather_data['temperature'] = self.unpackData(data[55:59]) / 10.
            weather_data['humidity'] = int(data[59:63], base=16) / 10.
            weather_data['dew_point'] = self.unpackData(data[63:67]) / 100.
            weather_data['pressure'] = int(data[67:71], base=16) / 10.
            #weather_data['height'] = int(data[71:75], base=16) / 10.
            weather_data['windspeed_current'] = int(data[75:79], base=16) / 10.
            weather_data['windspeed_2minaverage'] = int(data[79:83], base=16) / 10.
            weather_data['windspeed_10minaverage'] = int(data[83:87], base=16) / 10.
            weather_data['wind_direction'] = int(data[87:91], base=16)
            #weather_data['radia1_current'] = data[91:95]
            #weather_data['radia2_current'] = data[95:99]
            weather_data['precipitation'] = int(data[99:103], base=16) / 10.
            #weather_data['evaporation'] = int(data[103:109], base=16) / 10.
            #weather_data['power_capacity'] = int(data[109:113], base=16)
            #weather_data['sunshine_hours'] = int(data[113:115], base=16) / 10.
            return weather_data
        else:
            return

    def buildCmd(self, cmdname):
        'Build command according to definition.'''
        if cmdname == 'getdata':
            self.cmd = '%s%s%s%s' % (self.header, self.devno, self.cmd_getdata, self.settailer)
            return self.cmd
        elif cmdname == 'settime':
            curr_time = time.strftime('%S%M%H%d%m%02w%y')
            self.cmd = '%s%s%s%s%s' % (self.header, self.devno, self.cmd_settime, curr_time, self.settailer)
            return self.cmd
        elif cmdname == 'chkmem':
            self.cmd = '%s%s%s%s' % (self.header, self.devno, self.cmd_chkmem, self.settailer)
            return self.cmd

    def getData(self):
        '''Get weather data from weather station.'''
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.remoteIP, self.remotePort))
        self.cmd = self.buildCmd('getdata')
        sock.send(self.cmd)
        for i in xrange(5):
            self.returnData  = sock.recv(1000)
            if len(self.returnData) != 117:
                sent = sock.send(self.cmd)
                if sent == 0:
                    print 'Cannot send out data.'
                    break
            else: break
        return self.parseData(self.returnData)

    def setDevTime(self):
        '''Set date and time for weather station.'''
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.remoteIP, self.remotePort))
        self.cmd = self.buildCmd('settime')
        sock.send(self.cmd)
        for i in xrange(5):
            self.returnData  = sock.recv(1000)
            if len(self.returnData) != 11:
                sent = sock.send(self.cmd)
                if sent == 0:
                    print 'Cannot send out data.'
                    break
            else:
                print 'Time has been successfully set.'
                break
        return

    def chkDevMem(self):
        '''Check data records in weather station memory.'''
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.remoteIP, self.remotePort))
        self.cmd = self.buildCmd('chkmem')
        sock.send(self.cmd)
        for i in xrange(5):
            self.returnData  = sock.recv(1000)
            if len(self.returnData) != 29:
                sent = sock.send(self.cmd)
                if sent == 0:
                    print 'Cannot send out data.'
                    break
            else:
                try:
                    print time.strftime('%Y/%m/%d %H:%M:%S', time.strptime(self.returnData[13:27], '%S%M%H%d%m0%w%y'))
                except:
                    try:
                        print time.strftime('%Y/%m/%d %H:%M:%S', time.strptime(self.returnData[13:27], '%S%M%H%d%m07%y'))
                    except:
                        raise
                    break
        return

if __name__ == '__main__':
    localIP = '192.168.1.22'
    ws = WeatherStation(localIP)

### Get weather data, return a dict
    w_d = ws.getData()
#    ##print w_d['temperature']
#    ##print w_d['windspeed_current']
#    ##print w_d['wind_direction']
    for k,v in w_d.iteritems():
        print k,'\t',v
### Set weather station time
#    ws.setDevTime()
    #time.sleep(1)
### Check data records in weather station
    #print '-------'
    #ws.chkDevMem()

