############################################
# Applies to 4 port serial switch JY-DAM0400 #
# Version 0.0                                #
# Last modified 2016.3.14                    #
# Contact: jxli@bao.ac.cn                    #
##############################################

import socket
import sys
import time
import struct

cmds = {'look': '\xfe\x01\x00\x00\x00\x04\x29\xc6',
        'lookr':'\xfe\x01\x01\x00\x61\x9c',
        '1on':  '\xfe\x05\x00\x00\xff\x00\x98\x35',
        '1off': '\xfe\x05\x00\x00\x00\x00\xd9\xc5',
        '2on':  '\xfe\x05\x00\x01\xff\x00\xc9\xf5',
        '2off': '\xfe\x05\x00\x01\x00\x00\x88\x05',
        '3on':  '\xfe\x05\x00\x02\xff\x00\x39\xf5',
        '3off': '\xfe\x05\x00\x02\x00\x00\x78\x05',
        '4on':  '\xfe\x05\x00\x03\xff\x00\x68\x35',
        '4off': '\xfe\x05\x00\x03\x00\x00\x29\xc5'}
 
def parse_stat(s):
    ''' One byte string. Each bit is a status for one port.'''
    stat = {}
    for i in xrange(4):
        if s % 2 == 1:
            stat[i+1] = 'on'
        else:
            stat[i+1] = 'off'
        s = s >> 1
    return stat

def rm_fe(s):
    '''Strangely, the serial switch automatically sends out 1Byte "\xfe".
        One has to remove the residual "\xfe" before to use.
    '''
    if s[:2] == '\xfe\xfe':
        return rm_fe(s[1:])
    else: return s

if __name__ == '__main__':
# Usage:
# python noise_source.py commands
# Commands can be one of below:
# 32, 192, look

    remoteIP = '192.168.1.49'
    remotePort = 10030
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((remoteIP, remotePort))
    
    try:
        cmd_input = sys.argv[1]
    except IndexError:
        print 'Usage:'
        print 'python noise_source.py commands'
        print 'Commands can be one of below:'
        print '32, 192, look'
        exit()

    if cmd_input == '32':
        sock.send(cmds['1on'])
        #time.sleep(0.2)
        if rm_fe(sock.recv(1000)) != cmds['1on']:
            print 'Error: Switch to 32 failed. You must try again before to use.'
            ser.close()
            exit()
        else:
            print 'Noise source TTL driver has been turned to 32chn correlator.'
            exit()
    elif cmd_input == '192':
        sock.send(cmds['1off'])
        time.sleep(0.2)
        if rm_fe(sock.recv(1000)) != cmds['1off']:
            print 'Error: Switch to 192 failed. You must try again before to use.'
            ser.close()
            exit()
        else:
            print 'Noise source TTL driver has been turned to 192chn correlator.'
            exit()
    elif cmd_input == 'look':
        sock.send(cmds['look'])
        time.sleep(0.2)
        lookr = rm_fe(sock.recv(1000))
        if lookr.startswith('\xfe\x01\x01'):
            curr_stat = parse_stat(struct.unpack('B', lookr[3:4])[0])
            print 'Current TTL driver is',
            print '%d' % (32 if curr_stat[1] == 'on' else 192),
            print 'correlator.'
            exit()
        else:
            print struct.unpack('B'*len(lookr), lookr)
            print 'Error. Please try again.'
            exit()
        ser.close()
    else:
        print 'Error: The command "%s" is unknown.' % cmd_input
        print '       Use "32, 192, look" instead.'
        

