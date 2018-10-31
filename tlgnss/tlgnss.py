#! /usr/bin/env python

import serial
import os
import struct
import threading
import Queue
import time
import signal
import string
from ctypes import c_ulong


# Use dict to store various settings.
settings = {}
# Rinex File Related
settings['RINEX_VERSION'] = '3.00' # This code only applies to version 3.00 .
# Rinex naming related. Ref. rinex300.pdf "4. The Exchange of Rinex Files".
# 4 character station name designator
settings['station'] = 'HLXA' # All Upper case; "HLX" for HongLiuXia; "A": Living area; "B": Antenna area; "C""D".... for future places.
settings['PGM_NAME'] = __file__[:-3] # Name of program creating current file; < 20 bytes.
settings['PGM_VER']  = '0.0'         # Version of program creating current file; < 20 bytes.
settings['PGM_RUNBY']= 'Tianlai Project'  # Name of agency  creating current file; < 20 bytes.
settings['MARKER_NAME'] = ' ' # Name of antenna marker
settings['MARKER_NUMBER'] = ' ' # Number of antenna marker
settings['MARKER_TYPE'] = 'NON_GEODETIC' # Type of the marker; See below:
            # GEODETIC     : Earth-fixed, high-precision monumentation
            # NON_GEODETIC : Earth-fixed, low-precision monumentation
            # NON_PHYSICAL : Generated from network processing
            # SPACEBORNE   : Orbiting space vehicle
            # AIRBORNE     : Aircraft, balloon, etc.
            # WATER_CRAFT  : Mobile water craft
            # GROUND_CRAFT : Mobile terrestrial vehicle
            # FIXED_BUOY   : "Fixed" on water surface
            # FLOATING_BUOY: Floating on water surface
            # FLOATING_ICE : Floating ice sheet, etc.
            # GLACIER      : "Fixed" on a glacier 
            # BALLISTIC    : Rockets, shells, etc 
            # ANIMAL       : Animal carrying a receiver
            # HUMAN        : Human being 
            # 
            # Record required except for GEODETIC and NON_GEODETIC marker types.
settings['OBSERVER'] = 'Jixia Li'             # < 20 bytes; Observer's name.
settings['AGENCY']   = 'NAOC, Beijing, China' # < 40 bytes; Observer's agency.
settings['REC_NO']   = ' ' # Receiver number; < 20 bytes
settings['REC_TYPE'] = ' ' # Receiver type;   < 20 bytes
settings['REC_VERS'] = ' ' # Receiver version;< 20 bytes
settings['ANT_NO']   = ' ' # Antenna number;  < 20 bytes
settings['ANT_TYPE'] = ' ' # Antenna type;    < 20 bytes
# Geocentric approximate marker position (Units: Meters, System: ITRS recommended) Optional for moving platforms.
settings['MKRPOS_X'] = 0.000 # Floating number; Marker position of X
settings['MKRPOS_Y'] = 0.000 # Floating number; Marker position of Y
settings['MKRPOS_Z'] = 0.000 # Floating number; Marker position of Z
settings['ANT_DELTAH'] = 0.0 # Floating number
settings['ANT_DELTAE'] = 0.0 # Floating number
settings['ANT_DELTAN'] = 0.0 # Floating number
settings['OBS_TIME_SYS'] = 'GPS' # Time system: GPS (=GPS time system), GLO (=UTC time system), GAL (=Galileo System Time), BDT (=BeiDou time system)
# Receiver related.
settings['datainterval'] = 1 # Seconds; Rangeb data output interval.
settings['serdev']   = '/dev/ttyUSB0' # Serial device.
settings['sercom'] = 'com1' # Receiver's COM port
settings['baudrate'] = 115200 # Serial port baudrate.
settings['sertimeout'] = 5 # Serial port timeout.
settings['qtimeout'] = 1.5 * settings['datainterval'] # Queue timeout.
settings['leapsecs'] = 18 # Leap seconds since gps epoch.
settings['rollover'] = 1 # Number of GPS week rollover times. After 2019/4/16, change the value to 2.
settings['datadir'] = './data/' # Data output directory.

######### Static settings. DO NOT edit below lines. ##########
# IDs of different messages defined by receiver.
MSGIDDICT = { #71: 'bd2ephemb',           412: 'bd2rawephemb',\
            # 741: 'bd2rawalmb',          210: 'bdgga',\
            #  42: 'bestposa',            241: 'bestxyz', \
            #  99: 'bestvela',            218: 'gpgga', \
            # 259: 'gpggartk',            219: 'gpgll', \
            # 221: 'gpgsa',               222: 'gpgst', \
            # 223: 'gpgsv',               228: 'gphdt', \
             101: 'timeb',               71: 'gpsephemb', \
            # 227: 'gpzda',                 8: 'ionutca', \
            #   5: 'loglista',             47: 'psrposa', \
             140: 'rangecmpb',            43: 'rangeb', \
            #  74: 'rawalmb',              41: 'rawephemb', \
         }  # Note: The ref manual gives 'gpsephemb' to be 712 which is wrong.
# Tracking status
#TRACKINGSTATE = {0: 'dle',    2: 'wideFrequencyBandPullin',
#                 3: 'narrowFrequencyBandPullin', 4: 'phaseLockLoop',
#                 7: 'frequencyLockLoop',  9: 'channelAlignment',
#                 10: 'codeSearch',     11: 'aidedPhaseLockLoop'}
# Observation type.
OBS_TYPE = {'G': ['C1C', 'L1C', 'D1C', 'C2P', 'L2P', 'D2P'], 
            'C': ['C1I', 'L1I', 'D1I', 'C7I', 'L7I', 'D7I','C6I', 'L6I', 'D6I']} # To consist with RINEX version 3.02 .
SIG_TYPE = {'G': [0, 9], 'C': [0, 17, 2]} # Signal type defined by receiver.
SYNC = '\xAA\x44\x12' # SYNC bytes in the beginning of the returned log data defined by receiver.
HEADERLENGTH = 28   # Header length of returned serial data. TODO: Though it is a fixed value now, it may change in future version of gnss receiver. 
LINE_BREAK = '\r\n' # Since the recorded data is mostly processed in Windows OS, a double line break of Return and Next line is needed for compatibility.
######### Static settings. DO NOT edit above lines. ###########

