#!/usr/bin/python

import asyncore, socket
import threading
import re
import collections
import time
import subprocess
import math
import cherrypy
import logging
import os
import math

from sys import argv, path

########################################################################################
GLOBAL_TIME_INTERVAL = 0.1

########################################################################################
class buffer_processor:
    ' process reception buffer '

    def __init__(self):
        self.buf = ''

    def add(self, new_buf):
        self.buf += new_buf

    def extract_line(self):
        t = self.buf.find('\r\n')
        if t != -1:
            s = self.buf[:t+2]
            self.buf = self.buf[t+2:]
            return s
        else:
            return ''

    def buf_len(self):
        return len(self.buf)

    def extract_len(self, length):
        t = self.buf[:length]
        self.buf = self.buf[length:]
        return t

    def extract_buf(self):
        t = self.buf
        self.flush_buf()
        return t
        
    def flush_buf(self):
        self.buf = ''

########################################################################################
class client(asyncore.dispatcher):

    def __init__(self, server, mutex):
        self.rx_buf = buffer_processor()
        self.mutex = mutex
        self.reset()
        self.server = server
        
    @staticmethod
    def combine_bs(lst, new_lst, last_idx):
        if lst != []:
            lst_end = int(lst[-1][0:lst[-1].find(',')])         #last index
            nlst_st = int(new_lst[0][0:new_lst[0].find(',')])    
            lst += new_lst[max(lst_end + 1 - nlst_st, 0):]
        elif new_lst != []:
            lst += new_lst
        del lst[:-neighbor_state.NB_QUEUE_SIZE]
        
    def handle_connect(self):
        print 'connected'
        self.closed = False

    def handle_close(self):
        print 'closed'
        self.close()
        self.reset()
#        self.start_connection()

    def handle_read(self):
        t = self.recv(8192)
        self.rx_buf.add(t)
#         self.mutex.acquire()
#         try:
        while self.rx_buf.buf_len():
            if not self.receiving_data:
                t = self.rx_buf.extract_line()
                while t != '':
                    if t == '\r\n':
                        if self.rx_buf.buf_len() >= self.data_size:
                            t = self.rx_buf.extract_len(self.data_size)
                            self.data_size = 0
                            states, last_idx, p = self.requests.popleft()
                            if t != '' and t != '[]' and t[0] == '[':
                                client.combine_bs(states[p], 
                                    t[2:-2].split('], ['), last_idx[p])
                                if states[p] != []:
                                    last_entry = states[p][-1]
                                    last_idx[p] = int(last_entry[0:last_entry.find(',')])
                        else:
                            self.receiving_data = True
                            return
                    s = t.find('Content-Length: ')
                    if s == 0: # Content length found
                        self.data_size = int(t[s+16:])
                    t = self.rx_buf.extract_line()
            else:
                if self.rx_buf.buf_len() >= self.data_size:
                    t = self.rx_buf.extract_len(self.data_size)
                    self.receiving_data = False
                    self.data_size = 0
                    states, last_idx, p = self.requests.popleft()
                    if t != '' and t != '[]' and t[0] == '[':
                        client.combine_bs(states[p], t[2:-2].split('], ['), last_idx[p])
                        if states[p] != []:
                            last_entry = states[p][-1]
                            last_idx[p] = int(last_entry[0:last_entry.find(',')])
                else:
                    return
#         finally: #the following line will always be executed
#             self.mutex.release()

    def writable(self):
        return (len(self.tx_buf) > 0)

    def handle_write(self):
        sent = self.send(self.tx_buf)
        self.tx_buf = self.tx_buf[sent:]

    def handle_error(self):
        print "problem reaching server."
        self.start_connection()

    def reset(self):
#         self.mutex.acquire()
        self.tx_buf = ''
        self.rx_buf.flush_buf() # flush buffer
        self.receiving_data = False
        self.data_size = 0
        self.requests = collections.deque()
        self.closed = True
#         self.mutex.release()

    def start_connection(self):
        print 'connecting to ' + self.server[0] + ':' + str(self.server[1])
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect( self.server )

    def request(self, s, mesg):
        self.requests.append(s)
        num_sent = self.send(mesg[:512])
        self.tx_buf += mesg[num_sent:]

########################################################################################
class neighbor_state:
    " A class to obtain network state every 50ms "

    # constants
    START_DELAY = 15 # 5s delayed start
    TIME_INTERVAL = GLOBAL_TIME_INTERVAL 
    NB_QUEUE_SIZE = 15 # 15 per state table

    def __init__(self, mutex):
        self.mutex = mutex
        self.clients = list()
        self.paths = []  # a list of lists
        self.states = []
        self.connected = False
        self.timer = threading.Timer(self.START_DELAY, self.run)
        self.timer.start()
        self.last_idx = []

    @staticmethod
    def start_thread():
        threading.Thread(target=asyncore.loop).start()
        
    def run(self):
