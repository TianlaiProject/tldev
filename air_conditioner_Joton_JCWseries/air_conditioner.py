import struct
import socket
import argparse

class AirConditioner(object):
    def __init__(self):
        self.remoteIP = '192.168.1.49'
        self.remotePort = 10031
        self.cmd_soi = '\x7E' # Start Of Information
        self.cmd_ver = '20'   # Version of Protocol
        self.cmd_adr = '01'   # address of device
        self.cmd_typ = '60'   # type of device
        self.cmd_eoi = '\x0D' # End Of Information
        self.cmd_send = ''

    def _cal_length(self, lenid):
        lchksum = (((~((((lenid & 0xf) + ((lenid >> 4) & 0xf) + ((lenid >> 8) & 0xf)) % 16) & 0xf))&0xf) + 1) & 0xf
        l = hex((lenid & 0xfff) + (lchksum << 12))[2:].upper()
        return '0'*(4-len(l)) + l

    def _cal_chksum(self, s):
       return hex((~(sum(struct.unpack(len(s)*'B', s))% 65535) & 0xffff) + 1)[2:].upper()

    def _build_cmd(self, request):
        if request == 'look':
            self.cmd_send = '%s%s%s%s%s%s' % (self.cmd_soi, self.cmd_ver, self.cmd_adr, self.cmd_typ, 'E0', self._cal_length(0))
            self.cmd_send = '%s%s%s' % (self.cmd_send, self._cal_chksum(self.cmd_send[1:]), self.cmd_eoi)
            return self.cmd_send
        elif request == 'poweron':
            self.cmd_send = '%s%s%s%s%s%s%s' % (self.cmd_soi, self.cmd_ver, self.cmd_adr, self.cmd_typ, '45', self._cal_length(2), '10')
            self.cmd_send = '%s%s%s' % (self.cmd_send, self._cal_chksum(self.cmd_send[1:]), self.cmd_eoi)
            return self.cmd_send
        elif request == 'poweroff':
            self.cmd_send = '%s%s%s%s%s%s%s' % (self.cmd_soi, self.cmd_ver, self.cmd_adr, self.cmd_typ, '45', self._cal_length(2), '1F')
            self.cmd_send = '%s%s%s' % (self.cmd_send, self._cal_chksum(self.cmd_send[1:]), self.cmd_eoi)
            return self.cmd_send
        else:
            print 'Error: Unknown request.'
            return

    def send(self, cmd_send):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.remoteIP, self.remotePort))
        self.sock.send(cmd_send)

    def recv(self):
        rtn = self.sock.recv(1000)
        return rtn

    def show_status(self, rtn_str):
        '''Now only show temperature, humidity, working_or_not.'''
        if rtn_str.startswith('%s%s%s%s' % (self.cmd_soi, self.cmd_ver, self.cmd_adr, self.cmd_typ)):
            room_temperature = int(rtn_str[13:17], base = 16) / 10.
            room_humidity = int(rtn_str[17:21], base = 16) / 10.
            power_status = 'poweron' if rtn_str[21:23] == '01' else 'poweroff'
            temperature_uplim = int(rtn_str[35:39], base = 16)
            temperature_lolim = int(rtn_str[39:43], base = 16)
            humidity_uplim = int(rtn_str[43:47], base = 16)
            humidity_lolim = int(rtn_str[47:51], base = 16)
            humidity_setting = int(rtn_str[51:55], base = 16)
            temperature_setting = int(rtn_str[59:63], base = 16) / 10.
            working_hours = int(rtn_str[67:71], base = 16)
            print '#' * 35
            print 'room_temperature    : %.1f Celcius' % room_temperature
            print 'room_humidity       : %.1f %%' % room_humidity
            print 'power_status        : %s' % power_status
            print 'temperature_setting : %.1f Celcius'% temperature_setting
            print 'temperature_upperlim: %d Celcius' % temperature_uplim
            print 'temperature_lowerlim: %d Celcius' % temperature_lolim
            print 'humidity_setting    : %d %%' % humidity_setting
            print 'humidity_upperlim   : %d %%' % humidity_uplim
            print 'humidity_lowerlim   : %d %%' % humidity_lolim
            print 'working_hours       : %d Hours' % working_hours
            print '#' * 35
        else:
            print 'Error'

    def run(self, request):
        '''request can be "look", "poweron", "poweroff".'''
        self.send(self._build_cmd(request))
        if request == 'look':
            self.show_status(self.recv())
        if request == 'poweron':
            rtn = self.recv()
            if rtn.startswith('%s%s%s%s%s' % (self.cmd_soi, self.cmd_ver, self.cmd_adr, self.cmd_typ, '00')):
                print 'Successfully powered on.'
        if request == 'poweroff':
            rtn = self.recv()
            if rtn.startswith('%s%s%s%s%s' % (self.cmd_soi, self.cmd_ver, self.cmd_adr, self.cmd_typ, '00')):
                print 'Successfully powered off.'
    def getData(self):
        self.send(self._build_cmd('look'))
        rtn_str = self.recv()
        if rtn_str.startswith('%s%s%s%s' % (self.cmd_soi, self.cmd_ver, self.cmd_adr, self.cmd_typ)):
            data = {}
            data['room_temperature'] = int(rtn_str[13:17], base = 16) / 10.
            data['room_humidity'] = int(rtn_str[17:21], base = 16) / 10.
            data['power_status'] = 'poweron' if rtn_str[21:23] == '01' else 'poweroff'
            data['temperature_uplim'] = int(rtn_str[35:39], base = 16)
            data['temperature_lolim'] = int(rtn_str[39:43], base = 16)
            data['humidity_uplim'] = int(rtn_str[43:47], base = 16)
            data['humidity_lolim'] = int(rtn_str[47:51], base = 16)
            data['humidity_setting'] = int(rtn_str[51:55], base = 16)
            data['temperature_setting'] = int(rtn_str[59:63], base = 16) / 10.
            data['working_hours'] = int(rtn_str[67:71], base = 16)
            return data
        else:
            return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Controller for Air Conditioner in Analog Room')
    parser.add_argument('-o', '--on', action='store_true', help='power on air-conditioner')
    parser.add_argument('-f', '--off', action='store_true', help='power off air-conditioner')
    parser.add_argument('-l', '--look', action='store_true', help='look current status of air-conditioner')

    ac = AirConditioner()
    options = parser.parse_args()
    if options.on == True:
        ac.run('poweron')
        exit()
    if options.off == True:
        ac.run('poweroff')
        exit()
    if options.look == True:
        ac.run('look')
        exit()
    print parser.print_help()