class CRC32(object):
    ''' CRC32 MODULE for data check.
        Originally written by Cristian NAVALICI cristian.navalici at gmail dot com
        Modified by Jixia Li (jxli at bao.ac.cn)
        Note: the CRC32 algorithm used by the receiver is different from the commonly used one, so I modified some parts of the codes.
    '''
    crc32_tab = []
    # The CRC's are computed using polynomials. Here is the most used coefficient for CRC32
    crc32_constant = 0xEDB88320

    def __init__(self):
        if not len(self.crc32_tab): self.init_crc32() # initialize the precalculated tables

    def calculate(self, string = ''):
        try:
            if not isinstance(string, str): raise Exception("Please provide a string as argument for calculation.")
            if not string: return 0

            #crcValue = 0xffffffff
            crcValue = 0x00000000 # Modified by Jixia Li
            for c in string:
                tmp = crcValue ^ ord(c)
                #crcValue = (crcValue >> 8) ^ int(self.crc32_tab[(tmp & 0x00ff)], 0)
                crcValue = ((crcValue >> 8) & 0x00ffffff) ^ int(self.crc32_tab[(tmp & 0x00ff)], 0) # Modified by Jixia Li

            # Only for CRC-32: When all bytes have been processed, take the
            # one's complement of the obtained CRC value
            #crcValue ^= 0xffffffff # (or crcValue = ~crcValue) # Commented by Jixia Li
            return crcValue
        except Exception, e:
            print "EXCEPTION(calculate): {}".format(e)

    def init_crc32(self):
        '''The algorithm use tables with precalculated values'''
        for i in xrange(0, 256):
            crc = i
            for j in range(0, 8):
                if (crc & 0x00000001):  crc = int(c_ulong(crc >> 1).value) ^ self.crc32_constant
                else:                   crc = int(c_ulong(crc >> 1).value)
            self.crc32_tab.append(hex(crc))

# CRC32 initialization.
crc32 = CRC32()

def parseGPSws(week, sow):
    '''Transfer GPS week and seconds of week to time struct.
    INPUT:
          week: GPS week with roll-over corrected, namely continuous week number without roll-over.
          sow:  Seconds Of Week, seconds since the beginning of one GPS week.
    RETURN: time struct. Note: this is GPS time, not UTC time, so no leap seconds.
    '''
    return time.gmtime(week * 604800 + 315964800 + sow)

def loghdr(bs):
    '''Parse log header of binary string sent from the GNSS receiver.
    INPUT: Binary String sent from the GNSS receiver.
    OUTPUT: dict.
    '''
    lh = {}
    lh['sync'] = bs[:3] # The sync bytes.
    lh['hdrlen'] = struct.unpack('<B', bs[3])[0] # Length of header.
    # The following check of header length validity has been done by read() function.
    #if lh['hdrlen'] != HEADERLENGTH:
    #    print 'Error: Log header length is not %s. This program does not support it and has to exit.' % HEADERLENGTH
    #    exit()
    lh['msgid']   = struct.unpack('<H', bs[ 4: 6])[0] # Message ID
    lh['msglen']  = struct.unpack('<H', bs[ 8:10])[0] # Message length
    lh['gpsweek'] = struct.unpack('<H', bs[14:16])[0] # GPS week number; Continuous number.
    lh['gpsms']   = struct.unpack('<L', bs[16:20])[0] # Milliseconds from the beginning of the GPS week.
    lh['RecvSwVer'] = struct.unpack('<H', bs[26:28])[0] # Receiver Software Version
    return lh

def parseChannelTracking(t):
    '''Parse channel tracking status.
    INPUT: unsigned long number t.
    OUTPUT: tracking status in dict.'''
    # See Table 25 of Receiver Reference Manual.
    d = {}
    #d['TrackingState'] = t & 0b11111
    #d['ChannelNumber'] = (t & 0b1111100000) >> 5
    #d['PhaseLockFlag'] = (t & 0x400) >> 10
    #d['ParityKnownFlag'] = (t & 0x800) >> 11
    #d['CodeLockedFlag'] = (t & 0x1000) >> 12
    #d['CorrelatorType'] = (t & 0b1110000000000000) >> 13
    #d['Satellite'] = (t & 0b1110000000000000000) >> 16
    ##d['reserved1'] = (t & 0x80000) >> 19
    #d['Grouping'] = (t & 0x100000) >> 20
    d['SignalType'] = (t & 0b11111000000000000000000000) >> 21
    #d['ForwardErrorCorrection'] = (t & 0x4000000) >> 26
    #d['PrimaryL1Channel'] = (t & 0x8000000) >> 27
    #d['CarrierPhaseMeasurement'] = (t & 0x10000000) >> 28
    ##d['reserved2'] = (t & 0x20000000) >> 29
    #d['PrnLockFlag'] = (t & 0x40000000) >> 30
    #d['ChannelAssignment'] = (t & 0x80000000) >> 31
    return d

def parse_rangeb(binstr):
    '''Parse the binary string from receiver to observation data.
    INPUT: Binary String sent from the GNSS receiver.
    OUTPUT: dict.
    '''
    # Obtain the CRC bytes.
    logcrc = binstr[-4:]
    if crc32.calculate(binstr[:-4]) != struct.unpack('<L', logcrc)[0]:
        print 'Error: CRC check failed. Received data may be incomplete - by parse_rangeb.'
        return None
    #header = loghdr(binstr[:HEADERLENGTH])
    data = binstr[HEADERLENGTH:-4]
    # Number of observations.
    #obsnum = struct.unpack('<L', binstr[header['hdrlen'] : header['hdrlen']+4])[0]
    obsnum = struct.unpack('<L', binstr[HEADERLENGTH:HEADERLENGTH+4])[0] # Equals number of satellites.
    # Use a dict to contain the observation data for one satellite with all different frequencies.
    satdict = {}
    for datai in xrange(obsnum):
        datadict = {} # Use a dict to contain observation data of one frequency band for one satellite.
        # Satellite PRN number; See Table 22 of Receiver Reference Manual.
        datadict['prn'] = struct.unpack('<H', data[4+44*datai: 6+44*datai])[0]
        # GLONASS Frequency + 7
        #datadict['glofre'] = struct.unpack('<H', data[6+44*datai: 8+44*datai])[0]
        # Pseudorange measurement (meter)
        datadict['psr'] = struct.unpack('<d', data[8+44*datai: 16+44*datai])[0]
        # Pseudorange measurement standard deviation (meter)
        #datadict['psrstd'] = struct.unpack('<f', data[16+44*datai: 20+44*datai])[0]
        # Carrier phase, in cycles (accumulated Doppler range)
        datadict['adr'] = -1*struct.unpack('<d', data[20+44*datai: 28+44*datai])[0]
        #print datadict['adr']
        # Estimated carrier phase standard deviation (cycles)
        #datadict['adrstd'] = struct.unpack('<f', data[28+44*datai: 32+44*datai])[0]
        # Instantaneous carrier Doppler frequency (Hz)
        datadict['dop'] = struct.unpack('<f', data[32+44*datai: 36+44*datai])[0]
        # Carrier to noise density ratio C/No = 10[log10(S/N0)] (dB-Hz)
        #datadict['CNR'] = struct.unpack('<f', data[36+44*datai: 40+44*datai])[0]
        # Number of seconds of continuous tracking (no cycle slipping)
        #datadict['locktime'] = struct.unpack('<f', data[40+44*datai: 44+44*datai])[0]
        # Tracking status; See Table 25 of Receiver Reference Manual.
        datadict['chntrack'] = parseChannelTracking(struct.unpack('<L', data[44+44*datai: 48+44*datai])[0])

        if datadict['prn'] in satdict.keys():
            satdict[datadict['prn']][datadict['chntrack']['SignalType']] = datadict
        else:
            satdict[datadict['prn']] = {datadict['chntrack']['SignalType']: datadict}
    return satdict