#         self.timer = threading.Timer(self.TIME_INTERVAL, self.run)
#         self.timer.start()
        while (True):
            start_time = time.time()
#             self.mutex.acquire()
            if self.connected == False:
                for c in self.clients:
                    c.start_connection()
                self.connected = True
                neighbor_state.start_thread()
            for s in range(len(self.clients)):
                for p in range(len(self.paths[s])):
                    r1,r2 = self.paths[s][p]
                    self.clients[s].request( (self.states[s], self.last_idx[s], p), 
                        "GET /stats/"+r1+"/"+r2+"/"+str(self.last_idx[s][p])+
                        "/0/ HTTP/1.1\r\nHost: localhost\r\n\r\n")
#             self.mutex.release()
            time_diff = start_time + self.TIME_INTERVAL -  time.time()
            if time_diff > 0.01:
                time.sleep(time_diff)

    def add_path(self, server, path):
        # find if we know the server
        match = [i for i,x in enumerate(self.clients) if x.server == server]
        if not match:
            self.clients.append(client(server, self.mutex))
            idx = len(self.clients) - 1
            self.paths.append([])
            self.states.append([])
            self.last_idx.append([])
        else :
            idx = match[0]
        
        # add path if it is not in the servers list of paths
        match = [i for i,x in enumerate(self.paths[idx]) if x == path]
        if not match:
            self.paths[idx].append(path)
            self.states[idx].append(list())
            self.last_idx[idx].append(0)

########################################################################################
def reconfig_interfaces(ns_dict):

    for i in ns_dict:
        intf = i.keys()[0]
        twice_bw = str(i[intf]['bw']*2)+'kbit'
        bw = str(i[intf]['bw'])+'kbit'
        half_bw = str(i[intf]['bw']/2)+'kbit'
        
        # delete all configuration
        subprocess.call('sudo tc qdisc del dev ' + intf + ' root', shell=True)
        
        # This means the device is at root and uses 5: as a handle. any non 
        # classified traffic is assigned to class 5:20
        subprocess.call('sudo tc qdisc add dev ' + intf + ' root handle 5:'
                        ' htb default 20', shell=True)

        # create the branch 5:1 to have the maximum rate
        subprocess.call('sudo tc class add dev ' + intf + ' parent 5: classid 5:1'
                        ' htb rate ' + bw + ' ceil ' + bw, shell=True)
        
        # create two queues, each with its rate
        subprocess.call('sudo tc class add dev ' + intf + ' parent 5:1 classid 5:10'
                        ' htb rate ' + half_bw + ' ceil ' + bw, shell=True)
        subprocess.call('sudo tc class add dev ' + intf + ' parent 5:1 classid 5:20'
                        ' htb rate ' + half_bw + ' ceil ' + bw + ' prio 1', 
                        shell=True)

        # add delay so that we can see the number of queued bytes
        subprocess.call('sudo tc qdisc add dev ' + intf + ' parent 5:10 handle 10:'
                        ' netem delay 1us limit 250', shell=True)
        subprocess.call('sudo tc qdisc add dev ' + intf + ' parent 5:20 handle 20:'
                        ' netem delay 1us limit 250', shell=True)

        # define filters here
        # udp into 5:10, everything else goes into 5:20
        subprocess.call('sudo tc filter add dev ' + intf + ' protocol ip parent 5:'
                        ' u32 match ip protocol 17 0xff flowid 5:10', shell=True)

########################################################################################
def set_interactive_rate(intf, interactive_bw, ceil_bw):
    #change class rates here, bw and ceil_bw are assumed to be in kbits
    
    i_bw = str(interactive_bw) + 'kbit'
    ni_bw = str(ceil_bw - interactive_bw) + 'kbit'
    c_bw = str(ceil_bw) + 'kbit'
    os.system('bash change_rates.sh ' + intf + ' 10 ' + i_bw + ' ' + c_bw )
    os.system('bash change_rates.sh ' + intf + ' 20 ' + ni_bw + ' ' + c_bw )

#     cmd = 'bash '
#     cmd += 'sudo tc class change dev ' + intf + ' parent 5:1 classid 5:10'
# ' htb rate ' + i_bw + ' ceil ' + c_bw
#     cmd += '; '
#     cmd += 'sudo tc class change dev ' + intf + ' parent 5:1 classid 5:20'
# ' htb rate ' + ni_bw + ' ceil ' + c_bw
#     os.system(cmd)
    
