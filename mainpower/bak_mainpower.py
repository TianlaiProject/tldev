#!/usr/bin/env  python 
############################################
# Applies to 4 port sock.al switch JY-DAM0400 #
# Version 0.0                                #
# Last modified 2016.7.3                     #
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
    '''Strangely, the sock.al switch automatically sends out 1Byte "\xfe".
        One has to remove the residual "\xfe" before to use.
    '''
    if s[:2] == '\xfe\xfe':
        return rm_fe(s[1:])
    else: return s

if __name__ == '__main__':
# Usage:
# python mainpower.py commands
# Commands can be one of below:
# 32op, dish, 192op, hill, look

    remoteIP = '192.168.1.49'
    remotePort = 10028
    localIP = '192.168.1.22'
    localPort = 4028
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((remoteIP, remotePort))
    
    try:
        opt_input = sys.argv[1]
    except IndexError:
        sock.close()
        print '[Usage:]'
        print '    python mainpower.py options commands'
        print 'Options can be one of below:'
        print '    32op, dish, 192op, hill'
        print 'Commands can be one of below:'
        print '    on, off, look  (Note: When use look, keep options blank.)'
        print 'Example:'
        print '    python mainpower.py look'
        print '    python mainpower.py 32op on'
        exit()
    if opt_input != 'look':
        try:
            cmd_input = sys.argv[2]
        except IndexError:
            sock.close()
            print '[Usage:]'
            print '    python mainpower.py options commands'
            print 'Options can be one of below:'
            print '    32op, dish, 192op, hill'
            print 'Commands can be one of below:'
            print '    on, off, look  (Note: When use look, keep options blank.)'
            print 'Example:'
            print '    python mainpower.py look'
            print '    python mainpower.py 32op on'
            exit()
    else:
        cmd_input = 'look'

    if cmd_input == 'on':
        if opt_input == '32op':
            sock.send(cmds['1off'])
        #time.sleep(0.2)
            if rm_fe(sock.recv(1000)) != cmds['1off']:
                print 'Error: Turn on 32 optic sender failed. You must try again before to use.'
                sock.close()
                exit()
            else:
                print '32 optic sender has been turned on.'
                exit()
        elif opt_input == 'dish':
            sock.send(cmds['2on'])
        #time.sleep(0.2)
            if rm_fe(sock.recv(1000)) != cmds['2on']:
                print 'Error: Turn on dishes failed. You must try again before to use.'
                sock.close()
                exit()
            else:
                print 'Dishes have been turned on.'
                exit()
        elif opt_input == '192op':
            sock.send(cmds['3off'])
        #time.sleep(0.2)
            if rm_fe(sock.recv(1000)) != cmds['3off']:
                print 'Error: Turn on 192 optic sender failed. You must try again before to use.'
                sock.close()
                exit()
            else:
                print '192 optic sender has been turned on.'
                exit()
        elif opt_input == 'hill':
            sock.send(cmds['4off'])
            if rm_fe(sock.recv(1000)) != cmds['4off']:
                print 'Error: Turn on hill power failed. You must try again before to use.'
                sock.close()
                exit()
            else:
                print 'Hill power has been turned on.'
                exit()
        else:
            print 'Unknown command!!!'
            exit()
    elif cmd_input == 'off':
        if opt_input == '32op':
            sock.send(cmds['1on'])
        #time.sleep(0.2)
            if rm_fe(sock.recv(1000)) != cmds['1on']:
                print 'Error: Turn off 32 optic sender failed. You must try again before to use.'
                sock.close()
                exit()
            else:
                print '32 optic sender has been turned off.'
                exit()
        elif opt_input == 'dish':
            sock.send(cmds['2off'])
        #time.sleep(0.2)
            if rm_fe(sock.recv(1000)) != cmds['2off']:
                print 'Error: Turn off dishes failed. You must try again before to use.'
                sock.close()
                exit()
            else:
                print 'Dishes have been turned off.'
                exit()
        elif opt_input == '192op':
            sock.send(cmds['3on'])
        #time.sleep(0.2)
            if rm_fe(sock.recv(1000)) != cmds['3on']:
                print 'Error: Turn off 192 optic sender failed. You must try again before to use.'
                sock.close()
                exit()
            else:
                print '192 optic sender has been turned off. (~13 seconds delay)'
                exit()
        elif opt_input == 'hill':
            sock.send(cmds['4on'])
            if rm_fe(sock.recv(1000)) != cmds['4on']:
                print 'Error: Turn off hill power failed. You must try again before to use.'
                sock.close()
                exit()
            else:
                print 'Hill power has been turned off.'
                exit()
        else:
            print 'Unknown command!!!'
            exit()
    elif cmd_input == 'look':
        sock.send(cmds['look'])
        time.sleep(0.2)
        lookr = rm_fe(sock.recv(1000))
        if lookr.startswith('\xfe\x01\x01'):
            curr_stat = parse_stat(struct.unpack('B', lookr[3:4])[0])
            print 'Current power status is:'
            print '32op : %s' % ('on' if curr_stat[1] == 'off' else 'off')
            print 'dish :', curr_stat[2]
            print '192op: %s' % ('on' if curr_stat[3] == 'off' else 'off')
            print 'hill : %s' % ('on' if curr_stat[4] == 'off' else 'off')
            exit()
        else:
            print struct.unpack('B'*len(lookr), lookr)
            print 'Error. Please try again.'
            exit()
        sock.close()
    else:
        print 'Error: The command "%s" is unknown.' % cmd_input
        print '       Use "on, off, look" instead.'
        

