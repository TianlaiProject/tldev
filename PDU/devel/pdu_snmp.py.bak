from pysnmp.carrier.asyncore.dispatch import AsyncoreDispatcher
from pysnmp.carrier.asyncore.dgram import udp, udp6, unix
from pyasn1.codec.ber import encoder, decoder
from pysnmp.proto import api
from time import time
import argparse
import sys

class PDU():
    '''Power Distribution Unit class.'''
    def __init__(self, pdu_ip=None):
        self.ip = pdu_ip
        self.portnum = None #TODO: auto get from PDU
        self.name = None #TODO: auto get from PDU
        self.action_value = {'oni': 1, 'offi': 2, 'rebooti': 3,
                             'ond': 4, 'offd': 5, 'rebootd': 6}
        self.current = -1.0 #TODO: auto get from PDU
        self.location = None #TODO: auto get from PDU
        self.community = 'observer'
        self.command = {'current' : '1.3.6.1.4.1.318.1.1.12.2.3.1.1.2.1',
                        'pduname' : '1.3.6.1.3.94.1.6.1.20.1',
                        'outlet_name_' : '1.3.6.1.4.1.318.1.1.4.5.2.1.3.',
                        'setoutlet_' : '1.3.6.1.4.1.318.1.1.12.3.3.1.1.4.',
                        'outlet_status' : '1.3.6.1.4.1.318.1.1.4.2.2.0'}
        # Initilize portnum with requesting from PDU automatically.
        try:
            self.portnum = 8
        except:
            self.portnum = 8

    def _write(self, keys, values, IP=None):
        '''Write keys and values to PDU.
        keys and values are lists of the same length. Example:
        keys = ['1.3.6.1.4.1.318.1.1.4.5.2.1.3.1',]
        values = [1,]
        '''
        if len(keys) != len(values):
            print 'Error: the keys and values are not matched.'
            exit()
        if IP == None:
            IP = self.ip

        # Protocol version to use
        pMod = api.protoModules[api.protoVersion1]
        # Build PDU
        reqPDU = pMod.SetRequestPDU()
        pMod.apiPDU.setDefaults(reqPDU)
        pMod.apiPDU.setVarBinds(reqPDU, zip(keys, map(pMod.Integer, values)))
        reqMsg = pMod.Message()
        pMod.apiMessage.setDefaults(reqMsg)
        pMod.apiMessage.setCommunity(reqMsg, self.community)
        pMod.apiMessage.setPDU(reqMsg, reqPDU)
        
        startedAt = time()
        def cbTimerFun(timeNow):
            if timeNow - startedAt > 3:
                raise Exception('Request timed out')
        def cbRecvFun(transportDispatcher, transportDomain, transportAddress,
                      wholeMsg, reqPDU=reqPDU):
            while wholeMsg:
                rspMsg, wholeMsg = decoder.decode(wholeMsg, asn1Spec=pMod.Message())
                rspPDU = pMod.apiMessage.getPDU(rspMsg)
                # Match response to request
                if pMod.apiPDU.getRequestID(reqPDU) == pMod.apiPDU.getRequestID(rspPDU):
                    # Check for SNMP errors reported
                    errorStatus = pMod.apiPDU.getErrorStatus(rspPDU)
                    if errorStatus:
                        print(errorStatus.prettyPrint())
                    else:
                        for oid, val in pMod.apiPDU.getVarBinds(rspPDU):
                            #print '-----OK-----'
                            pass
                           
                    transportDispatcher.jobFinished(1)
            return wholeMsg
        
        transportDispatcher = AsyncoreDispatcher()
        transportDispatcher.registerRecvCbFun(cbRecvFun)
        transportDispatcher.registerTimerCbFun(cbTimerFun)
        
        # UDP/IPv4
        transportDispatcher.registerTransport(
        udp.domainName, udp.UdpSocketTransport().openClientMode()
        )
        
        # Pass message to dispatcher
        transportDispatcher.sendMessage(
        encoder.encode(reqMsg), udp.domainName, (IP, 161)
        )
        transportDispatcher.jobStarted(1)
        transportDispatcher.runDispatcher()
        transportDispatcher.closeDispatcher()

    def _read(self, keys, IP = None):
        '''read results for keys.
        keys is a list.
        '''
        if IP == None:
           IP = self.ip
        values = []

        pMod = api.protoModules[api.protoVersion1]
        # pMod = api.protoModules[api.protoVersion2c]
        # Build PDU
        reqPDU = pMod.GetRequestPDU()
        pMod.apiPDU.setDefaults(reqPDU)
        ###

        pMod.apiPDU.setVarBinds(reqPDU, zip(keys, [pMod.Null('')]*len(keys)))

        # Build message
        reqMsg = pMod.Message()
        pMod.apiMessage.setDefaults(reqMsg)
        pMod.apiMessage.setCommunity(reqMsg, self.community)
        pMod.apiMessage.setPDU(reqMsg, reqPDU)

        startedAt = time()
        def cbTimerFun(timeNow):
            if timeNow - startedAt > 3:
                raise Exception('Request timed out')

        def cbRecvFun(transportDispatcher, transportDomain, transportAddress,
                      wholeMsg, reqPDU=reqPDU):
            while wholeMsg:
                rspMsg, wholeMsg = decoder.decode(wholeMsg, asn1Spec=pMod.Message())
                rspPDU = pMod.apiMessage.getPDU(rspMsg)
                # Match response to request

                if pMod.apiPDU.getRequestID(reqPDU) == pMod.apiPDU.getRequestID(rspPDU):
                    # Check for SNMP errors reported
                    errorStatus = pMod.apiPDU.getErrorStatus(rspPDU)
                    if errorStatus:
                        print(errorStatus.prettyPrint())
                    else:
                        for oid, val in pMod.apiPDU.getVarBinds(rspPDU):
                            values.append(val.prettyPrint())

                    transportDispatcher.jobFinished(1)
            return wholeMsg

        transportDispatcher = AsyncoreDispatcher()
        transportDispatcher.registerRecvCbFun(cbRecvFun)
        transportDispatcher.registerTimerCbFun(cbTimerFun)

        # UDP/IPv4
        transportDispatcher.registerTransport(
        udp.domainName, udp.UdpSocketTransport().openClientMode()
        )
        # Pass message to dispatcher
        transportDispatcher.sendMessage(
        encoder.encode(reqMsg), udp.domainName, (IP, 161)
        )
        transportDispatcher.jobStarted(1)
        transportDispatcher.runDispatcher()
        transportDispatcher.closeDispatcher()
        return values

    def action(self, actions, outlets, IP = None):
        '''set outlet status.
        actions and outlets are list of the same length. Example:
        actions = ['oni', 'offd', 'rebooti']
        outlets = [2, 4, 5]
        port 2 will turn on immediately;
        port 4 will turn off delayed;
        port 5 will reboot immediately.
        '''
        if (type(actions) is list) and (type(outlets) is list):
            if len(outlets) != len(actions):
                print 'Error: outlets and actions do not matched.'
                print
                exit()
            if IP == None:
                IP = self.ip
            keys = []; values = []
            for i in xrange(len(outlets)):
                keys.append(self.command['setoutlet_'] + str(outlets[i]))
                values.append(self.action_value[actions[i]])
            self._write(keys, values, IP)
        else:
            print 'Error: your actions/outlets are of wrong format.'
            print 'actions ->', actions
            print 'outlets ->', outlets

    def get_outlet_name(self, outlets, IP = None):
        ''' get outlet status.
        outlets is list. Example: [1,5,6]
        '''
        if IP == None:
            IP = self.ip
        keys = []
        for i in xrange(len(outlets)):
            keys.append(self.command['outlet_name_'] + str(outlets[i]))
        values = self._read(keys, IP)
        return values

    def get_outlet_status(self, outlets = None, IP = None):
        ''' get outlet status.
        outlets is list. Example: [1,5,6]
        if outlets is None, will return status of all the outlets.
        '''
        if IP == None:
            IP = self.ip
        if outlets == None:
            outlets = range(1, self.portnum + 1)
        elif type(outlets) is str:
            if outlets == 'all':
                outlets = '1-' + str(self.portnum)
            outlets = parse_outlets(outlets)
        keys = [self.command['outlet_status']]
        for i in xrange(len(outlets)):
            keys.append(self.command['outlet_name_'] + str(outlets[i]))
        values = self._read(keys, IP)
        status = [''] + values[0].split()
        
        #values = self._read([self.command['outlet_status']], IP)
        #values = [''] + values[0].split()
        return outlets, map(status.__getitem__, outlets), values[1:]

    def get_current(self, IP = None):
        '''Get current.'''
        if IP == None:
            IP = self.ip
        self.current = float(self._read([self.command['current']], IP)[0]) / 10.
        return self.current

    def get_pdu_name(self, IP = None):
        '''Get PDU name.'''
        if IP == None:
            IP = self.ip
        return self._read([self.command['pduname']], IP)[0]