#     subprocess.call('sudo tc class change dev ' + intf + ' parent 5:1 classid 5:10'
#                     ' htb rate ' + i_bw + ' ceil ' + c_bw, shell=True)
#     subprocess.call('sudo tc class change dev ' + intf + ' parent 5:1 classid 5:20'
#                     ' htb rate ' + ni_bw + ' ceil ' + c_bw, shell=True)

########################################################################################
def background_set_i_rate(intf, interactive_bw, ceil_bw):
    #set new bandwidth in the background
    threading.Thread(target = set_interactive_rate,
        kwargs = {'intf' : intf, 'interactive_bw' : interactive_bw, 'ceil_bw' : ceil_bw}
        ).start()

########################################################################################
class network_state:
    " A class to obtain network state every 50ms "

    # constants
    START_DELAY = 30 # 2.5s delayed start
    TIME_INTERVAL = GLOBAL_TIME_INTERVAL
    NS_QUEUE_SIZE = 15 # per state table
    REC_OFFSET = 2
    REC_SIZE = 5
    
    def __init__(self, mutex, this_subnet, dict, nb, rc):
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
        self.idx = 1
        self.last_time = time.time()
        self.regex = re.compile(r"qdisc\snetem\s+[0-9]+:\sdev\s([a-zA-Z0-9-]+)"
            "\s.*\slimit\s[0-9]+\sdelay\s([0-9.]+)[mu]"
            "s[a-zA-Z0-9_.:\s]+Sent\s([\d]+)\sbytes\s[\d]+\spkt\s\(dropped\s[\d]+"
            ",\soverlimits\s[\d]+\srequeues\s[\d]+\)\s*"
            "backlog\s([\dA-Z]+)b\s[\d]+p\srequeues\s[0-9]+")
        tc_output = subprocess.check_output( 'tc -s qdisc show', shell=True)
        tc_parse = self.regex.findall(tc_output)
        self.this_subnet = this_subnet.split('.')
        self.int_this_subnet = int(self.this_subnet[2])
        self.intf_dest = []
        self.intfs = []
        self.intfs_info = []
        self.files = []
        for i in dict:
            for j in tc_parse:
                if j[0] == i.keys()[0]:
                    d = i[j[0]]
                    intf_info = [int(j[2]), 0, d['bw'] / 2, d.get('delay')]
                    self.intf_dest.append(int(d['subnet'].split('.')[2]))
                    self.intfs.append(j[0])
                    self.intfs_info.append(intf_info)
                    self.files.append(open(j[0] + '.txt', 'w'))
                    break  # only one interface is for interactive traffic 
                           # the other one is for non-interactive traffic
        self.nb = nb
        self.rc = rc
        self.paths = list()
        self.states = list()
        self.last_entries = list()
        self.last_idx = list()
        self.timer = threading.Timer(self.START_DELAY, self.run)
        self.timer.start()

    @staticmethod
    def combine_entries(u_num, u, v_num, v, self_idx, last_entry, debug=False):
        entry = [self_idx, u_num+v_num]
        for i in range(0, u_num+v_num):
            entry.extend((0, 0, 0, 0, 0))
        if u_num != 0 and bool(u):
            for j in range(0, len(u)):
                t = u[j].split(', ')
                nr = (len(t) - network_state.REC_OFFSET) / network_state.REC_SIZE
                for i in range(0, nr):
                    idx1 = network_state.REC_OFFSET + i * network_state.REC_SIZE
                    entry[idx1]    = int(t[idx1])
                    entry[idx1+1] += int(t[idx1+1])
                    entry[idx1+2]  = int(t[idx1+2])
                    entry[idx1+3]  = int(t[idx1+3])
                    entry[idx1+4] = int(entry[idx1+4])+float(t[idx1+4])
        elif u_num != 0 and bool(last_entry):
            for i in range(0, u_num):
                idx = network_state.REC_OFFSET + i * network_state.REC_SIZE
                entry[idx]   = last_entry[idx]
                entry[idx+1] = 0
                entry[idx+2] = last_entry[idx+2]
                entry[idx+3] = last_entry[idx+3]
                entry[idx+4] = 0
        if v_num != 0 and bool(v):
            off = u_num * network_state.REC_SIZE
            for j in range(0, len(v)):
                t = v[j].split(', ')
                nr = (len(t) - network_state.REC_OFFSET) / network_state.REC_SIZE
                for i in range(0, nr):
                    idx1 = network_state.REC_OFFSET + i * network_state.REC_SIZE