def parse_gpsephemb(binstr):
    '''Parse the binary string from receiver to navigation data.
    INPUT: Binary String sent from the GNSS receiver.
    OUTPUT: dict.
    '''
    # Obtain the CRC bytes.
    logcrc = binstr[-4:]
    if crc32.calculate(binstr[:-4]) != struct.unpack('<L', logcrc)[0]:
        print 'Error: CRC check failed. Received data may be incomplete - by parse_gpsephemb.'
        return None
    #header = loghdr(binstr[:HEADERLENGTH])
    data = binstr[HEADERLENGTH:-4]

    datadict = {}
    #datadict['wSize'] = struct.unpack('<H', data[:2])[0] # Struct size
    #datadict['blFlag'] = struct.unpack('B', data[2])[0]  # Eph valid flag
    datadict['bHealth'] = struct.unpack('B', data[3])[0] # Satellite health flag
    datadict['prn'] = struct.unpack('B', data[4])[0]   # Satellite prn (1~177)
    if datadict['prn'] > 140:
        # PRN in 141~177 are BeiDou satellites. Defined by the receiver.
        print 'This is BeiDou satellite.'
        #print 'BD week =', struct.unpack('<H', data[14:16])[0] + 1356 # BeiDou epoch started at GPS epoch's 1356th week.
        #print 'BD toc  =', struct.unpack('<d', data[32:40])[0] # BeiDou Time Of Clock.
        datadict['prn'] -= 140 # Correct the PRN.
        datadict['sat_sys'] = 'C' # Originally BeiDou system is named Compass.
        datadict['week'] = struct.unpack('<H', data[14:16])[0] + 1356 # BeiDou epoch started at GPS's 1356th week.
    else:
        # PRN in 1~32 are GPS satellites. Defined by the receiver.
        print 'This is GPS satellite.'
        datadict['sat_sys'] = 'G'
        datadict['week'] = struct.unpack('<H', data[14:16])[0] + 1024*settings['rollover'] # GPS week; 0~1023; Correct the roll over problem.
    #datadict['bReserved'] = struct.unpack('B', data[5])[0] # Reserved
    #datadict['uMsgID'] = struct.unpack('<H', data[6:8])[0] # ignored
    #datadict['m_wIdleTime'] = struct.unpack('<h', data[8:10])[0] # ignored
    datadict['iodc'] = struct.unpack('<h', data[10:12])[0] # Issue of data block
    datadict['accuracy'] = struct.unpack('<h', data[12:14])[0] # Reference to URA in paga-84 [doc13]
    datadict['iode'] = struct.unpack('<i', data[16:20])[0] # Issue of data
    datadict['tow'] = struct.unpack('<i', data[20:24])[0]  # time of eph be sent
    datadict['toe'] = struct.unpack('<d', data[24:32])[0] # Eph time
    datadict['toc'] = struct.unpack('<d', data[32:40])[0] # Time of clock-para
    datadict['af2'] = struct.unpack('<d', data[40:48])[0] # SV clock drift rate; Refer to ICD-GPS-200C.pdf page-86
    datadict['af1'] = struct.unpack('<d', data[48:56])[0] # SV clock drift;      Refer to ICD-GPS-200C.pdf page-86
    datadict['af0'] = struct.unpack('<d', data[56:64])[0] # SV clock bias;       Refer to ICD-GPS-200C.pdf page-86
    datadict['Ms0'] = struct.unpack('<d', data[64:72])[0] # Mean Anomaly
    datadict['deltan'] = struct.unpack('<d', data[72:80])[0] # Mean motion difference from computed value
    datadict['es'] = struct.unpack('<d', data[80:88])[0] # Eccentricity
    datadict['roota'] = struct.unpack('<d', data[88:96])[0] # Square root of A
    datadict['omega0'] = struct.unpack('<d', data[96:104])[0] # Longitude of ascending node of orbit plane at weekly epoch
    datadict['i0'] = struct.unpack('<d', data[104:112])[0] # Inclination angle at ref. times
    datadict['ws'] = struct.unpack('<d', data[112:120])[0] # Argument of perigee
    datadict['omegaot'] = struct.unpack('<d', data[120:128])[0] # Rate of right ascension
    datadict['itoet'] = struct.unpack('<d', data[128:136])[0] # Rate of inclination angle
    datadict['Cuc'] = struct.unpack('<d', data[136:144])[0] # Amplitude of the cosine harmonic correction term to the augument of latitude
    datadict['Cus'] = struct.unpack('<d', data[144:152])[0] # Amplitude of the sine harmonic correction term to the augument of latitude
    datadict['Crc'] = struct.unpack('<d', data[152:160])[0] # Amplitude of the cosine harmonic correction term to the orbit radius
    datadict['Crs'] = struct.unpack('<d', data[160:168])[0] # Amplitude of the sine harmonic correction term to the orbit radius
    datadict['Cic'] = struct.unpack('<d', data[168:176])[0] # Amplitude of the cosine harmonic correction term to the angle of inclination
    datadict['Cis'] = struct.unpack('<d', data[176:184])[0] # Amplitude of the sine harmonic correction term to the angle of inclination
    datadict['tgd'] = struct.unpack('<d', data[184:192])[0] # Reference to paga-90 [doc1]
    datadict['tgd2']= struct.unpack('<d', data[192:200])[0] # Only used in BD2 satellite, refer to BD2-ICD

    # P code is commanded ON for L2 channel.
    # 0b00 = Reserved;   0b01 = P code ON;   0b10 = C/A code ON.
    datadict['L2code'] = 0b1
    # Data flag for L2 P-Code.
    # 0b0 = navigation data stream is commanded ON  on P-code of L2 channel.
    # 0b1 = navigation data stream is commanded OFF on P-code of L2 channel.
    datadict['L2Pflag'] = 0b0
    # Fit interval; See ICD-GPS-200C, 20.3.4.4 .
    datadict['fitinterval'] = 0
    return datadict

