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
import collections

########################################################################################
class network_state:
    """ 
        A class to obtain network state every 50ms
        The code is based on _Timer's code; I did not want to inherit from Timer
        because it is just a function that wraps around _Timer, which looks
        like the authors of the code do not want you to inherit from 
    """

    INTERVAL_TIME = 0.5 # 50ms intervals
    DEQUE_SIZE = 3 * 100 # three networks, 100 for each
    NETEM_KEYS = ['Dev','P_Delay','SentB','BackB']

        
    def __init__(self):
        self.timer = None
        self.ns = collections.deque(maxlen=self.DEQUE_SIZE)
        self.regex = re.compile(r"qdisc\snetem\s+[0-9]+:\sdev\s([a-zA-Z0-9-]+)"
            "\s.*\slimit\s[0-9]+\sdelay\s([0-9.]+)[mu]"
            "s[a-zA-Z0-9_.:\s]+Sent\s([\d]+)\sbytes\s[\d]+\spkt\s\(dropped\s[\d]+"
            ",\soverlimits\s[\d]+\srequeues\s[\d]+\)\s*"
            "backlog\s([\dA-Z]+)b\s[\d]+p\srequeues\s[0-9]+")
        
    def run(self):
        try:
#             t1 = time.time()
            self.timer = threading.Timer(self.INTERVAL_TIME, self.run).start()
            tc_output = subprocess.check_output( 'tc -s qdisc show', shell=True)
            tc_parse = self.regex.findall(tc_output)
#             netem_entry = [dict(zip(self.NETEM_KEYS,row)) for row in tc_parse]
#             for i in tc_parse:
#                 print i
#            print tc_parse[0]
#             print time.time() - t1 
        except (KeyboardInterrupt, SystemExit):
            if self.timer is not None:
                self.timer.cancel()

########################################################################################
if __name__ == '__main__':
    ns = network_state()
    ns.run()


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