#                     print t, entry, off, idx1
#                     print u_num, u, v_num, v, self_idx, last_entry
                    entry[off + idx1]      = int(t[idx1])
                    entry[off + idx1 + 1] += int(t[idx1 + 1])
                    entry[off + idx1 + 2]  = int(t[idx1 + 2])
                    entry[off + idx1 + 3]  = int(t[idx1 + 3])
                    entry[off + idx1 + 4] = int(entry[off+idx1+4])+float(t[idx1+4])
        elif v_num != 0 and bool(last_entry):
            off = u_num * network_state.REC_SIZE
            for i in range(0, v_num):
                idx = network_state.REC_OFFSET + i * network_state.REC_SIZE
                entry[off + idx]   = last_entry[off + idx]
                entry[off + idx+1] = 0
                entry[off + idx+2] = last_entry[off + idx+2]
                entry[off + idx+3] = last_entry[off + idx+3]
                entry[off + idx+4] = 0
        if debug:
            print entry
        return entry
    
    def run(self):
        #timer
#         self.timer = threading.Timer(self.TIME_INTERVAL, self.run)
#         self.timer.start()
        while (True):
            start_time = time.time()
            
#             self.mutex.acquire()
        
            # tc
            tc_output = subprocess.check_output( 'tc -s qdisc show', shell=True)
            tc_parse = self.regex.findall(tc_output)
            tc_parse = [i for i in tc_parse if i[0] in self.intfs]
        
            # update the states arising from tc
            t = time.time()
            delta = float(int(1000 * (t - self.last_time)))
            tt = t / 100 - math.floor(t / 100)
            tt = math.floor(tt * 100000) / 100000
            delta = delta + tt
            self.last_time = t
            new_entries = []
            ni_q = []
            for i in range(len(self.intfs)):
