#!/usr/bin/env python
import sys
import base64
import httplib
import urllib
import urllib2

action_dict = {
               'none':   1,
               'on':     2,
               'off':    4,
               'reboot': 7,
              }

def run(ip, ports, action='none'):
    url = ip
    option = action_dict[action]
    port = 80
    timeout = 30 # second
    username = 'apc'
    password = 'apc'
    ctrl1 = [('HX', ''), ('HX2', ''), ('C2', 'C2'), ('rPDUOutletCtrl', option)]
    for p in ports:
        ctrl1.append(('OL_Cntrl_Col1_Btn', '?%d,2' % (p + 1)))
    ctrl1.append(('Submit', 'Next >>'))
    ctrl1 = tuple(ctrl1)
    ctrl2 = {
              'HX': '',
              'HX2': '',
              'C2': 'C2',
              'Control': '',
              'Submit': 'Apply',
             }

    # http request
    httpClient = None
    try:
        params = urllib.urlencode(ctrl1)
        auth = base64.b64encode('%s:%s' % (username, password)).decode("ascii")
        basic_auth = "Basic %s" % auth,
        headers = {
                   "Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain",
                   "Authorization": basic_auth
                  }
        httpClient = httplib.HTTPConnection(url, port, timeout=timeout)

        # first request
        httpClient.request("POST", "/Forms/rPDUout1", params, headers)
        response = httpClient.getresponse()
        # it may make one request with no authentication first
        # see https://josephscott.org/archives/2011/06/http-basic-auth-with-httplib2/
        if response.status == 401:
            httpClient.request("POST", "/Forms/rPDUout1", params, headers)
            response = httpClient.getresponse()
        # print response.status
        # print response.reason
        assert response.status == 303, 'Error occured during request'
        response.read()
        ret = response.getheaders()

        # open the generated page
        # req = urllib2.Request("http://192.168.1.88/rPDUoconf.htm")
        req = urllib2.Request(dict(ret)['location'])
        req.add_header("Authorization", basic_auth)
        res = urllib2.urlopen(req)
        # Read from the object, storing the page's contents in 's'.
        s = res.read()
        # print s
        res.close()

        # second request
        params = urllib.urlencode(ctrl2)
        httpClient = httplib.HTTPConnection(url, port, timeout=30)
        httpClient.request("POST", "/Forms/rPDUoconf1", params, headers)
        response = httpClient.getresponse()
        if response.status == 401:
            httpClient.request("POST", "/Forms/rPDUout1", params, headers)
            response = httpClient.getresponse()
        # print response.status
        # print response.reason
        assert response.status == 303, 'Error occured during request'
        response.read()
        ret = response.getheaders()

        # open the generated page
        # req = urllib2.Request("http://192.168.1.88/rPDUout.htm")
        req = urllib2.Request(dict(ret)['location'])
        req.add_header("Authorization", basic_auth)
        res = urllib2.urlopen(req)
        # Read from the object, storing the page's contents in 's'.
        s = res.read()
        # print s
        res.close()

    except Exception, e:
        print e
    finally:
        if httpClient:
            httpClient.close()

if __name__ == '__main__':
    # python pdu.py ip ports action
    if sys.argv[2] == '1-16':
        ports = range(1,17)
    else:
        ports = list(map(int, sys.argv[2].split(',')))
    # ip = "192.168.1.88"
    pdu_ip = "192.168.1." + sys.argv[1]
    #ports = range(1,17)
    #ports = [2,10]
    action = sys.argv[3]
    #action = 'reboot'
    #action = 'none'
    #action = 'off'
    #action = 'on'
    run(pdu_ip, ports, action)