def parse_outlets(outlets):
    '''parse ports string to list.
    Example:
    "1"       ---> [1]
    "1,2,3"   ---> [1,2,3]
    "1,2-5,8" ---> [1,2,3,4,5,8]
    '''
    outlets = outlets.strip().replace(' ', '')
    if outlets[-1] == ',': outlets = outlets[:-1]
    if '-' in outlets:
        outlets = outlets.strip().split(',')
        outs = []
        for out_i in outlets:
            if '-' in out_i:
                chn_extend = map(int, out_i.split('-'))
                outs += range(chn_extend[0], chn_extend[1]+1)
            else:
                outs += [int(out_i)]
    else:
        outs = map(int, outlets.strip().split(','))
    return outs

def parse_actions(actions, outlets):
    '''parse actions string to list of the same length as ports.'''
    actions = actions.strip().split(',')
    while 1:
        try:
            actions.remove('')
        except ValueError:
            break
    return actions * len(parse_outlets(outlets)) if len(actions) == 1 else actions

def pretty_print_status(outlet_status):
    for i in xrange(len(outlet_status[0])):
        print '{0:<3}{1:<4s}{2:<}'.format(outlet_status[0][i], outlet_status[1][i], outlet_status[2][i])
 
if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Controller for Power Distrubution Unit')
    parser.add_argument('-d', '--dev', required=True, help='the PDU IP address; omit "192.168.1."')
    #parser.add_argument('-p', '--port', nargs=2, default =[13,'offi'],help='two arguments needed:chooose one outlet of pdu then take one action')
    parser.add_argument('-o', '--outlet', default = None, const = 'all', nargs = '?', help='input outlets splitted with comma')
    parser.add_argument('-a', '--action', help='input actions for all of the ports or splitted with comma for each outlet')
    parser.add_argument('-l', '--look', action = 'store_true', help="look outlet status of PDU: one argument needed.\teg-->all:look all outlet status.-----------------1,2,3: look outlet1,outlet2 and outlet3 status")
    parser.add_argument('-c', '--current', action='store_true', help='look current of PDU')
    parser.add_argument('-n', '--name', action='store_true', help='look name of PDU')
    
    options = parser.parse_args()

    if not (1 < int(options.dev) < 255):
        print 'Error: IP address is invalid.'
        exit()

    pdu88 = PDU('192.168.1.' + options.dev) # IP
    
    if options.look:
        outlet_status = pdu88.get_outlet_status(options.outlet)
        pretty_print_status(outlet_status)
        exit()
    if options.action:
        outlet_list = parse_outlets(options.outlet)
        action_list = parse_actions(options.action, options.outlet)
        print outlet_list
        print action_list
        pdu88.action(action_list, outlet_list)
        exit()
    if options.name:
        if options.outlet:
            if options.outlet == 'all':
                outlet_list = parse_outlets('1,2,3,4,5,6,7,8')
            else:
                outlet_list = parse_outlets(options.outlet)
            outlet_name = pdu88.get_outlet_name(outlet_list)
            print outlet_name
        else:
            print pdu88.get_pdu_name()
        exit()
    if options.current:
       current = pdu88.get_current()
       print 'Current = %.1f A' % current
       exit()