#def parse_timeb(binstr):
#    '''Obtain the various time information.
#    INPUT: binary string send from the receiver.
#    OUTPUT: various time information in dict.
#    '''
#    # Obtain the CRC bytes.
#    logcrc = binstr[-4:]
#    if crc32.calculate(binstr[:-4]) != struct.unpack('<L', logcrc)[0]:
#        print 'Error: CRC check failed. Received data may be incomplete - by parse_timeb.'
#        return None
#    data = binstr[HEADERLENGTH:-4]
#    datadict = {}
#    datadict['clockstatus']=struct.unpack('<I', data[ 0: 4])[0] # Clock model status, refer to Table 35 of Receiver's Manual.
#    datadict['offset']    = struct.unpack('<d', data[ 4:12])[0] # Board clock offset
#    datadict['offsetstd'] = struct.unpack('<d', data[12:20])[0] # Board clock offset standard deviation.
#    datadict['UTCoffset'] = struct.unpack('<d', data[20:28])[0] # The offset of GPS time from UTC time, namely leap seconds.
#    datadict['UTCyear']   = struct.unpack('<L', data[28:32])[0] # UTC year
#    datadict['UTCmonth']  = struct.unpack('<B', data[32:33])[0] # UTC month (0-12)
#    datadict['UTCday']    = struct.unpack('<B', data[33:34])[0] # UTC day (0-31)
#    datadict['UTChour']   = struct.unpack('<B', data[34:35])[0] # UTC hour (0-23)
#    datadict['UTCmin']    = struct.unpack('<B', data[35:36])[0] # UTC minute (0-59)
#    datadict['UTCms']     = struct.unpack('<L', data[36:40])[0] # UTC millisecond (0-60999)
#    datadict['UTCstatus'] = struct.unpack('<L', data[40:44])[0] # UTC status, 0 = Invalid, 1 = Valid, 2 = Warning
#    return datadict

def read(qobs, qnav, evt, settings):
    '''Read bytes from serial port and send to specific queue according to data type.'''
    ser = serial.Serial(settings['serdev'], baudrate = settings['baudrate'], timeout = settings['sertimeout'])
    #ser.flushInput()
    #ser.write('log {0[sercom]} rangeb ontime 1\r\n'.format(settings))
    #print 'log {0[sercom]} rangeb ontime 1'.format(settings)
    #time.sleep(0.1)
    ser.write('log {0[sercom]} gpsephemb onchanged\r\n'.format(settings))
    print 'log {0[sercom]} gpsephemb onchanged'.format(settings)
    ser.write('log {0[sercom]} bd2ephemb onchanged\r\n'.format(settings))
    print 'log {0[sercom]} bd2ephemb onchanged'.format(settings)

    try:
        while not evt.isSet():
            #print 'Sub: new while.'
            bs = ser.read(3) # Read 3 bytes to judge whether the receiver works well.
            if len(bs) < 3: # In this case, the receiver may have stopped sending data.
                print 'Read: serial data < 3 bytes.'
                raise KeyboardInterrupt 
            if bs == SYNC: # This is the normal status.
                #print 'Sub: 3 bytes are 0xAA4412.'
                hdr_remain = ser.read(HEADERLENGTH - 3) # Read remaining bytes of the header.
                msglen = struct.unpack('<H', hdr_remain[5:7])[0] # Parse the length of the data part.
                msgcrc = ser.read(msglen + 4)  # Read the data and CRC bytes.
                #print 'Sub: read whole bytes'
                wholebs = '%s%s%s' % (bs, hdr_remain, msgcrc) # Build the whole bytes.

                header = loghdr(wholebs) # Parse log header in order to recognize what type the data is.
                if   MSGIDDICT[header['msgid']] == 'rangeb': # For rangeb data.
                    print '------', time.strftime('%Y/%m/%d %H:%M:%S'), '(UTC+8)---'
                    print 'Got data: rangeb.'
                    qobs.put_nowait((header, wholebs))
                elif MSGIDDICT[header['msgid']] == 'gpsephemb': # For gpsephemb data.
                    print 'Got data: gpsephemb.'
                    qnav.put_nowait((header, wholebs))
                # For other data, add more "elif" here.
                # elif MSGIDDICT[header['msgid']] == '':
                else: # For not supported data.
                    print 'Read: Got unknown data, message id =', header['msgid'], 'Ignored.'
                #print 'Sub: put into queue.'
            elif bs == '\r\nO': # This is the "OK" bytes indicating the receiver has just reponsed your command correctly.
                print 'Read: 3 bytes are OK bytes.'
                print '%s%s' % (bs, ser.readline()) # '\r\nOK!\r\n'
                print ser.readline() # 'Command accepted! Port: COM2.\r\n'
            else: # This is case for invalid data.
                print 'Read: unknown data encountered. Ignored.'
                #raise KeyboardInterrupt
                #time.sleep(0.01)
                # Note: the subthread is waiting on the queue. Once qtimeout is reached, it will exit. So here, "None" data are put into the queue indicating that the main thread is still running. 
                qobs.put_nowait((None, None))

                # Below lines will try to find the correct data by seaching the SYNC bytes.
                tried_times = 0
                ud = open('unknown_data64.bin', 'a')
                ud.write(bs)
                while 1:
                    bs = '{0}{1}'.format(bs[1:], ser.read(1))
                    ud.write(bs[-1])
                    if bs == SYNC: # SYNC bytes have been found.
                        hdr_remain = ser.read(HEADERLENGTH - 3)
                        msglen = struct.unpack('<H', hdr_remain[5:7])[0]
                        msgcrc = ser.read(msglen + 4)
                        #print 'Sub: read whole bytes'
                        wholebs = '%s%s%s' % (bs, hdr_remain, msgcrc)
        
                        # Parse log header.
                        header = loghdr(wholebs)
                        if   MSGIDDICT[header['msgid']] == 'rangeb':
                            print '--------', time.strftime('%Y/%m/%d %H:%M:%S'), '-------'
                            print 'Find data: rangeb.'
                            qobs.put_nowait((header, wholebs))
                        elif MSGIDDICT[header['msgid']] == 'gpsephemb':
                            print 'Find data: gpsephemb.'
                            qnav.put_nowait((header, wholebs))
                        else:
                            print 'Read: Got unknown data, message id =', header['msgid'], 'Ignored.'
                        #print 'Sub: put into queue.'
                        ud.write('---------------------------------------')
                        ud.close()
                        break
                    else: # Still not SYNC bytes.
                        tried_times += 1
                        print 'Trying to find correct data ->', tried_times
                        if tried_times > 5000: # Limit the trial within 5000 times.
                            print 'Read: Failed to find correct data.'
                            raise KeyboardInterrupt
                    
    except KeyboardInterrupt:
        print 'Read: keyboard interrupt.'
        pass
    finally:
        try:
            ser.close()
        except:
            pass
        evt.set()
        print 'Read: exit.'

def navdata_exist(navdatafile, input_time):
    '''Judge whether or not the navigation data has been stored in the navigation file.'''
    # Read the navigation data file and check the input_time in reverse lines.
    with open(navdatafile, 'r') as nd:
        for line in nd.readlines()[::-1]:
            if line.strip() == 'END OF HEADER':
                return False
            #if line.startswith('C') or line.startswith('G'):
            if line.startswith('G'): 
                break
    navdata_time = time.mktime(time.strptime(line[4:23], '%Y %m %d %H %M %S'))
    return navdata_time - time.mktime(input_time) <= 16 # Some satellites' clocks have 16 seconds offset.

