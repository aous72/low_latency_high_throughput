#!/usr/bin/python

import time
import os
from sys import argv

########################################################################################
def start_service(argv):
    t = time.time()
    time.sleep(t - float(argv[1]))
    if argv[0] == 'jpip':
        if len(argv) == 2:
#             print 'jpip'
            os.system('client_server/client 192.168.11.2 8000 1')
        else:
#             print 'jpip save'
            os.system('client_server/client 192.168.11.2 8000 1 0')
    elif argv[0] == 'iperf':
#             print 'iperf'
            os.system('iperf -c 192.168.12.2 -i 1 -t 10')
    else:
        print 'Not Supported'
    

########################################################################################
if __name__ == '__main__':
    if len(argv) not in [3, 4]:
        print ('Usage: <service, either jpip or iperf> <time from now> <save bw to file>', )
    else:
       start_service(argv[1:])