#                 t = int(tc_parse[i][2])
#                 transmitted = t - self.intfs_info[i][0]
#                 self.intfs_info[i][0] = t
#                 queued = tc_parse[i][3]
#                 if queued.endswith('K'):
#                     queued = queued[0:-1] + '000'
#                 elif queued.endswith('M'):
#                     queued = queued[0:-1] + '000000'
#                 queued = int(queued)
#                 new_entries.append((queued, transmitted,
#                     self.intfs_info[i][1], self.intfs_info[i][2], int(1000*delta)))
                t = int(tc_parse[2 * i][2])
                transmitted = t - self.intfs_info[i][0]
                self.intfs_info[i][0] = t
                queued = tc_parse[2 * i][3]
                if queued.endswith('K'):
                    queued = queued[0:-1] + '000'
                elif queued.endswith('M'):
                    queued = queued[0:-1] + '000000'
                queued = int(queued)
                new_entries.append((queued, transmitted,
                    self.intfs_info[i][2], self.intfs_info[i][3], delta))
                self.files[i].write(str(self.last_time)+' '+str(queued)+' '+str(transmitted)+' ')
                queued = tc_parse[2 * i + 1][3]
                if queued.endswith('K'):
                    queued = queued[0:-1] + '000'
                elif queued.endswith('M'):
                    queued = queued[0:-1] + '000000'
                ni_q.append(int(queued))
                t = int(tc_parse[2 * i + 1][2])
                transmitted = t - self.intfs_info[i][1]
                self.intfs_info[i][1] = t
                self.files[i].write(str(queued)+' '+str(transmitted)+'\n')
                self.files[i].flush()
        
            # ni_q must be used to set rates
            self.rc.update_flows(ni_q)
        
            #assemble all states
            hnet = self.this_subnet[0] + '.' + self.this_subnet[1] + '.' \
                + str(self.int_this_subnet+1) + '.0'
            cnet = self.this_subnet[0] + '.' + self.this_subnet[1] + '.' \
                + str(self.int_this_subnet) + '.0'
            lnet = self.this_subnet[0] + '.' + self.this_subnet[1] + '.' \
                + str(self.int_this_subnet-1) + '.0'

            #start with paths from the adjacent clients
            r_entries = [[] for i in range(len(self.intf_dest))]
            for i, val in enumerate(self.intf_dest):
                tnet = self.this_subnet[0]+'.'+self.this_subnet[1]+'.'+str(val)+'.0'
                t = (tnet, cnet)
                s = []
                for j in range(len(self.nb.clients)):
                    if t in self.nb.paths[j]:
                        idx = self.nb.paths[j].index(t)
                        s = self.nb.states[j][idx]
                        self.nb.states[j][idx] = []
                        if s != []:
                            idx = self.paths.index(t)
                            fi = int(s[0][:s[0].find(',')]) #first index
                            li = int(s[-1][:s[-1].find(',')]) # last index
                            # li - self.last_idx[i] last elements
                            s = s[self.last_idx[idx]-li:]
                            if s != []:
                                self.last_idx[idx] = li
                    r_entries[i] = s
            #other paths
            for i, path in enumerate(self.paths):
                obj_src = int(path[0].split('.')[2])
                obj_dst = int(path[1].split('.')[2])
                assert obj_src == self.int_this_subnet or obj_dst == self.int_this_subnet
                if obj_src < self.int_this_subnet:
                    #neighbor's list
                    num_sw = self.int_this_subnet - obj_src
                    u = []
                    v = []
                    # from low to this_subnet - 1
                    t = (path[0], lnet)
                    if path[0] != lnet:
                        for j in range(len(self.nb.clients)):
                            if t in self.nb.paths[j]:
                                idx = self.nb.paths[j].index(t)
                                u = self.nb.states[j][idx]
                                self.nb.states[j][idx] = []
                                if u != []:
                                    fi = int(u[0][:u[0].find(',')]) #first index
                                    li = int(u[-1][:u[-1].find(',')]) # last index
                                    # li - self.last_idx[i] last elements
                                    u = u[self.last_idx[i]-li:]
                                    if u != []:
                                        self.last_idx[i] = li
                    # from r_entries, this_subnet - 1 to this_subnet
                    idx = self.intf_dest.index(self.int_this_subnet - 1)
                    v = r_entries[idx]
                    entry = network_state.combine_entries(num_sw-1, u, 1, v, self.idx, \
                        self.last_entries[i])
                    self.last_entries[i] = entry
                    self.states[i].append(entry)
                    del self.states[i][:-self.NS_QUEUE_SIZE]
                elif obj_src > self.int_this_subnet:
                    #neighbor's list
                    num_sw = obj_src - self.int_this_subnet
                    u = []
                    v = []
                    # from high to this_subnet + 1
                    t = (path[0], hnet)
                    if path[0] != hnet:
                        for j in range(len(self.nb.clients)):
                            if t in self.nb.paths[j]:
                                idx = self.nb.paths[j].index(t)
                                u = self.nb.states[j][idx]
                                self.nb.states[j][idx] = []
                                if u != []:
                                    fi = int(u[0][:u[0].find(',')]) #first index
                                    li = int(u[-1][:u[-1].find(',')]) # last index
                                    # li - self.last_idx[i] last elements
                                    u = u[self.last_idx[i]-li:]
                                    if u != []:
                                        self.last_idx[i] = li
                    # from r_entries, this_subnet + 1 to this_subnet
                    idx = self.intf_dest.index(self.int_this_subnet + 1)
                    v = r_entries[idx]
                    entry = network_state.combine_entries(num_sw-1, u, 1, v, self.idx, \
                        self.last_entries[i])
                    self.last_entries[i] = entry
                    self.states[i].append(entry)
                    del self.states[i][:-self.NS_QUEUE_SIZE]
                elif obj_dst < self.int_this_subnet:
                    #this one then neighbor's list
                    num_sw = self.int_this_subnet - obj_dst
                    u = []
                    v = []
                    # from this_subnet to this_subnet - 1
                    idx = self.intf_dest.index(self.int_this_subnet - 1)
                    v = [0, 1]
                    v.extend(new_entries[idx])
                    v = [str(v)[1:-1]]
                    # from this_subnet - 1 to low
                    t = (lnet, path[1])
                    if path[1] != lnet:
                        for j in range(len(self.nb.clients)):
                            if t in self.nb.paths[j]:
                                idx = self.nb.paths[j].index(t)
                                u = self.nb.states[j][idx]
                                self.nb.states[j][idx] = []
                                if u != []:
                                    fi = int(u[0][:u[0].find(',')]) #first index
                                    li = int(u[-1][:u[-1].find(',')]) # last index
                                    # li - self.last_idx[i] last elements
                                    u = u[self.last_idx[i]-li:]
                                    if u != []:
                                        self.last_idx[i] = li
                    entry = network_state.combine_entries(1, v, num_sw-1, u, self.idx, \
                        self.last_entries[i])
                    self.last_entries[i] = entry
                    self.states[i].append(entry)
                    del self.states[i][:-self.NS_QUEUE_SIZE]
                elif obj_dst > self.int_this_subnet:
                    #this one then neighbor's list
                    num_sw = obj_dst - self.int_this_subnet
                    u = []
                    v = []
                    # from this_subnet to this_subnet + 1
                    idx = self.intf_dest.index(self.int_this_subnet + 1)
                    v = [0, 1]
                    v.extend(new_entries[idx])
                    v = [str(v)[1:-1]]
                    # from this_subnet + 1 to high
                    t = (hnet, path[1])
                    if path[1] != hnet:
                        for j in range(len(self.nb.clients)):
                            if t in self.nb.paths[j]:
                                idx = self.nb.paths[j].index(t)
                                u = self.nb.states[j][idx]
                                self.nb.states[j][idx] = []
                                if u != []:
                                    fi = int(u[0][:u[0].find(',')]) #first index
                                    li = int(u[-1][:u[-1].find(',')]) # last index
                                    # li - self.last_idx[i] last elements
                                    u = u[self.last_idx[i]-li:]
                                    if u != []:
                                        self.last_idx[i] = li
                    entry = network_state.combine_entries(1, v, num_sw-1, u, self.idx, \
                        self.last_entries[i])
                    self.last_entries[i] = entry
                    self.states[i].append(entry)
                    del self.states[i][:-self.NS_QUEUE_SIZE]
                else:
                    assert 0
            self.idx += 1
