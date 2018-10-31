##############################################
# Applies to 4 port serial switch JY-DAM0400 #
# Version 1.1                                #
# Last modified 2017.7.31                    #
# Contact: jxli@bao.ac.cn                    #
##############################################

import socket
import sys
import time
import struct
import argparse

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
    # Switch ports allocation.
    #ports = {'192': 1, '32': 2, 'on': 3, 'off': 3} # ports allocation
    #default_status={'192': 'off', '32': 'off', 'on': 'off', 'off': 'on'} # default status of the ports.

    # Serial server.
    remoteIP = '192.168.1.49'
    remotePort = 10030

    parser = argparse.ArgumentParser(description="set noise source driver")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-l", "--look", action="store_true", help="look current noise source driver")
    group.add_argument("-s", "--source", choices=["192", "32", "on", "off"], help="set to one of these source drivers: on for ALWAYS ON; off for ALWAYS OFF.")
    args = parser.parse_args()

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((remoteIP, remotePort))
    except:
        print "Network Error."
        raise
        
    if args.source == '192':
        cmd_transfer = '3off' #TODO ???
        sock.send(cmds[cmd_transfer])
        time.sleep(0.2)
        if rm_fe(sock.recv(1000)) != cmds[cmd_transfer]:
            print 'Error: turn to ALWAYS OFF failed. You must try again before to use.'
            ser.close()
            exit()
        else:
            print 'Turn to ALWAYS OFF succeeded.'
            #exit()
        time.sleep(0.2)
        cmd_transfer = '2off'
        sock.send(cmds[cmd_transfer])
        time.sleep(0.2)
        if rm_fe(sock.recv(1000)) != cmds[cmd_transfer]:
            print 'Error: turn off 32 failed. You must try again before to use.'
            ser.close()
            exit()
        else:
            print 'Turn off 32 succeeded.'
        time.sleep(0.2)
        cmd_transfer = '1on'
        sock.send(cmds[cmd_transfer])
        time.sleep(0.2)
        if rm_fe(sock.recv(1000)) != cmds[cmd_transfer]:
            print 'Error: turn on 192 failed. You must try again before to use.'
            ser.close()
            exit()
        else:
            print 'Turn on 192 succeeded.'
            exit()
    elif args.source == '32':
        cmd_transfer = '3off'
        sock.send(cmds[cmd_transfer])
        time.sleep(0.2)
        if rm_fe(sock.recv(1000)) != cmds[cmd_transfer]:
            print 'Error: turn to ALWAYS OFF failed. You must try again before to use.'
            ser.close()
            exit()
        else:
            print 'Turn to ALWAYS OFF succeeded.'
        time.sleep(0.2)
        cmd_transfer = '1off'
        sock.send(cmds[cmd_transfer])
        time.sleep(0.2)
        if rm_fe(sock.recv(1000)) != cmds[cmd_transfer]:
            print 'Error: turn off 192 failed. You must try again before to use.'
            ser.close()
            exit()
        else:
            print 'Turn off 192 succeeded.'
        time.sleep(0.2)
        cmd_transfer = '2on'
        sock.send(cmds[cmd_transfer])
        time.sleep(0.2)
        if rm_fe(sock.recv(1000)) != cmds[cmd_transfer]:
            print 'Error: turn on 32 failed. You must try again before to use.'
            ser.close()
            exit()
        else:
            print 'Turn on 32 succeeded.'
            exit()
    elif args.source == 'on':
        cmd_transfer = '1off'
        sock.send(cmds[cmd_transfer])
        time.sleep(0.2)
        if rm_fe(sock.recv(1000)) != cmds[cmd_transfer]:
            print 'Error: turn off 192 failed. You must try again before to use.'
            ser.close()
            exit()
        else:
            print 'Turn off 192 succeeded.'
        time.sleep(0.2)
        cmd_transfer = '2off'
        sock.send(cmds[cmd_transfer])
        time.sleep(0.2)
        if rm_fe(sock.recv(1000)) != cmds[cmd_transfer]:
            print 'Error: turn off 32 failed. You must try again before to use.'
            ser.close()
            exit()
        else:
            print 'Turn off 32 succeeded.'
        time.sleep(0.2)
        cmd_transfer = '3on'
        sock.send(cmds[cmd_transfer])
        time.sleep(0.2)
        if rm_fe(sock.recv(1000)) != cmds[cmd_transfer]:
            print 'Error: turn on ALWAYS ON failed. You must try again before to use.'
            ser.close()
            exit()
        else:
            print 'Turn to ALWAYS ON succeeded.'
            exit()
    elif args.source == 'off':
        cmd_transfer = '1off'
        sock.send(cmds[cmd_transfer])
        time.sleep(0.2)
        if rm_fe(sock.recv(1000)) != cmds[cmd_transfer]:
            print 'Error: turn off 192 failed. You must try again before to use.'
            ser.close()
            exit()
        else:
            print 'Turn off 192 succeeded.'
        time.sleep(0.2)
        cmd_transfer = '2off'
        sock.send(cmds[cmd_transfer])
        time.sleep(0.2)
        if rm_fe(sock.recv(1000)) != cmds[cmd_transfer]:
            print 'Error: turn off 32 failed. You must try again before to use.'
            ser.close()
            exit()
        else:
            print 'Turn off 32 succeeded.'
        time.sleep(0.2)
        cmd_transfer = '3off'
        sock.send(cmds[cmd_transfer])
        time.sleep(0.2)
        if rm_fe(sock.recv(1000)) != cmds[cmd_transfer]:
            print 'Error: turn to ALWAYS OFF failed. You must try again before to use.'
            ser.close()
            exit()
        else:
            print 'Turn to ALWAYS OFF succeeded.'
            exit()
    elif args.look == True:
        sock.send(cmds['look'])
        time.sleep(0.2)
        lookr = rm_fe(sock.recv(1000))
        if lookr.startswith('\xfe\x01\x01'):
            curr_stat = parse_stat(struct.unpack('B', lookr[3:4])[0])
            print 'Current TTL driver is',
            if curr_stat[1] == 'on':
                print '192 correlator.'
            elif curr_stat[2] == 'on':
                print '32 correlator.'
            elif curr_stat[3] == 'on':
                print 'ALWAYS ON.'
            elif curr_stat[3] == 'off':
                print 'ALWAYS OFF.'
            exit()
        else:
            print struct.unpack('B'*len(lookr), lookr)
            print 'Error. Please try again.'
            exit()
        ser.close()
    else:
        parser.print_help()
        #print 'Error: The command "%s" is unknown.' % args.source
        #print '       Use "32, 192, on, off, look" instead.'
        

