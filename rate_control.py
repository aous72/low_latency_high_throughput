#!/usr/bin/python

import subprocess


########################################################################################
class rate_control(object):

    def __init__(self, ns_dict):
        self.ns = None
        self.switches = list()
        self.max_bw =  list()
        self.outport = list()
        self.udp_flows = list() # udp flows for video
        self.tcp_flows = list() # tcp flows for data
        for i in ns_dict:
            t = i.keys()[0]
            u = t.split('-')
            self.switches.append(u[0])
            self.outport.append(u[1][-1])
            self.max_bw.append(i[t]['bw'])

    def add_networks_state(self, ns):
        self.ns = ns

    def update_flows(self):
        for i, x in enumerate(self.switches):
            cmdline = 'sudo ovs-ofctl dump-flows ' + x
            result = subprocess.check_output(cmdline, shell=True)
            for item in result.split('\n'):
                elem = item.split(',')
                if len(elem)<=9:
                    pass
                elif elem[8]=='tcp':
                    t = elem[-1][-1]
                    if t == self.output[i]:
                        print item
                elif elem[8]=='udp':
                    if t == self.output[i]:
                        print item

    def configure_flows():
        pass

########################################################################################
def start_service():

    ns = list()

    #rate control
    ns_dict = [ {'s2-eth1': {'delay':60, 'bw': 5000 } }, 
                {'s4-eth2' : {'delay':80, 'bw': 5000 } } ]
#     rc_dict = [ {'s2' : {'bw': 5000, 'ip_port' = '1'} }, 
#                 {'s4' : {'bw': 5000, 'ip_port' = '2'} ]
    rc = rate_control(ns_dict)
    rc.add_networks_state(ns)
    rc.update_flows()


########################################################################################
if __name__ == '__main__':
       start_service()