def savenav(q, evt, settings):
    '''Navigation thread will receive data from queue and save data into navigation file.'''
    print 'SaveNav: started.'
    # Initialize part.
    header, it = q.get(timeout=settings['qtimeout'])
    last_day = int(header['gpsms'] / 1e3) / 86400
    first_navtime = parseGPSws(header['gpsweek'], header['gpsms']/1e3)
    rfnavname = rinex_naming(settings['station'], first_navtime, 'N')
    datayeardir = '{0}{1:d}/'.format(settings['datadir'], first_navtime.tm_year)
    if not os.path.exists(datayeardir): # When a new year begins; "./data/2017"
        os.mkdir(datayeardir)

    if os.path.exists(datayeardir + rfnavname) and os.path.getsize(datayeardir + rfnavname) > 0: # The file exists and is not empty, so there must be previous data in the file.
        # Different from observation data is that navigation data is updated every 1 hour, and the codes should avoid the case of storing repeated items when being started up. Example:
        # At 10:00, the code stored the navigation data to file. 
        # At 10:18, the code stopped due to power failure or any other case.
        # At 10:40, the code restarted again. At this time, the code will receive the same data as obtained at 10:00. So the newly received data should be ignored.
        # Judge whether the data has been stored or not in the file
        if navdata_exist(datayeardir + rfnavname, first_navtime):
            # Data have been stored. Do nothing.
            rfnav = open(datayeardir + rfnavname, 'a')
        else:
            # Data have not been stored. Store them.
            rfnav = open(datayeardir + rfnavname, 'a')
            print 'savenav: File exists. Add to the end.'
            rinex_data_nav(rfnav, parse_gpsephemb(it))
    else:
        # In this case, create file and then write header part.
        rfnav = open(datayeardir + rfnavname, 'a')
        print 'savenav: File does not exist. Create a new one.'
        rinex_hdr_nav(rfnav)
        rinex_data_nav(rfnav, parse_gpsephemb(it))
    
    try:
        while not evt.isSet():
            #print 'savenav: waiting queue get'
            try:
                header, it = q.get(timeout=settings['qtimeout'])
                #print 'savenav: got item from que'
            except Queue.Empty: # Recall that navigation data is updated in every one hour. So most of the time, no data is in the queue.
                continue
            #header = loghdr(it[:HEADERLENGTH])
            #print 'header week = ', header['gpsweek']
            #print 'header msec = ', header['gpsms']
            #if int(header['gpsms'] / 1e3) % 86400 == 0: # This is a new day of GPS epoch, so close current file and create a new one.
            this_day = int(header['gpsms'] / 1e3) / 86400
            print 'Today is', this_day
            if this_day != last_day:
                last_day = this_day
                try:
                    rfnav.close()
                except:
                    pass
                first_navtime = parseGPSws(header['gpsweek'], header['gpsms']/1e3)
                rfnavname = rinex_naming(settings['station'], first_navtime, 'N')
                datayeardir = '{0}{1:d}/'.format(settings['datadir'], first_navtime.tm_year)
                if not os.path.exists(datayeardir): # "./data/2017"; In case a new year begins.
                    os.mkdir(datayeardir)
                rfnav = open(datayeardir + rfnavname, 'a') 
                # Write header part of navigation data file.
                rinex_hdr_nav(rfnav)

            rinex_data_nav(rfnav, parse_gpsephemb(it))
            rfnav.flush()
    except KeyboardInterrupt:
        print 'SaveObs: Keyboard interrupt.'
    finally:
        try:
            rfnav.close()
        except:
            pass
        try:
            while 1: # Before exit, there must be no data in the queue.
                q.get(timeout=1)
                'SaveNav: Remove potential elements in the queue.'
        except Queue.Empty:
            print 'SaveNav: No elements in the queue. qsize =', q.qsize()
            pass
    return

def saveobs(q, evt, settings):
    '''Observation thread will receive data from queue and save data into observation file.'''
    print 'SaveObs: started.'
    # Initialize part.
    header, it = q.get(timeout=settings['qtimeout'])
    #header = loghdr(it[:HEADERLENGTH])
    first_obstime = parseGPSws(header['gpsweek'], header['gpsms']/1e3)
    rfobsname = rinex_naming(settings['station'], first_obstime, 'O')
    datayeardir = '{0}{1:d}/'.format(settings['datadir'], first_obstime.tm_year)
    if not os.path.exists(datayeardir): # When a new year begins; "./data/2017"
        os.mkdir(datayeardir)

    if os.path.exists(datayeardir + rfobsname) and os.path.getsize(datayeardir + rfobsname) > 0: # The file exists and is not empty.
        # In this case, add new data in the end, but epoch_flag = 1 indicating a power failure between previous and current epoch.
        rfobs = open(datayeardir + rfobsname, 'a')
        rinex_data_obs(rfobs, header, parse_rangeb(it), epoch_flag = 1)
    else:
        # In this case, create file and then write header part.
        rfobs = open(datayeardir + rfobsname, 'a')
        rinex_hdr_obs(rfobs, first_obstime, sat_obstype = OBS_TYPE)
        rinex_data_obs(rfobs, header, parse_rangeb(it))
    try:
        while not evt.isSet():
            #print 'Main: waiting queue get'
            header, it = q.get(timeout=settings['qtimeout'])
            if header == None:
                print 'SaveObs: None data in queue. Ignored.'
                continue
            #print 'Main: got item.'
            #header = loghdr(it[:HEADERLENGTH])
            print 'header week = ', header['gpsweek']
            print 'header msec = ', header['gpsms']
            print 'Secs left =', 86400 - (int(header['gpsms'] / 1e3) % 86400)
            if int(header['gpsms'] / 1e3) % 86400 == 0: # This is a new day of GPS epoch, so close current file and create a new one.
                try:
                    rfobs.close()
                except:
                    pass
                first_obstime = parseGPSws(header['gpsweek'], header['gpsms']/1e3)
                rfobsname = rinex_naming(settings['station'], first_obstime, 'O')
                datayeardir = '{0}{1:d}/'.format(settings['datadir'], first_obstime.tm_year)
                if not os.path.exists(datayeardir): # "./data/2017"; In case a new year begins.
                    os.mkdir(datayeardir)
                rfobs = open(datayeardir + rfobsname, 'a') 
                # Write header part of observation data file.
                rinex_hdr_obs(rfobs, first_obstime, sat_obstype = OBS_TYPE)

            rinex_data_obs(rfobs, header, parse_rangeb(it))
    except KeyboardInterrupt:
        print 'SaveObs: Keyboard interrupt.'
    except Queue.Empty:
        print 'SaveObs: No item in the queue for more than %.1f seconds.' % settings['qtimeout']
    finally:
        try:
            rfobs.close()
        except:
            pass
        try:
            while 1:
                time.sleep(0.1)
                q.get(timeout=1)
                print 'SaveObs: Remove potential elements in the queue.'
        except Queue.Empty:
            print 'SaveObs: No elements in the queue. qsize =', q.qsize()
            pass
    return

