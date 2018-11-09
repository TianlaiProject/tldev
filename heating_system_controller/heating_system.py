##############################################
# Applies to 4 port serial switch JY-DAM0400 #
# Version 0.0                                #
# Last modified 2016.1.13                    #
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
# python heating_system.py commands
# Commands can be one of below:
# poweron, poweroff, run, stop, look

    remoteIP = '192.168.1.49'
    remotePort = 10032
    localIP = '192.168.1.22'
    localPort = 4032
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((remoteIP, remotePort))
    
    try:
        cmd_input = sys.argv[1]
    except IndexError:
        print 'Usage:'
        print 'python heating_system.py commands'
        print 'Commands can be one of below:'
        print 'poweron, poweroff, look'
        #print 'poweron, poweroff, run, stop, look'
        exit()

    if cmd_input == 'poweron':
        sock.send(cmds['1on'])
        if rm_fe(sock.recv(1000)) != cmds['1on']:
            print 'Error: Power on failed. You must try again before to use.'
            sock.close()
            exit()
        time.sleep(0.2)
        sock.send(cmds['1off'])
        for i in xrange(5):
            if rm_fe(sock.recv(1000)) != cmds['1off']:
                if i == 4:
                    print 'WARN: Cannot turn off switch 1!!! This may be dangerous. Please contact jxli@bao.ac.cn as soon as possible!!!'
                    sock.close()
                    exit()
                sock.send(cmds['1off'])
            else:
                print 'Heating system has been powered on.'
                #print 'Heating system has been powered on. \n(Note: The system is still not running. Please use "run" command.)'
                exit()
    elif cmd_input == 'poweroff':
        sock.send(cmds['3on'])
        if rm_fe(sock.recv(1000)) != cmds['3on']:
            print 'WARN: Cannot power off heating system!!! This is very dangerous!!!\n     If this is the first time you see this, please wait 20 seconds and run again.\n     Otherwise, please contact jxli@bao.ac.cn(Li Jixia) as soon as possible!!!'
            sock.close()
            exit()
        time.sleep(0.2)
        sock.send(cmds['3off'])
        for i in xrange(5):
            if rm_fe(sock.recv(1000)) != cmds['3off']:
                if i == 4:
                    print 'WARN: Cannot turn off switch 3!!! This may be dangerous. \n     If this is the first time you see this, please wait 20 seconds and run again.\n     Otherwise, Please contact jxli@bao.ac.cn (Li Jixia) as soon as possible.'
                    sock.close()
                    exit()
                sock.send(cmds['3off'])
            else:
                print 'Heating system has been powered off.'
                exit()
    elif cmd_input == 'run':
        print 'Command not supported.'
        exit()
        sock.send(cmds['2on'])
        if rm_fe(sock.recv(1000)) != cmds['2on']:
            print 'Error: Heating system failed to run. Please try again.'
            sock.close()
            exit()
        else:
            print 'Note: Heating system is running. You should stop it some time later by "stop" command.'
            sock.close()
            exit()
    elif cmd_input == 'stop':
        print 'Command not supported.'
        exit()
        sock.send(cmds['2off'])
        if rm_fe(sock.recv(1000)) != cmds['2off']:
            print 'WARN: Cannot stop the heating system!!! This is very dangerous!!!\n If this is the first time you see this, please run again or use "poweroff" command.\n     Otherwise, please contact jxli@bao.ac.cn(Li Jixia) as soon as possible!!!'
            sock.close()
            exit()
        else:
            print 'Heating system has stopped working.'
            sock.close()
            exit()
    elif cmd_input == 'look':
        sock.send(cmds['look'])
        lookr = rm_fe(sock.recv(1000))
        if lookr.startswith('\xfe\x01\x01'):
            curr_stat = parse_stat(struct.unpack('B', lookr[3:4])[0])
            print 'Current status:'
            print '   ',curr_stat
            print 'Normal status should be:'
            print '    switch-1,3,4: "off"'
            print '    switch-2:     "on"(when running), "off"(when stopped)'
            exit()
        else:
            print 'Error. Please try again.'
            exit()
        sock.close()
    else:
        print 'Error: The command "%s" is unknown.' % cmd_input
        print '       Use "poweron, poweroff, run, stop, look" instead.'
        

