#!/usr/bin/python

import asyncore, socket
import threading
import re
import collections
from operator import itemgetter

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

    def extract_buf(self):
        t = self.buf
        self.flush_buf()
        return t
        
    def flush_buf(self):
        self.buf = ''

########################################################################################
def combine(lst, new_lst):
    ls = len(lst)
    lt = len(new_lst)
    if ls != 0 and lt != 0:
        lst_st = int(lst[0][0:lst[0].find(',')])         #first index
        nlst_st = int(new_lst[0][0:new_lst[0].find(',')])    
        lst += new_lst[max(lst_st + ls - nlst_st, 0):]
    else:
        lst += new_lst
    del lst[:-neighbor_state.NB_QUEUE_SIZE]
    print new_lst

########################################################################################
class client(asyncore.dispatcher):

    def __init__(self):
        asyncore.dispatcher.__init__(self)
        self.rx_buf = buffer_processor()
        self.reset()
        
    def handle_connect(self):
        self.closed = False

    def handle_close(self):
        self.close()
        self.reset()

    def handle_read(self):
        t = self.recv(8192)
        self.rx_buf.add(t)
        if not self.receiving_data:
            t = self.rx_buf.extract_line()
            while t != '':
                if t == '\r\n':
                    if self.rx_buf.buf_len() == self.data_size:
                        t = self.rx_buf.extract_buf()
                        self.data_size = 0
                        s = self.requests.popleft()
                        combine(s, t[2:-2].split('], ['))
                    else:
                        self.receiving_data = True
                        return
                s = t.find('Content-Length: ')
                if s == 0: # Content length found
                    self.data_size = int(t[s+16:])
                t = self.rx_buf.extract_line()
        else:
            if self.rx_buf.buf_len() == self.data_size:
                t = self.rx_buf.extract_buf()
                self.receiving_data = False
                self.data_size = 0
                s = self.requests.popleft()
                combine(s, t[2:-2].split('], ['))

    def writable(self):
        return (len(self.tx_buf) > 0)

    def handle_write(self):
        sent = self.send(self.tx_buf)
        self.tx_buf = self.tx_buf[sent:]

    def reset(self):
        self.tx_buf = ''
        self.rx_buf.flush_buf() # flush buffer
        self.receiving_data = False
        self.data_size = 0
        self.requests = collections.deque()
        self.closed = True

    def start_connection(self, server):
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect( server )
        self.server = server

    def request(self, s, mesg):
        self.requests.append(s)
        num_sent = self.send(mesg[:512])
        self.tx_buf += mesg[num_sent:]

########################################################################################
class neighbor_state:
    " A class to obtain network state every 50ms "

    # constants
    START_DELAY = 0.5 # 3s delayed start
    TIME_INTERVAL = 0.05 # 50ms intervals
    NB_QUEUE_SIZE = 5 # three networks, 100 for each

    def __init__(self, mutex):
        self.mutex = mutex
        self.clients = list()
        self.paths = []  # a list of lists
        self.states = [] 
        self.timer = threading.Timer(self.START_DELAY, self.run)
        self.timer.start()

    def run(self):
        self.timer = threading.Timer(self.TIME_INTERVAL, self.run)
        self.timer.start()
        for s in range(len(self.clients)):
            for p in range(len(self.paths[s])):
                r1,r2 = self.paths[s][p]
                if bool(self.states[s][p][0]):
                    last_entry = self.states[s][p][0][-1]
                    lidx = last_entry[0:last_entry.find(',')]
                else:
                    lidx = '0'
                self.clients[s].request(self.states[s][p][0], "GET /stats/"+r1+"/"
                +r2+"/"+lidx+"/0/ HTTP/1.1\r\nHost: localhost\r\n\r\n")
                if bool(self.states[s][p][1]):
                    last_entry = self.states[s][p][1][-1]
                    lidx = last_entry[0:last_entry.find(',')]
                else:
                    lidx = '0'
                self.clients[s].request(self.states[s][p][1], "GET /stats/"+r2+"/"
                +r1+"/"+lidx+"/0/ HTTP/1.1\r\nHost: localhost\r\n\r\n")
                
    def add_path(self, server, path):
        # find if we know the server
        match = [i for i,x in enumerate(self.clients) if x.server == server]
        if not match:
            self.clients.append(client())
            idx = len(self.clients) - 1
            self.clients[idx].start_connection(server)
            self.paths.append([])
            self.states.append([])
        else :
            idx = match[0]
        
        # add path if it is not in the servers list of paths
        match = [i for i,x in enumerate(self.paths[idx]) if x == path]
        if not match:
            self.paths[idx].append(path)
            self.states[idx].append([list(), list()])            

########################################################################################
if __name__ == '__main__':
#     a = client(('192.168.21.100', 8080))
    mutex = threading.Lock()
    nb = neighbor_state(mutex)
    nb.add_path(('192.168.21.100', 8080), ('192.168.10.2','192.168.13.3') )
    asyncore.loop()

########################################################################################
