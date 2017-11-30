#!/bin/bash

cur_time=`date +%s`
let run_time=$cur_time+30
let run_time2=$cur_time+40
let run_time3=$cur_time+50

echo ${run_time}
echo ssh mininet@192.168.14.2 "start_service.py jpip ${run_time}" &
echo ssh mininet@192.168.14.2 "start_service.py jpip ${run_time2} 1" &
echo ssh mininet@192.168.12.2 "start_service.py iperf ${run_time3}" &