#!/usr/bin/python

import subprocess
import time

########################################################################################
class rate_control(object):

    def __init__(self, ns_dict, margin_percent, short_time_const, long_time_const, freq):
        self.ns = None
        self.action_ports = list()
        self.ceil_bw =  list()
        self.cmn = list() # capacity - margin
        self.short_rate = list()
        self.long_rate = list()
        self.intfs = list()
        self.alp_short = 1.0 / (short_time_const *  freq)
        self.alp_long = 1.0 / (long_time_const *  freq)
        
        self.tflows = list() # tcp flows for data
        self.tfs_bytes = list()
        self.tfs_active = list()
        self.tfs_exist = list()
        self.uflows = list() # udp flows for video
        self.ufs_bytes = list()
        self.ufs_active = list()
        self.ufs_exist = list()
        
        items = subprocess.check_output('ovs-dpctl show', shell=True).split('\n')
        for i in ns_dict:
            t = i.keys()[0]
            self.intfs.append(t)
            idx = [j for j,x in enumerate(items) if x.find(t) != -1][0]
            self.action_ports.append(items[idx].split(' ')[1][:-1])
            bw = float(i[t]['bw'])
            self.ceil_bw.append(bw)
            self.cmn.append(bw * (1 - margin_percent))
            self.short_rate.append(bw / 2)
            self.long_rate.append(bw / 2)
            self.tflows.append(list())
            self.tfs_bytes.append(list())
            self.tfs_active.append(list())
            self.tfs_exist.append(list())
            self.uflows.append(list())
            self.ufs_bytes.append(list())
            self.ufs_active.append(list())
            self.ufs_exist.append(list())

    def add_networks_state(self, ns):
        self.ns = ns

    @staticmethod
    def between(s, d1, d2):
        t1 = s.find(d1) + 1
        t2 = s[t1:].find(d2)
        return s[t1:t1+t2]

    def update_flows(self, q_ni):
        # Enumerate and update flows
        
        #mark all existing flows as non-existing, in order to remove stale ones later on
        for i in range(len(self.action_ports)):
            for j in range(len(self.ufs_exist[i])):
                self.ufs_exist[i][j] = False
            for j in range(len(self.tfs_exist[i])):
                self.tfs_exist[i][j] = False
        
        items = subprocess.check_output('ovs-dpctl dump-flows', shell=True).split('\n')
        for pi, port in enumerate(self.action_ports):
            idcs = [j for j,y in enumerate(items) if y[y.rfind(':')+1:] == port]
            for idx in idcs:
                if items[idx].find('tcp') != -1:     # tcp flow
                    elems = items[idx].split(',')
                    #identify a flow by its 4-tuple
                    t = (rate_control.between(elems[5], '=', '/'),
                         rate_control.between(elems[6], '=', '/'),
                         elems[11][elems[11].find('=')+1:],
                         rate_control.between(elems[12], '=', ')'))
                    bytes = elems[14][elems[14].find(':')+1:]
                    if t in self.tflows[pi]:
                        t_idx = self.tflows[pi].index(t)
                        self.tfs_active[pi][t_idx] = (self.tfs_bytes[pi][t_idx] != bytes)
                        self.tfs_bytes[pi][t_idx] = bytes
                        self.tfs_exist[pi][t_idx] = True
                    else:
                        self.tflows[pi].append(t)
                        self.tfs_active[pi].append(True)
                        self.tfs_bytes[pi].append(bytes)
                        self.tfs_exist[pi].append(True)
                elif items[idx].find('udp') != -1:     # udp flow
                    elems = items[idx].split(',')
                    #identify a flow by its 4-tuple
                    t = (rate_control.between(elems[5], '=', '/'),
                         rate_control.between(elems[6], '=', '/'),
                         elems[11][elems[11].find('=')+1:],
                         rate_control.between(elems[12], '=', ')'))
                    bytes = elems[14][elems[14].find(':')+1:]
                    if t in self.uflows[pi]:
                        t_idx = self.uflows[pi].index(t)
                        self.ufs_active[pi][t_idx] = (self.ufs_bytes[pi][t_idx] != bytes)
                        self.ufs_bytes[pi][t_idx] = bytes
                        self.ufs_exist[pi][t_idx] = True
                    else:
                        self.uflows[pi].append(t)
                        self.ufs_bytes[pi].append(bytes)
                        self.ufs_active[pi].append(True)
                        self.ufs_exist[pi].append(True)
            #remove stale flows
            idcs = [j for j,y in enumerate(self.tfs_exist[pi]) if y == False]
            if idcs: # some has to be removed
                idcs = [j for j,y in enumerate(self.tfs_exist[pi]) if y == True]
                if idcs: # some has to be kept
                    self.tflows[pi][:] = \
                        [it for j, it in enumerate(self.tflows[pi]) if j in idcs]
                    self.tfs_bytes[pi][:] = \
                        [it for j, it in enumerate(self.tfs_bytes[pi]) if j in idcs]
                    self.tfs_active[pi][:] = \
                        [it for j, it in enumerate(self.tfs_active[pi]) if j in idcs]
                    self.tfs_exist[pi][:] = \
                        [it for j, it in enumerate(self.tfs_exist[pi]) if j in idcs]
                else:
                    self.tflows[pi][:] = list()
                    self.tfs_bytes[pi][:] = list()
                    self.tfs_active[pi][:] = list()
                    self.tfs_exist[pi][:] = list()
            idcs = [j for j,y in enumerate(self.ufs_exist[pi]) if y == False]
            if idcs: # some has to be removed
                idcs = [j for j,y in enumerate(self.ufs_exist[pi]) if y == True]
                if idcs: # some has to be kept
                    self.uflows[pi][:] = \
                        [it for j, it in enumerate(self.uflows[pi]) if j in idcs]
                    self.ufs_bytes[pi][:] = \
                        [it for j, it in enumerate(self.ufs_bytes[pi]) if j in idcs]
                    self.ufs_active[pi][:] = \
                        [it for j, it in enumerate(self.ufs_active[pi]) if j in idcs]
                    self.ufs_exist[pi][:] = \
                        [it for j, it in enumerate(self.ufs_exist[pi]) if j in idcs]
                else:
                    self.uflows[pi][:] = list()
                    self.ufs_bytes[pi][:] = list()
                    self.ufs_active[pi][:] = list()
                    self.ufs_exist[pi][:] = list()
        self.find_rates(q_ni)

        
    def find_rates(self, q_ni):
        for pi in range(len(self.action_ports)):
            i = self.ufs_active[pi].count(True) + 1
            ni = self.tfs_active[pi].count(True) + 1
            term = self.long_rate[pi] if q_ni[pi] > 0 else self.cmn[pi]
            self.short_rate[pi] += self.alp_short * (term - self.short_rate[pi])
            term = self.ceil_bw[pi] * i / (i + ni)
            self.long_rate[pi] += self.alp_long * (term - self.long_rate[pi])
            print ni, i, self.short_rate[pi], self.long_rate[pi]
        self.ns.append(self.short_rate)
        #set long rate
            



########################################################################################
def start_service():

    ns = list()

    #rate control
    ns_dict = [ {'s2-eth1': {'delay':60, 'bw': 5000 } }, 
                {'s4-eth2' : {'delay':80, 'bw': 5000 } } ]
    rc = rate_control(ns_dict, 0.1, 1, 5, 5)
    rc.add_networks_state(ns)
    q_ni = [0, 5]
    for i in range(10000000):
        rc.update_flows(q_ni)
        time.sleep(0.2)
        


########################################################################################
if __name__ == '__main__':
       start_service()