def rinex_naming(station, date, filetype, fseq = -1):
    '''Create rinex file name.
    station: station name. See below.
    date: time struct.
    filetype: file type. See below.
    fseq: hour in integer type: 0, 1, 2, ..., 23; Any valus < 0 means a daily file (defaults); Floats are permitted but will be transferred to integer with function int().

    Rinex File Naming Convention: (Ref. rinex300.pdf "4. The Exchange of Rinex Files")
    ssssdddf.yyt
    |   |  | | |
    |   |  | | +--  t: file type:
    |   |  | |         O: Observation file
    |   |  | |         N: GPS navigation message file
    |   |  | |         M: Meteorological data file
    |   |  | |         G: GLONASS navigation message file
    |   |  | |         L: Galileo navigation message file
    |   |  | |         P: Mixed GNSS navigation message file
    |   |  | |         H: SBAS Payload navigation message file
    |   |  | |         B: SBAS broadcast data file
    |   |  | |                       (separate documentation)
    |   |  | |         C: Clock file (separate documentation)
    |   |  | |         S: Summary file (used e.g., by IGS, not a standard!)
    |   |  | +---  yy: two-digit year
    |   |  +-----   f: file sequence number/character within day.
    |   |              daily file: f = 0 (zero)
    |   |              hourly files:
    |   |              a = 1st hour: 00h-01h; b = 2nd hour: 01h-02h;
    |   |                               . . . x = 24th hour: 23h-24h
    |   +-------  ddd: day of the year of first record
    +----------- ssss: 4-character station name designator
    '''
    fseq = '0' if fseq < 0 else string.lowercase[int(fseq)] # "0" for daily file; "a": 00h-01h; "b": 02h-03h; .......; x = 23h-24h
    return '{0}{1.tm_yday:03d}{2}.{3:02d}{4}'.format(station, date, fseq, date.tm_year-2000, filetype)

def rinex_hdr_obs(rf, first_obstime, creation_time = None, sat_sys_name = 'GC', sat_obstype = None, leap_seconds = 18, num_sat = None):
    '''Save header part of rinex observation file.
    rf: Rinex File object opened with open() function.
    first_obstime: Observation time of the first record.
    creation_time: time when rinex file is created. Defaults to None, use computer time.
    sat_sys_name: name(s) of satellite system(s), one or a combination of following:
                 G: GPS
                 R: GLONASS
                 E: Galileo
                 C: Beidou
                 S: SBAS payload
    sat_obstype: a dict containing satellite observation type. Example:
                 {'C': ['L1C', 'L5I'], 'G': ['C1C', 'L1W', 'L2W']}
    num_sat: number of satellites stored in the file. Defaults to None, namely "# OF SATELLITES" record is not stored.
    '''
    # Determine file creation time; if None, use computer time.
    # Format: "yyyymmdd hhmmss zone"
    #    zone: 3-4 char. code for time zone. UTC recommended!
    # Example: "20170319 164415 UTC"
    if creation_time == None:
        creation_time = time.strftime('%Y%m%d %H%M%S UTC', time.gmtime()) # TODO: Modify to use GPS time minus leap seconds.
    # Obtain sat_sys by parsing sat_sys_name
    sat_sys = 'M' if len(sat_sys_name) > 1 else sat_sys_name # "M" for Mixed satellite system.
    if sat_obstype == None:
        print 'Error: Satellite observation types are not defined.'
        exit()

    # Line  1: RINEX VERSION / TYPE
    rf.write('{0:>9}{1:11}{2:<20}{3:<20}{4:<20}{5}'.format(settings['RINEX_VERSION'], ' ', 'OBSERVATION DATA', sat_sys, 'RINEX VERSION / TYPE', LINE_BREAK))
    # Line  2: COMMENT for satellite system.
    rf.write('{0:<60}{1:<20}{2}'.format('G:GPS R:GLONASS E:GALILEO C:BDS S:GEO M:MIXED', 'COMMENT', LINE_BREAK))
    # Line: COMMENT for test.
    rf.write('{0:<60}{1:<20}{2}'.format('Current data is for test only. ----- Li Jixia', 'COMMENT', LINE_BREAK))
    # Line  3: Program, run by and creation time
    rf.write('{0:<20}{1:<20}{2:<20}{3:<20}{4}'.format(settings['PGM_NAME']+' V'+settings['PGM_VER'], settings['PGM_RUNBY'], creation_time, 'PGM / RUN BY / DATE', LINE_BREAK))
    # Line  4: Name of antenna marker
    rf.write('{0:<60}{1:<20}{2}'.format(settings['MARKER_NAME'], 'MARKER NAME', LINE_BREAK))
    # Line  5: (Optional) Number of antenna marker
    rf.write('{0:<60}{1:<20}{2}'.format(settings['MARKER_NUMBER'], 'MARKER NUMBER', LINE_BREAK))
    # Line  6: Type of antenna marker
    rf.write('{0:<20}{1:<40}{2:<20}{3}'.format(settings['MARKER_TYPE'], ' ', 'MARKER TYPE', LINE_BREAK))
    # Line  7: Name of observer / agency
    rf.write('{0:<20}{1:<40}{2:<20}{3}'.format(settings['OBSERVER'], settings['AGENCY'], 'OBSERVER / AGENCY', LINE_BREAK))
    # Line  8: Receiver number, type, and version
    rf.write('{0:<20}{1:<20}{2:<20}{3:<20}{4}'.format(settings['REC_NO'], settings['REC_TYPE'], settings['REC_VERS'], 'REC # / TYPE / VERS', LINE_BREAK))
    # Line  9: Antenna number and type
    rf.write('{0:<20}{1:<20}{2:<20}{3:<20}{4}'.format(settings['ANT_NO'], settings['ANT_TYPE'], ' ', 'ANT # / TYPE', LINE_BREAK))
    # Line 10: Geocentric approximate marker position (Units: Meters, System: ITRS recommended) Optional for moving platforms.
    rf.write('{0:<14.4f}{1:<14.4f}{2:<14.4f}{3:<18}{4:<20}{5}'.format(settings['MKRPOS_X'], settings['MKRPOS_Y'], settings['MKRPOS_Z'], ' ', 'APPROX POSITION XYZ', LINE_BREAK))
    # Line 11: Antenna height: Height of the antenna reference point (ARP) above the marker (units in meters)
    #          Horizontal eccentricity of ARP relative to the marker (east/north) (units in meters)
    rf.write('{0:<14.4f}{1:<14.4f}{2:<14.4f}{3:<18}{4:<20}{5}'.format(settings['ANT_DELTAH'], settings['ANT_DELTAE'], settings['ANT_DELTAN'], ' ', 'ANTENNA: DELTA H/E/N', LINE_BREAK))
    # Line 12: (Optional) Position of antenna reference point for antenna on vehicle (m): XYZ vector in body-fixed coord. system.
    #rf.write('{0:<14.4f}{1:<14.4f}{2:<14.4f}{3:<18}{4:<20}{5}'.format(ANT_DELTX, ANT_DELTY, ANT_DELTZ, ' ', 'ANTENNA: DELTA X/Y/Z', LINE_BREAK))
    # Line 13: (Optional) Average phase center position w/r to antenna reference point (m)
    #                     - Satellite system (G/R/E/S)
    #                     - Observation code
    #                     - North/East/Up (fixed station) or X/Y/Z in body-fixed system (vehicle)
    #rf.write('{0:1}{1:1}{2:<3}{3:<9.4f}{4:<14.4f}{5:<14.4f}{6:<18}{7}'.format(sat_sys[0], ' ', OBS_CODE, TODO, TODO, TODO, 'ANTENNA: PHASECENTER', LINE_BREAK))
    # Line 14: (Optional) Direction of the "vertical" antenna axis towards the GNSS satellites. TODO
    # Line 15: (Optional) Azimuth of the zero-direction of a fixed antenna (degrees, from north) TODO
    # Line 16: (Optional) Zero-direction of antenna on vehicle. TODO
    # Line 17: (Optional) Current center of mass (X,Y,Z, meters) of vehicle in body-fixed coordinate system. TODO
    # Line 18: - Satellite system code (G/R/E/S)
    #          - Number of different observation types for the specified satellite system
    #          - Observation descriptors: Type,Band,Attribute
    #          Refer to Table A1 of Appendix in "rinex300.pdf".
    #          By now, the number of observation types should be <= 13.
    
    for sat_sys_namei in sat_sys_name:
        num_obstype = len(sat_obstype[sat_sys_namei])
        if num_obstype > 13: # Currently, this program only supports obstypes <= 13
            print 'Error: the number of observation types should be <= 13. '
            try:
                rf.close()
            except:
                pass
            exit()
        rf.write('{0:1}{1:2}{2:>3}'.format(sat_sys_namei, ' ', num_obstype))
        for obs_typei in sat_obstype[sat_sys_namei]:
            rf.write('{0:1}{1:3}'.format(' ', obs_typei))
        rf.write('{0:{Nblank}}{1:<20}{2}'.format(' ', 'SYS / # / OBS TYPES', LINE_BREAK, Nblank=54-4*num_obstype))
    # Line 19: (Optional) Unit of the signal strength
    #rf.write('{0:<20}{1:<40}{2:<20}{3}'.format('DBHZ', ' ', 'SIGNAL STRENGTH UNIT', LINE_BREAK))
    # Line 20: (Optional) Observation interval in seconds
    #rf.write('{0:<10.3f}{1:<50}{2:<20}{3}'.format(TODO, ' ', 'INTERVAL', LINE_BREAK))
    # Line 20: Time of first observation record
    rf.write('{0.tm_year:>6d}{0.tm_mon:>6d}{0.tm_mday:>6d}{0.tm_hour:>6d}{0.tm_min:>6d}{1:>13.7f}{2:5}{3:3}{4:9}{5}'.format(first_obstime, first_obstime.tm_sec, ' ', settings['OBS_TIME_SYS'], ' ', LINE_BREAK)) #TODO: How to determine first observation time?
    # Line 21: (Optional) Time of last observation record
    #rf.write('{0.tm_year:>6d}{0.tm_mon:>6d}{0.tm_mday:>6d}{0.tm_hour:>6d}{0.tm_min:>6d}{1:>13.7f}{2:5}{3:3}{4:9}{5}'.format(last_obs_time, last_obs_time_sec, ' ', settings['OBS_TIME_SYS'], ' ', LINE_BREAK)) # TODO
    # Line 22: (Optional) Epoch, code, and phase are corrected by applying the realtime-derived receiver clock offset: 1=yes, 0=no; default: 0=no Record required if clock offsets are reported in the EPOCH/SAT records TODO
    # Line 23: (Optional) SYS / DCBS APPLIED TODO
    # Line 24: (Optional) SYS / PCVS APPLIED TODO
    # Line 25: (Optional) SYS / SCALE FACTOR TODO
    # Line 26: (Optional) Number of leap seconds since 6-Jan-1980 as transmitted by the GPS almanac. Recommended for mixed GLONASS files. TODO
    #rf.write('{0:>6d}{1:54}{2:>20}{3}'.format(leap_seconds, ' ', 'LEAP SECONDS', LINE_BREAK))
    # Line 27: (Optional) Number of satellites, for which observations are stored in the file.
    if num_sat != None:
        rf.write('{0:>6d}{1:54}{2:>20}{3}'.format(num_sat, ' ', '# OF SATELLITES', LINE_BREAK))
    # Line 28: (Optional) Satellite numbers, number of observations for each observation type indicated in the SYS / # / OBS TYPES record. TODO
    #                     If more than 9 observation types: Use continuation line(s)
    #                     This record is (these records are) repeated for each satellite present in the data file.
    # Line 29: Last record in the header section.
    rf.write('{0:60}{1:<20}{2}'.format(' ', 'END OF HEADER', LINE_BREAK))
    rf.flush()
    return 