#             self.mutex.release()
            time_diff = start_time + self.TIME_INTERVAL -  time.time()
            if time_diff > 0.01:
                time.sleep(time_diff)
    
    def update_reported_bw(self, intf, short_rate):
        idx = self.intfs.index(intf)
        self.intfs_info[idx][2] = int(short_rate)

    def add_path(self, path):
        # add path if it is not in the servers list of paths
        if not path in self.paths:
            self.paths.append(path)
            self.states.append(list())
            self.last_entries.append(list())
            self.last_idx.append(0)

    def terminate(self):
        self.timer.cancel()

########################################################################################
class rate_control(object):

    ZERO_Q_CNT = 3  #the queued bytes has to be zero for ZERO_Q_CNT before
                    # the queue is considered idle
    ZERO_D_CNT = 20 #the transmitted bytes has to be zero for ZERO_D_CNT 
                    # before the flow is considered idle
                    # 20 is chosen because it is equivalent to 2 seconds.
                    # With a buffer that can hold 250 packets
                    # a rate of 5/3 Mbps, and a packet of 1514 bytes,
                    # we less than 2 seconds worth of buffer.
                    # we have to do this because we cannot check if a flow
                    # has queued packets.

    def __init__(self, ns_dict, margin_percent, short_time_const, long_time_const, freq,
                 skip):
        self.ns = None
        self.action_ports = list()
        self.qni_cnt = list()
        self.ceil_bw =  list()
        self.cmn = list() # capacity - margin
        self.short_rate = list()
        self.long_rate = list()
        self.intfs = list()
        self.alp_short = min(1.0, 1.0 / (short_time_const *  freq / skip))
        self.alp_long = min(1.0, 1.0 / (long_time_const *  freq / skip))
        self.skip = skip
        self.skip_cnt = 0
        
        self.tflows = list() # tcp flows for data
        self.tfs_bytes = list()
        self.tfs_active = list()
        self.tfs_exist = list()
        self.uflows = list() # udp flows for video
        self.ufs_bytes = list()
        self.ufs_active = list()
        self.ufs_exist = list()
        self.files = list()
        
        items = subprocess.check_output('ovs-dpctl show', shell=True).split('\n')
        idxx = 0
        for i in ns_dict:
            t = i.keys()[0]
            self.intfs.append(t)
            idx = [j for j,x in enumerate(items) if x.find(t) != -1][0]
            self.action_ports.append(items[idx].split(' ')[1][:-1])
            self.qni_cnt.append(self.ZERO_Q_CNT);
            bw = float(i[t]['bw'])
            self.ceil_bw.append(bw)
            self.cmn.append(bw * (1 - margin_percent))
            self.short_rate.append(bw / 2)
            self.long_rate.append(list())
            self.long_rate[idxx].extend([bw/2, bw/2, bw/2, bw/2])
            self.tflows.append(list())
            self.tfs_bytes.append(list())
            self.tfs_active.append(list())
            self.tfs_exist.append(list())
            self.uflows.append(list())
            self.ufs_bytes.append(list())
            self.ufs_active.append(list())
            self.ufs_exist.append(list())
            self.files.append(open(t + '_rate.txt', 'w'))
            idxx += 1

    def add_networks_state(self, ns):
        self.ns = ns

    @staticmethod
    def between(s, d1, d2):
        t1 = s.find(d1) + 1
        t2 = s[t1:].find(d2)
        return s[t1:t1+t2]

    def update_flows(self, q_ni):
        # Enumerate and update flows
        
        # reduce the frequency of running this code
        self.skip_cnt += 1
        if self.skip_cnt < self.skip:
            return
        self.skip_cnt = 0
        
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
                        self.tfs_active[pi][t_idx] = 0 if (self.tfs_bytes[pi][t_idx] != bytes) else self.tfs_active[pi][t_idx] + 1
                        self.tfs_bytes[pi][t_idx] = bytes
                        self.tfs_exist[pi][t_idx] = True
                    else:
                        self.tflows[pi].append(t)
                        self.tfs_active[pi].append(0)
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
                        self.ufs_active[pi][t_idx] = 0 if (self.ufs_bytes[pi][t_idx] != bytes) else self.ufs_active[pi][t_idx] + 1
                        self.ufs_bytes[pi][t_idx] = bytes
                        self.ufs_exist[pi][t_idx] = True
                    else:
                        self.uflows[pi].append(t)
                        self.ufs_active[pi].append(0)
                        self.ufs_bytes[pi].append(bytes)
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
            i = len([x for x in self.ufs_active[pi] if x < self.ZERO_D_CNT]) + 1
            ni = len([x for x in self.tfs_active[pi] if x < self.ZERO_D_CNT]) + 1
            self.qni_cnt[pi] = self.qni_cnt[pi]+1 if q_ni[pi] == 0 else 0
            term1 = self.long_rate[pi][0] if self.qni_cnt[pi] < self.ZERO_Q_CNT else self.cmn[pi]
            self.short_rate[pi] += self.alp_short * (term1 - self.short_rate[pi])
            term2 = self.ceil_bw[pi] * i / (i + ni)
            self.long_rate[pi][0] += self.alp_long * (term2 - self.long_rate[pi][0])
            #update network state
            self.ns.update_reported_bw(self.intfs[pi], self.short_rate[pi])
            #change network settings
            set_interactive_rate(self.intfs[pi], self.long_rate[pi][0], self.ceil_bw[pi])
            self.files[pi].write(str(time.time())+' '+str(i)+' '+str(ni)+' '+str(term2)+' '+str(self.long_rate[pi][0])+' '+str(term1)+' '+str(self.short_rate[pi])+'\n')
