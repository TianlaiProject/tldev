# -*- coding: utf-8 -*-
#@author: congyanping

from pysnmp.carrier.asyncore.dispatch import AsyncoreDispatcher
from pysnmp.carrier.asyncore.dgram import udp, udp6, unix
from pyasn1.codec.ber import encoder, decoder
from pysnmp.proto import api
from time import time
import argparse
import sys

class pdu():
    '''PDU class.'''
    def __init__(self, pdu_ip):
        
        self.ip = pdu_ip
        self.ports = 8
        self.name = None
        self.action_dict = { 'oni': 1,   'offi': 2,   'rebooti': 3,
			     'ond': 4,   'offd': 5,   'rebootd': 6 }
        self.outlet=[1,2,3,4,5,6,7,8]
        self.current = -1.0
        self.location = None
        self.community = 'observer'
	self.command={	'current':'1.3.6.1.4.1.318.1.1.12.2.3.1.1.2.1',
		      	'name':'1.3.6.1.3.94.1.6.1.20.1',
			'outlet_header':'1.3.6.1.4.1.318.1.1.12.3.3.1.1.4.',
		      	'port':'1.3.6.1.4.1.318.1.1.4.2.2.0',
		 	'name_1': '1.3.6.1.4.1.318.1.1.4.5.2.1.3.1',
			'name_2': '1.3.6.1.4.1.318.1.1.4.5.2.1.3.2',
			'name_3': '1.3.6.1.4.1.318.1.1.4.5.2.1.3.3',
			'name_4': '1.3.6.1.4.1.318.1.1.4.5.2.1.3.4',
			'name_5': '1.3.6.1.4.1.318.1.1.4.5.2.1.3.5',
			'name_6': '1.3.6.1.4.1.318.1.1.4.5.2.1.3.6',
		  	'name_7': '1.3.6.1.4.1.318.1.1.4.5.2.1.3.7',
			'name_8': '1.3.6.1.4.1.318.1.1.4.5.2.1.3.8',
		        'name_9': '1.3.6.1.4.1.318.1.1.4.5.2.1.3.9',
		        'name_10':'1.3.6.1.4.1.318.1.1.4.5.2.1.3.10',
 			'name_11':'1.3.6.1.4.1.318.1.1.4.5.2.1.3.11',
                        'name_12':'1.3.6.1.4.1.318.1.1.4.5.2.1.3.12',
                        'name_13':'1.3.6.1.4.1.318.1.1.4.5.2.1.3.13',
	   		'name_14':'1.3.6.1.4.1.318.1.1.4.5.2.1.3.14',
			'name_15':'1.3.6.1.4.1.318.1.1.4.5.2.1.3.15',
			'name_16':'1.3.6.1.4.1.318.1.1.4.5.2.1.3.16'	
			}
    def SET(self, outlet, action, IP = None):
        '''Set parameter for PDU.'''
        if IP == None:
	    IP = self.ip
        # Protocol version to use
        pMod = api.protoModules[api.protoVersion1]
            # Build PDU
        reqPDU = pMod.SetRequestPDU()
        pMod.apiPDU.setDefaults(reqPDU)
        outlet=str(outlet)
        pMod.apiPDU.setVarBinds(
                reqPDU,
                  (
                  (self.command['outlet_header']+outlet, pMod.Integer(self.action_dict[action])),
            ))
        
        reqMsg = pMod.Message()
        pMod.apiMessage.setDefaults(reqMsg)
        pMod.apiMessage.setCommunity(reqMsg, self.community)
        pMod.apiMessage.setPDU(reqMsg, reqPDU)
        
        startedAt = time()
        def cbTimerFun(timeNow):
            if timeNow - startedAt > 3:
                raise Exception("Request timed out")
        
        # noinspection PyUnusedLocal,PyUnusedLocal
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
                            print '-----OK-----'
                            #print('%s = %s' % (oid.prettyPrint(), val.prettyPrint()))
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
    
    """Get information"""
    # Build PDU
    def GEToutlet(self, outlet=None,IP = None):
        if IP == None:
           IP = self.ip
        pMod = api.protoModules[api.protoVersion1]
        # pMod = api.protoModules[api.protoVersion2c]
        # Build PDU
        reqPDU = pMod.GetRequestPDU()
        pMod.apiPDU.setDefaults(reqPDU)
        pMod.apiPDU.setVarBinds(
            reqPDU, ((self.command['name'], pMod.Null('')),
		    (self.command['port'], pMod.Null('')),
		    (self.command['name_1'],pMod.Null('')),
		    (self.command['name_2'],pMod.Null('')),
		    (self.command['name_3'],pMod.Null('')),
		    (self.command['name_4'],pMod.Null('')),
		    (self.command['name_5'],pMod.Null('')),
		    (self.command['name_6'],pMod.Null('')),
		    (self.command['name_7'],pMod.Null('')),
		    (self.command['name_8'],pMod.Null('')),
		    #(self.command['name_9'],pMod.Null('')
			    )
                    			
	    )	
        
        # Build message
        reqMsg = pMod.Message()
        pMod.apiMessage.setDefaults(reqMsg)
        pMod.apiMessage.setCommunity(reqMsg, self.community)
        pMod.apiMessage.setPDU(reqMsg, reqPDU)
        
        startedAt = time()
        def cbTimerFun(timeNow):
            if timeNow - startedAt > 3:
                raise Exception("Request timed out")
        
        # noinspection PyUnusedLocal,PyUnusedLocal
        def cbRecvFun(transportDispatcher=None, transportDomain=None, transportAddress=None,
                      wholeMsg=None, reqPDU=reqPDU):
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
                            oid_str = oid.prettyPrint()
                            
                            if   oid_str =='1.3.6.1.4.1.318.1.1.4.2.2.0':
				 self.result_str=val.prettyPrint()

			    elif oid_str == self.command['name_1']: 
			         self.nothing=[]
			         self.nothing.append(val.prettyPrint())
                            elif oid_str == self.command['name_2']:
	                         self.nothing.append(val.prettyPrint())
			    elif oid_str == self.command['name_3']:
				 self.nothing.append(val.prettyPrint()) 
		            elif oid_str == self.command['name_4']:
				 self.nothing.append(val.prettyPrint())
			    elif oid_str == self.command['name_5']:
				 self.nothing.append(val.prettyPrint())
			    elif oid_str == self.command['name_6']:
				 self.nothing.append(val.prettyPrint())
		            elif oid_str == self.command['name_7']:
				 self.nothing.append(val.prettyPrint())
		            elif oid_str == self.command['name_8']:
				 self.nothing.append(val.prettyPrint())

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
        
        ## UDP/IPv6 (second copy of the same PDU will be sent)
        # transportDispatcher.registerTransport(
        #    udp6.domainName, udp6.Udp6SocketTransport().openClientMode()
        # )
        
        # Pass message to dispatcher
        # transportDispatcher.sendMessage(
        #    encoder.encode(reqMsg), udp6.domainName, ('::1', 161)
        # )
        # transportDispatcher.jobStarted(1)
        
        ## Local domain socket
        # transportDispatcher.registerTransport(
        #    unix.domainName, unix.UnixSocketTransport().openClientMode()
        # )
        #
        # Pass message to dispatcher
        # transportDispatcher.sendMessage(
        #    encoder.encode(reqMsg), unix.domainName, '/tmp/snmp-agent'
        # )
        # transportDispatcher.jobStarted(1)
        
        # Dispatcher will finish as job#1 counter reaches zero
       
        transportDispatcher.runDispatcher()
	self.nothing=self.nothing+['...','...','...','...','...','...','...','...',]
	#print self.nothing
	result_str=self.result_str.split()
        for i, element in enumerate(result_str):
            result_str[i]='%d--%s--%s' % (i+1,self.nothing[i],result_str[i])
	if outlet==None:
	   for i in range(len(result_str)):
	       print  result_str[i]
	else:
	    try: 
	       for j in outlet:
		   j=int(j)
		   print result_str[j-1]
            except:
		  print 'one outlet dosen\'t existence,please check the number of outlet'
        transportDispatcher.closeDispatcher()
    def GETname(self, IP = None):
        if IP == None:
           IP = self.ip
        pMod = api.protoModules[api.protoVersion1]
        # pMod = api.protoModules[api.protoVersion2c]
        
        # Build PDU
        reqPDU = pMod.GetRequestPDU()
        pMod.apiPDU.setDefaults(reqPDU)
        pMod.apiPDU.setVarBinds(
            reqPDU, ((self.command['name'], pMod.Null('')),
        ))
        
        # Build message
        reqMsg = pMod.Message()
        pMod.apiMessage.setDefaults(reqMsg)
        pMod.apiMessage.setCommunity(reqMsg, self.community)
        pMod.apiMessage.setPDU(reqMsg, reqPDU)
        
        startedAt = time()
        
        def cbTimerFun(timeNow):
            if timeNow - startedAt > 3:
                raise Exception("Request timed out")
        
        # noinspection PyUnusedLocal,PyUnusedLocal
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
                            oid_str = oid.prettyPrint()
                            if  oid_str =='1.3.6.1.3.94.1.6.1.20.1':
                                print('%s' % (val.prettyPrint()))
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
    def GETcurrent(self, IP = None):
        if IP == None:
           IP = self.ip
        pMod = api.protoModules[api.protoVersion1]
        
        # Build PDU
        reqPDU = pMod.GetRequestPDU()
        pMod.apiPDU.setDefaults(reqPDU)
        pMod.apiPDU.setVarBinds(
            reqPDU, (
                     (self.command['current'], pMod.Null('')),
        ))
        
        # Build message
        reqMsg = pMod.Message()
        pMod.apiMessage.setDefaults(reqMsg)
        pMod.apiMessage.setCommunity(reqMsg, self.community)
        pMod.apiMessage.setPDU(reqMsg, reqPDU)
        
        startedAt = time()
        
        
        def cbTimerFun(timeNow):
            if timeNow - startedAt > 3:
               raise Exception("Request timed out")
        
        # noinspection PyUnusedLocal,PyUnusedLocal
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
                            oid_str = oid.prettyPrint()
                            if  oid_str =='1.3.6.1.4.1.318.1.1.12.2.3.1.1.2.1':
                                print('%s' % (val.prettyPrint()))
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
if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Controller for PDU')
    parser.add_argument('-d', '--dev', required=True, help='the outlet IP address; omit "192.168.1."')
    parser.add_argument('-p', '--port',nargs=2, default =[13,'offi'],help='two arguments needed:chooose one outlet of pdu then tske one action')
    parser.add_argument('-l', '--look',default=[],help="""look outlet status of PDU: one argument needed.\teg-->all:look all outlet status.-----------------1,2,3: look outlet1,outlet2 and outlet3 status""")
    parser.add_argument('-c', '--current', action='store_true', help='look current of PDU')
    parser.add_argument('-n', '--name', action='store_true', help='look name of PDU')
    options = parser.parse_args()

    pdu88 = pdu('192.168.1.' + options.dev) # IP
    if options.port==[13,'offi']:#without input of command line
       pass
    else:
        pdu88.SET(int(options.port[0]),options.port[1])

    if options.current== True:
       pdu88.GETcurrent()
       #exit()
    if options.name==True:
       pdu88.GETname()
       #exit()
    if options.look ==[]:
       pass
    elif options.look == 'all':
         pdu88.GEToutlet()
    else:
	option=options.look.split(',')
        pdu88.GEToutlet(option)