def rinex_hdr_nav(rf, creation_time = None, sat_sys_name = 'GC', leap_seconds = 18):
    '''Save header part of rinex navigation file.
    rf: Rinex File object opened with open() function.
    creation_time: time when rinex file is created.
    sat_sys_name: name(s) of satellite system(s), one or a combination of following:
                 G: GPS
                 R: GLONASS
                 E: Galileo
                 C: Beidou
                 S: SBAS payload
    '''
    # Determine file creation time; if None, use computer time.
    # Format: "yyyymmdd hhmmss zone"
    #    zone: 3-4 char. code for time zone. UTC recommended!
    # Example: "20170319 164415 UTC"
    if creation_time == None:
        creation_time = time.strftime('%Y%m%d %H%M%S UTC', time.gmtime())
    # Obtain sat_sys by parsing sat_sys_name
    sat_sys = 'M' if len(sat_sys_name) > 1 else sat_sys_name # "M" for Mixed satellite system.

    # Line  1: RINEX VERSION / TYPE
    rf.write('{0:>9}{1:11}{2:<20}{3:<20}{4:<20}{5}'.format(settings['RINEX_VERSION'], ' ', 'NAVIGATION DATA', sat_sys, 'RINEX VERSION / TYPE', LINE_BREAK))
    # Line  2: COMMENT for satellite system.
    rf.write('{0:<60}{1:<20}{2}'.format('G:GPS R:GLONASS E:GALILEO C:BDS S:GEO M:MIXED', 'COMMENT', LINE_BREAK))
    # Line: COMMENT for test.
    rf.write('{0:<60}{1:<20}{2}'.format('Current data is for test only. ----- Li Jixia', 'COMMENT', LINE_BREAK))
    # Line  3: Program, run by and creation time
    rf.write('{0:<20}{1:<20}{2:<20}{3:<20}{4}'.format(settings['PGM_NAME']+' V'+settings['PGM_VER'], settings['PGM_RUNBY'], creation_time, 'PGM / RUN BY / DATE', LINE_BREAK))
    # Line  4: (Optional) Ionospheric correction parameters.
    # Line  5: (Optional) Corrections to transform the system time to UTC or other time system.
    # Line  6: (Optional) - Number of leap seconds since 6-Jan-1980 as transmitted by the GPS almanac \delta t_LS
    #                     - Future or past leap seconds \detla t_LSF
    #                     - Respective week number WN_LSF (continuous number)
    #                     - Respective day number DN (see ICD-GPS-200C 20.3.3.5.2.4)
    #                     Zero or blank if not known
    #rf.write('{0:>6d}{1:>6d}{2:>6d}{3:>6d}'.format(leap_seconds, t_lsf, wn_lsf, dn))
    # Line 7: Last record in the header section.
    rf.write('{0:60}{1:<20}{2}'.format(' ', 'END OF HEADER', LINE_BREAK))
    rf.flush()
    return