#            self.long_rate[pi][3] = self.long_rate[pi][2]
#            self.long_rate[pi][2] = self.long_rate[pi][1]
#            self.long_rate[pi][1] = self.long_rate[pi][0]

#######################################################################################
class rest_reply(object):
    " A class to prepare and send network state replys "
    
    def __init__(self, mutex, ip, ns, nb):
        self.mutex = mutex
        self.subnet = int(ip.split('.')[2])
        self.ns = ns
        self.nb = nb
    
    def _cp_dispatch(self, vpath):
        if len(vpath) == 5 and vpath[0] == 'stats':
            cherrypy.request.params[ 'max_entries' ] = vpath.pop()
            cherrypy.request.params[ 'oldest_idx' ] = vpath.pop()
            cherrypy.request.params[ 'dst_ip' ] = vpath.pop()
            cherrypy.request.params[ 'src_ip' ] = vpath.pop()
            vpath.pop()
            return self
        return vpath
    
    @cherrypy.expose
    def index(self, src_ip, dst_ip, oldest_idx, max_entries):
        src_ip = src_ip[0:argv[0].rfind('.')] + '0'
        dst_ip = dst_ip[0:argv[0].rfind('.')] + '0'
        
#         self.mutex.acquire()
        
        # convert to integers
        oldest_idx = int(oldest_idx)
        max_entries = int(max_entries)

        # get source and destination ips
        t = 'Unknown path'
        p = (src_ip, dst_ip)
        if p in self.ns.paths:
            idx = self.ns.paths.index(p)
            s = self.ns.states[idx]
            l = len(s)
            t = 'No data yet'
            if l != 0:
                oldest_idx = max(s[0][0], oldest_idx)
                max_entries = l if max_entries == 0 else max_entries
                num_entries = s[l-1][0] - oldest_idx + 1
                num_entries = min(num_entries, max_entries)
                t = str(s[-num_entries:])
#         self.mutex.release()            
        return t

