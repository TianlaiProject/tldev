#######################################
# Version 1.0                         #
# Last modified: 2015/12/26           #
# Any problem, contact jxli@bao.ac.cn #
#######################################

import time
import argparse
import sys
import corrswitch
import pdu

PDU1_ip = '192.168.1.66'
PDU2_ip = '192.168.1.67'

if __name__ == '__main__':
    corrsw = corrswitch.corrSwitch()
    parser = argparse.ArgumentParser(description='Correlator power controller')
    parser.add_argument('-o', '--on', action='store_true', help='power on the whole correlator system')
    parser.add_argument('-f', '--off', action='store_true', help='power off the whole correlator system')
    parser.add_argument('-r', '--restart', type=str, dest='devname', help='restart device(s); e.g. "adc10,sw0,dsp5"')
    #parser.add_argument('-n', '--name', type=str, dest='devname', help='Choose device name: adcN, swN, dspN, where N is a number.')
    #parser.add_argument('-c', '--chassis', dest='addr', type=int, choices=range(1,MAX_CHASSIS+1), help='choose chassis number (1-6).')
    #parser.add_argument('-p', '--port', type=int, choices=range(1,MAX_PORT+1), help='Choose port number (1-16).')
    #parser.add_argument('-l', '--look', action='store_true', help='look current ports status; chassis is needed')
    options = parser.parse_args()

    if options.on == True:
        print 'Turn off all switches.'
        corrsw.shutdown()
        print 'Begin starting the whole system ...'
        time.sleep(1)
        print 'Turn on port 1 and 2 of PDU1.'
        pdu.run(PDU1_ip, [1,2], 'on')
        #time.sleep(1)
        print 'Turn on port 1 and 2 of PDU2.'
        pdu.run(PDU2_ip, [1,2], 'on')
        time.sleep(1)
        print 'Turn on port 3 and 4 of PDU1.'
        pdu.run(PDU1_ip, [3,4], 'on')
        #time.sleep(1)
        print 'Turn on port 1 and 2 of PDU2.'
        pdu.run(PDU2_ip, [3,4], 'on')
        time.sleep(3)
        corrsw.power('on')
        exit()
    if options.off == True:
        print 'Begin shutting down the whole system ...'
        print 'Turn off all switches.'
        corrsw.shutdown()
        time.sleep(1)
        print 'Turn off PDU1.'
        pdu.run(PDU1_ip, [1,2,3,4], 'off')
        print 'Turn off PDU2.'
        pdu.run(PDU2_ip, [1,2,3,4], 'off')
        exit()
    if options.devname != None:
        inputdev = options.devname.split(',')
        if 'sw0' in inputdev or 'sw1' in inputdev:
            print 'Restarting sw0/sw1 ',
            sys.stdout.flush()
            pdu.run(PDU1_ip, [2], 'off')
            time.sleep(1)
            pdu.run(PDU1_ip, [2], 'on')
            print '[OK]'
        if 'sw2' in inputdev or 'sw3' in inputdev:
            print 'Restarting sw2/sw3 ',
            sys.stdout.flush()
            pdu.run(PDU2_ip, [2], 'off')
            time.sleep(1)
            pdu.run(PDU2_ip, [2], 'on')
            print '[OK]'
        for swN in ['sw0', 'sw1', 'sw2', 'sw3']:
            try:
                inputdev.remove(swN)
            except ValueError:
                continue
        if inputdev != []:
            inputdev = str(inputdev)[1:-1].replace(' ', '').replace("'","")
            corrsw.restart(inputdev)
        
    #if options.devname != None:
    #    options.addr, options.port = name2ap(options.devname)
    #if options.look == True:
    #    if options.addr == None:
    #        parser.print_help()
    #        print 'Chassis number is needed.'
    #        exit()
    #    look(options.addr)
    #    exit()
    #if options.restart == True:
    #    if options.addr == None:
    #        parser.print_help()
    #        print 'Chassis number is needed.'
    #        exit()
    #    if options.port == None:
    #        parser.print_help()
    #        print 'Port number is needed.'
    #        exit()
    #    restart(options.addr, options.port)
    #    exit()