def rinex_data_obs(rf, loghdr, data, epoch_flag = 0 ):
    '''Save data part of rinex observation file.
    rf: Rinex File object opened with open() function.
    loghdr: Log header.
    data: A dict containing the observation data to be saved.
    epoch_flag: 0: OK;   1: power failure between previous and current epoch;   >1: Special event.
    '''
    if data == None:
        print 'Warn: No obs data is saved.'
        return
    toe = parseGPSws(loghdr['gpsweek'], loghdr['gpsms']/1e3) # Time of epoch.
    toe_sec = toe.tm_sec + loghdr['gpsms']/1e3 % 1 # Seconds of Epoch; fractional.
    sat_num = len(data) # Number of satellites observed in current epoch
    rf.write('{0} {1.tm_year:4d} {1.tm_mon:02d} {1.tm_mday:02d} {1.tm_hour:02d} {1.tm_min:02d}{2:>11.7f}  {3:1d}{4:>3d}      {5:15}{6}'.format('>', toe, toe_sec, epoch_flag, sat_num, ' ', LINE_BREAK)) # Note: {5} is the receiver clock offset, should be {5:>15.12f}, but is optional.

    # The following records differ in different Epoch flags
    if epoch_flag == 0 or epoch_flag == 1:
    # Use dict to store data
        for datai in sorted(data.keys()):
            # Current receiver only supports GPS and BeiDou system, so use prn to judge satellite system.
            if 140 < datai < 178: # This is BeiDou data.
                sat = 'C'
                rf.write('{0}{1:02d}'.format(sat, datai-140)) # Satellite and PRN
            elif 0 < datai < 33: # This is GPS data.
                sat = 'G'
                rf.write('{0}{1:02d}'.format(sat, datai)) # Satellite and PRN
            else:
                print 'Error: Not supported satellite system. PRN =', datai
                print "       Refer to Table 22 of Receiver's manual for more information."
                exit()
            # Observation type.
            for sigi in SIG_TYPE[sat]:
                #print 'datai = ', datai
                if sigi in data[datai]:
                    rf.write('{0[psr]:>14.3f}{1:1}{2:1}{0[adr]:>14.3f}{1:1}{2:1}{0[dop]:>14.3f}{1:1}{2:1}'.format(data[datai][sigi], ' ', ' ')) # TODO: LLI and Signal strength are omitted here.
                else:
                    rf.write('{0:48}'.format(' '))
            rf.write(LINE_BREAK)

    elif 1 < epoch_flag < 6:
        raise NotImplementedError
        #rf.write()
    elif epoch_flag == 6:
        raise NotImplementedError
        #rf.write()
    else:
        print 'Error: epoch_flag = %d is not defined.' % epoch_flag
    return

def rinex_data_nav(rf, data):
    '''Save data part of rinex navigation file.
    rf: Rinex File object opened with open() function.
    data: A dict containing the navigation data to be saved.
    '''
    toc = parseGPSws(data['week'], data['toc']) # Time of clock.
    # SV / EPOCH / SV CLK
    rf.write('{0[sat_sys]:1}{0[prn]:02d} {1.tm_year:4d} {1.tm_mon:02d} {1.tm_mday:02d} {1.tm_hour:02d} {1.tm_min:02d} {1.tm_sec:02d}{0[af0]:>19.12E}{0[af1]:>19.12E}{0[af2]:>19.12E}{2}'.format(data, toc, LINE_BREAK))
    # BROADCAST ORBIT - 1
    rf.write('{0:4}{1[iode]:>19.12E}{1[Crs]:>19.12E}{1[deltan]:>19.12E}{1[Ms0]:>19.12E}{2}'.format(' ', data, LINE_BREAK))
    # BROADCAST ORBIT- 2
    rf.write('{0:4}{1[Cuc]:>19.12E}{1[es]:>19.12E}{1[Cus]:>19.12E}{1[roota]:>19.12E}{2}'.format(' ', data, LINE_BREAK))
    # BROADCAST ORBIT- 3
    rf.write('{0:4}{1[toe]:>19.12E}{1[Cic]:>19.12E}{1[omega0]:>19.12E}{1[Cis]:>19.12E}{2}'.format(' ', data, LINE_BREAK))
    # BROADCAST ORBIT- 4
    rf.write('{0:4}{1[i0]:>19.12E}{1[Crc]:>19.12E}{1[ws]:>19.12E}{1[omegaot]:>19.12E}{2}'.format(' ', data, LINE_BREAK))
    # BROADCAST ORBIT- 5
    rf.write('{0:4}{1[itoet]:>19.12E}{1[L2code]:>19.12E}{1[week]:>19.12E}{1[L2Pflag]:>19.12E}{2}'.format(' ', data, LINE_BREAK))
    # BROADCAST ORBIT- 6
    rf.write('{0:4}{1[accuracy]:>19.12E}{1[bHealth]:>19.12E}{1[tgd]:>19.12E}{1[iodc]:>19.12E}{2}'.format(' ', data, LINE_BREAK))
    # BROADCAST ORBIT- 7
    rf.write('{0:4}{1[tow]:>19.12E}{1[fitinterval]:>19.12E}{0:19}{0:19}{2}'.format(' ', data, LINE_BREAK))
    return
 
if __name__ == '__main__':
    # To capture KeyboardInterrupt.
    signal.signal(signal.SIGINT, signal.default_int_handler)
    # Record the PID for end.sh to kill the process.
    with open('.proc_pid.txt', 'w') as pypid:
        pypid.write(str(os.getpid()) + '\n')

    # Use queue to transfer data from main thread to subthread.
    qobs = Queue.Queue()
    qnav = Queue.Queue()
    # Use event to indicate running status.
    evt = threading.Event()

    # obsthread will receive data from queue, analyze the data and finally save data to observation data file.
    obsthread = threading.Thread(target=saveobs, args = (qobs, evt, settings))
    # navthread will receive data from queue, analyze the data and finally save data to navigation data file.
    navthread = threading.Thread(target=savenav, args = (qnav, evt, settings))
    print 'Start sub thread.'
    obsthread.start()
    navthread.start()
    # Main thread will read serial data and send to specific queue according to data type.
    read(qobs, qnav, evt, settings)

    print 'Main: Begin to join subthread.'
    obsthread.join()
    navthread.join()
    print 'Main: Successfully exit.'