########################################################################################
def start_service(argv):

    # about this network
    base_ip = argv[0][0:argv[0].rfind('.')] # the first three octets
    first_two_octets = base_ip[0:base_ip.rfind('.')] # first two octets    
    this_subnet = int(base_ip[base_ip.rfind('.')+1:]) # third octet as int

    mutex = threading.Lock()
    
    # neighbor_state
    nb = neighbor_state(mutex)
    if this_subnet > 11:
        contr_ip = first_two_octets + '.' + str(this_subnet+10-1) + '.100'
        d = first_two_octets + '.' + str(this_subnet) + '.0'
        s = first_two_octets + '.' + str(this_subnet-1) + '.0'
        nb.add_path( (contr_ip, 8080), (s,d) )
        d = s
        for i in range(this_subnet-2, 10, -1):
            s = first_two_octets + '.' + str(i) + '.0'
            nb.add_path( (contr_ip, 8080), (s,d) )
            nb.add_path( (contr_ip, 8080), (d,s) )
    if this_subnet < 14:
        contr_ip = first_two_octets + '.' + str(this_subnet+10+1) + '.100'
        d = first_two_octets + '.' + str(this_subnet) + '.0'
        s = first_two_octets + '.' + str(this_subnet+1) + '.0'
        nb.add_path( (contr_ip, 8080), (s,d) )
        d = s
        for i in range(this_subnet+2, 15):
            d = first_two_octets + '.' + str(i) + '.0'
            nb.add_path( (contr_ip, 8080), (s,d) )
            nb.add_path( (contr_ip, 8080), (d,s) )
    print 'Finished running neighbor_state'

    # network_state
    s1 = first_two_octets + '.' + str(this_subnet-1) + '.0'
    s2 = first_two_octets + '.' + str(this_subnet+1) + '.0'
    # delay and bandwidth need to match that in one_stage
    ns_dict = [ {'s2-eth1': {'delay':50, 'bw': 5000, 'subnet':s1 } }, 
                {'s4-eth2' : {'delay':50, 'bw': 5000, 'subnet':s2 } } ]
    #change interfaces configuration
    reconfig_interfaces(ns_dict)
    # configure rate_control
    rc = rate_control(ns_dict, 0.1, 0.3, 2, 1.0 / GLOBAL_TIME_INTERVAL, 1)
    #state network_state
    s = first_two_octets + '.' + str(this_subnet) + '.0'
    ns = network_state( mutex, s, ns_dict, nb, rc )
    rc.add_networks_state(ns)
    for i in range(11,15):
        if i != this_subnet:
            d = first_two_octets + '.' + str(i) + '.0'
            ns.add_path((s, d))
            ns.add_path((d, s))
    print 'Finished running network_state'

    # http server
    logging.getLogger("cherrypy").propagate = False
    logging.basicConfig(level=logging.INFO, format="%(asctime)s.%(msecs)03d "
        "[%(levelname)s] (%(name)s) %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    http_ip = first_two_octets + '.' + str(this_subnet+10) + '.100'
    cherrypy.config.update({ 'global': {
            'environment': 'production',
            'log.screen': False,
#            'log.access_file': os.path.join(os.getcwd(), 'access.log'),
#            'log.error_file': os.path.join(os.getcwd(), 'error.log'),
            'engine.autoreload.on': False,
            'server.socket_host': http_ip,
            'server.socket_port': 8080,
            'server.thread_pool' : 100
    }})
    cherrypy.quickstart(rest_reply(mutex, base_ip+'.0', ns, nb))
    print 'Finished running cherrypy server'

########################################################################################
if __name__ == '__main__':
    if len(argv) != 2:
        print ('Please specify subnet')
    else:
       start_service(argv[1:])

########################################################################################
# if __name__ == '__main__':
#     mutex = threading.Lock()
#     nb = neighbor_state(mutex)
#     nb.add_path(('192.168.21.100', 8080), ('192.168.10.2','192.168.13.3') )
#     asyncore.loop()

########################################################################################
# if __name__ == '__main__':
#     mutex = threading.Lock()
#     ns_dict = [ {'s2-eth1': {'delay':60.0, 'bw': 5, 'subnet':'192.168.10.0'} }, 
#                 {'s4-eth2' : {'delay':80.0, 'bw': 5, 'subnet':'192.168.12.0'} } ]
#     ns = network_state( mutex, ns_dict )
# 
#     # http server
#     logging.getLogger("cherrypy").propagate = False
#     logging.basicConfig(level=logging.INFO, format="%(asctime)s.%(msecs)03d "
#         "[%(levelname)s] (%(name)s) %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
#     cherrypy.config.update({
#             'environment': 'production',
#             'server.socket_port': 2400,
#             'log.screen': False,
#             'log.access_file': os.path.join(os.getcwd(), 'access.log'),
#             'log.error_file': os.path.join(os.getcwd(), 'error.log')
#     })
# 
#     conf = {'global' : {'server.socket_host': '192.168.21.100',
#                         'server.socket_port': 8080} }
#     cherrypy.quickstart(rest_reply(mutex, '192.168.11.0'), config=conf)
