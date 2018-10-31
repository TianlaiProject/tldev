#######################################
# Version 1.0                         #
# Last modified: 2015/12/26           #
# Any problem, contact jxli@bao.ac.cn #
#######################################
import serial
import time
import struct

class serSwitch(object):
    '''Serial switch.'''
    def __init__(self, addr = 0, portnum = 32):
        self.name = '' # Name.
        self.portnum = portnum # number of ports; default 16.
        self.addr = addr # Address: 1,2
        self.cmdsendheader = '\x55'
        self.cmdrecvheader = '\x22'
        self.cmdreadstat   = '\x10'
        self.cmdfuncon     = '\x11'
        self.cmdfuncoff    = '\x12'
        #self.cmdfuncpoff   = '\x13'
        self.cmdfuncalloff = '\x15'
        self.cmd = ''
        self.action = ''
        self.port = 0
        self.bitstat = ''
    def buildCmd(self, cmd_type):
        '''
        Build serial command according to cmd_type.
        '''
        def buildBit(portnum = self.portnum):
            self.bitstat = struct.pack('>I', int('1'*portnum, base=2))
            return self.bitstat
        cmd_type_dict = {
              'on':    self.cmdfuncon,    # Turn on one switch
              'off':   self.cmdfuncoff,   # Turn on one switch
              'look':  self.cmdreadstat,  # Look switch status
              'alloff':self.cmdfuncalloff}#,# Turn off all switches
              #'poff':  self.cmdfuncalloff}# Turn off part of all switches
        if cmd_type == 'alloff':
            cmd_nochk = '%s%s%s%s' % (self.cmdsendheader, struct.pack('B', self.addr), cmd_type_dict[cmd_type], buildBit(self.portnum))
            #cmd_nochk = '%s%s%s\x00\x00\xff\xff' % (self.cmdsendheader, struct.pack('B', self.addr), cmd_type_dict[cmd_type])
#        elif cmd_type.startswith('poff'):
#            cmd_nochk = '%s%s%s\x00\x00\x3f\xff' % (self.cmdsendheader, struct.pack('B', self.addr), cmd_type_dict[cmd_type])
        else:
            cmd_nochk = '%s%s%s\x00\x00\x00%s' % (self.cmdsendheader, struct.pack('B', self.addr), cmd_type_dict[cmd_type], struct.pack('B', self.port))
        self.cmd = '%s%s' % (cmd_nochk, self.calc_chk(cmd_nochk))
        #print 'build cmd =', struct.unpack('8B', self.cmd)
        return self.cmd

    def run(self, action, port=0, output=True):
        '''
        action can be: 'on'/'off'/'look'/'alloff'/'poffN_N'
        port can be 1 to 16(including).
        '''
        ser = serial.Serial('/dev/ttyUSB1')
        self.action = action
        self.port = int(port)
        ser.write(self.buildCmd(action))
        if self.action == 'look':
            curr_stat = self.chk_result(ser)
            if type(curr_stat) is not dict:
                print 'Unknown error occured.'
                exit()
            if output == True:
                print '## Current Status ##'
                print '### Address = %d ###' % self.addr
                for i in xrange(self.portnum):
                    print '  Port %02d: %s' % (i+1, curr_stat[i+1])
                print '####################'
            else: return curr_stat
        elif self.action == 'alloff':
            if self.chk_result(ser): return True
            else:
                if output == True:
                    print '[WARN] Chassis %d can not be powered off!!!' % self.addr
                return False
#        elif self.action.startswith('poff'):
#            if self.chk_result(ser): return True
#            else:
#                if output == True:
#                    print '[WARN] Some switches on chassis %d can not be powered off!!!' % self.addr
#                    return False
        else:
            if self.chk_result(ser):
                if output == True:
                    print 'Apply action "%s" to (Addr=%d, Port=%d) succeed.' % (self.action, self.addr, self.port)
                return True
            else:
                if output == True:
                    print 'Apply action "%s" to (Addr=%d, Port=%d) FAILED!' % (self.action, self.addr, self.port)
                return False

    def calc_chk(self, cmd_nochk):
        '''Calculate check code of "cmd_nochk"'''
        return struct.pack('B', sum(struct.unpack(len(cmd_nochk)*'B', cmd_nochk))%0x100)

    def chk_result(self, ser):
        time.sleep(0.1)
        inwait = ser.inWaiting()
        if inwait == 0:
            print 'First reading failed.'
            time.sleep(0.2)
            inwait = ser.inWaiting()
        retn_data = ser.read(inwait)
        if retn_data == '':
            print 'No reply. This may be caused by:'
            print "=> The requested chassis doesn't exist."
            print "=> The requested chassis is not working."
            print "=> The serial cable of requested chassis is not well connected."
            exit()
        if retn_data[0] != self.cmdrecvheader:
            print 'Header is wrong.'
            return False
        if retn_data[1] != self.cmd[1]:
            print 'Address is wrong.'
            return False
        if retn_data[2] != self.cmd[2]:
            print 'Command is wrong.'
            return False
        if retn_data[7] != self.calc_chk(retn_data[:7]):
            print 'Check code is wrong:'
            print 'Retn =', struct.unpack('8B', retn_data)
            print 'Send =', struct.unpack('8B', self.cmd)
            return False
        if self.action == 'look':
            return self.parse_stat(retn_data[3:7])
        elif self.action == 'alloff':
            if retn_data[3:7] != self.bitstat: 
                print 'Action %s failed.' % self.action
                print 'Retn =', struct.unpack('8B', retn_data)
                return False
            else:
                return True
        else:
            if self.parse_stat(retn_data[3:7], p=self.port) != self.action:
                print self.parse_stat(retn_data[3:7], p=self.port)
                print self.action
                print 'Action %s failed.' % self.action
                print 'Retn =', struct.unpack('8B', retn_data)
                print 'Send =', struct.unpack('8B', self.cmd)
                return False
            return True
    def parse_stat(self, d, p=None):
        '''
        portnum bits string indicating the status of all ports.
        1 for off, 0 for on.
        if p exists, only return p's status, else return portnum status.
        '''
        d = struct.unpack('>I', d)[0]
        if p == None:
            stat = {}
            for i in xrange(self.portnum):
               stat[i+1] = 'on' if (d>>i) % 2 == 0 else 'off'
            return stat
        else:
            return 'on' if (d>>(p-1)) % 2 == 0 else 'off'


if __name__ == '__main__':
    import sys
# Action can be 'on','off','look'
    sersw = serSwitch(addr=int(sys.argv[2]), portnum = 32) # Maximum = 8 ports * 4 boards = 32.
    #sersw.run('alloff')
    sersw.run(sys.argv[1], port = int(sys.argv[3]))
    #sersw.run('on', port = 1)
    #sersw.run('on', port = 6)
    #sersw.run('on', port = 9)
    #sersw.run('on', port = 13)
    #sersw.run('on', port = 18)
    #sersw.run('on', port = 22)
    #sersw.run('on', port = 27)
    #sersw.run('on', port = 30)

#    sersw2 = serSwitch(addr=2, portnum = 32)
#    #sersw.run('alloff')
#    sersw2.run('on', port = 1)
#    sersw2.run('on', port = 2)
#    sersw2.run('on', port = 3)
#    sersw2.run('on', port = 4)
#
