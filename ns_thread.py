#!/usr/bin/python

"""
    A thread for collecting network statistics using tc
    Here we keep a small number of the latest sample

"""

import threading
import time
import re
import subprocess
import math
import cherrypy
import logging
import os

########################################################################################
class network_state:
    " A class to obtain network state every 50ms "

    # constants
    START_DELAY = 2.5 # 3s delayed start
    TIME_INTERVAL = 0.05 # 50ms intervals
    NS_QUEUE_SIZE = 5 # three networks, 100 for each

    def __init__(self, mutex, dict):
        # init network state here
        # mutex is used to lock access to state while it is being used
        # self.ns: this is where network state is stored
        # args pass switch interfaces of interest in the form of a list of 
        # dictionaries; each dictionary uses an interface name as a key.
        # The value that corresponds to this key is a dictionary that has the 
        # following keys:
        #   bw: the bandwidth for this interface
        #   delay: (optional) the interface at which delay can be obtained
        self.mutex = mutex
        self.timer = threading.Timer(self.START_DELAY, self.run)
        self.timer.start()
        self.ns = list()
        self.idx = 0
        self.last_time = time.time()
        self.regex = re.compile(r"qdisc\snetem\s+[0-9]+:\sdev\s([a-zA-Z0-9-]+)"
            "\s.*\slimit\s[0-9]+\sdelay\s([0-9.]+)[mu]"
            "s[a-zA-Z0-9_.:\s]+Sent\s([\d]+)\sbytes\s[\d]+\spkt\s\(dropped\s[\d]+"
            ",\soverlimits\s[\d]+\srequeues\s[\d]+\)\s*"
            "backlog\s([\dA-Z]+)b\s[\d]+p\srequeues\s[0-9]+")
        tc_output = subprocess.check_output( 'tc -s qdisc show', shell=True)
        tc_parse = self.regex.findall(tc_output)
        self.entries = []
        for i in dict:
            for j in tc_parse:
                if j[0] == i.keys()[0]:
                    d = i[j[0]]
                    delay = 0
                    subnet = d['subnet']
                    delay = float(d.get('delay'))
                    entry = (j[0], subnet, int(j[3]), int(j[2]), d['bw'], delay)
            self.entries.append(entry)

    def run(self):
        #timer
        self.timer = threading.Timer(self.TIME_INTERVAL, self.run)
        self.timer.start()
        
        # tc
        tc_output = subprocess.check_output( 'tc -s qdisc show', shell=True)
        tc_parse = self.regex.findall(tc_output)
        
        # update ns
        t = time.time()
        delta = t - self.last_time
        entry = [self.idx]
        for i in self.entries:
            for j in tc_parse:
                if j[0] == i[0]:
                    entry.append((i[1], int(j[3]), int(j[2]), i[4], i[5], delta))
        self.mutex.acquire()
        self.ns.append(entry)
        if len(self.ns) > self.NS_QUEUE_SIZE:
            self.ns.pop(0)
        self.mutex.release()
        self.last_time = t
        self.idx += 1

    def terminate(self):
        self.timer.cancel()

#######################################################################################
class rest_reply(object):
    " A class to prepare and send network state replys "
    
    def __init__(self, mutex, ip):
        self.mutex = mutex
        self.subnet = int(ip.split('.')[2])
        self.paths = list()
        pass
    
    def _cp_dispatch(self, vpath):
        if len(vpath) == 5 and vpath[0] == 'stats':
            cherrypy.request.params[ 'requester_ip' ] = cherrypy.request.remote.ip
            cherrypy.request.params[ 'max_entries' ] = vpath.pop()
            cherrypy.request.params[ 'oldest_idx' ] = vpath.pop()
            cherrypy.request.params[ 'dst_ip' ] = vpath.pop()
            cherrypy.request.params[ 'src_ip' ] = vpath.pop()
            vpath.pop()
            return self
        return vpath
    
    @cherrypy.expose
    def index(self, src_ip, dst_ip, oldest_idx, max_entries, requester_ip):
        src_subnet = int(src_ip.split('.')[2])
        dst_subnet = int(dst_ip.split('.')[2])
        oldest_idx = int(oldest_idx)
        max_entries = int(max_entries)
        self.mutex.acquire()
        #merge neighbors state with network state
        #extract request data
        l = len(ns.ns)
        oldest_idx = max(ns.ns[0][0], oldest_idx)
        max_entries = l if max_entries == 0 else max_entries
        num_entries = ns.ns[l-1][0] - oldest_idx + 1
        num_entries = min(num_entries, max_entries)
        self.mutex.release()
        if src_subnet < dst_subnet:
            new_list = list()        
            if self.subnet >= src_subnet and self.subnet < dst_subnet:
                for i in ns.ns[-num_entries:]:
                    entry = []
                    for j in range(2, len(i)):
                        subnet = int(i[j][0].split('.')[2])
                        if subnet > self.subnet:
                            if entry == []:
                                entry = [i[0], 0]
                            entry += list(i[j][1:-1]) + [round(i[j][-1], 3)]
                            entry[1] += 1
                    if entry != []:        
                        new_list.append(entry)
            return str(new_list)
        elif src_subnet > dst_subnet:
            new_list = list()
            if self.subnet <= src_subnet and self.subnet > dst_subnet:
                for i in ns.ns[-num_entries:]:
                    entry = []
                    for j in range(2, len(i)):
                        subnet = int(i[j][0].split('.')[2])
                        if subnet < self.subnet:
                            if entry == []:
                                entry = [i[0], 0]
                            entry += list(i[j][1:-1]) + [round(i[j][-1], 3)]
                            entry[1] += 1
                    if entry != []:        
                        new_list.append(entry)
            return str(new_list)
        else:
            return str(list())

########################################################################################
if __name__ == '__main__':
    mutex = threading.Lock()
    ns_dict = [ {'s2-eth1': {'delay':60.0, 'bw': 5, 'subnet':'192.168.10.0'} }, 
                {'s4-eth2' : {'delay':80.0, 'bw': 5, 'subnet':'192.168.12.0'} } ]
    ns = network_state( mutex, ns_dict )

    # http server
    logging.getLogger("cherrypy").propagate = False
    logging.basicConfig(level=logging.INFO, format="%(asctime)s.%(msecs)03d "
        "[%(levelname)s] (%(name)s) %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    cherrypy.config.update({ 'global': {
            'environment': 'production',
            'log.screen': False,
            'log.access_file': os.path.join(os.getcwd(), 'access.log'),
            'log.error_file': os.path.join(os.getcwd(), 'error.log'),
            'engine.autoreload.on': False,
            'server.socket_host': '192.168.21.100',
            'server.socket_port': 8080            
    }})

    cherrypy.quickstart(rest_reply(mutex, '192.168.11.0'))


########################################################################################
# originals
#
# NETEM_KEYS = ['RootNo','Dev','Parent','Q_Depth','P_Delay','SentB','SentP','DroppedP',
#               'OverlimitsB','Requeues','BackB','BackP']
# and you might add the requeues entry as well
#
# self.regex = re.compile(r"qdisc\snetem\s+([0-9]+):\sdev\s([a-zA-Z0-9-]+)\s"
#    "parent\s([0-9]+:[0-9]+)\slimit\s([0-9]+)\sdelay\s([0-9.]+)[mu]s"
#    "[a-zA-Z0-9_.:\s]+Sent\s([\d]+)\sbytes\s([\d]+)\spkt\s\(dropped\s([\d]+),"
#    "\soverlimits\s([\d]+)\srequeues\s([\d]+)\)\s*backlog\s([\dA-Z]+)b\s([\d]+)p")



