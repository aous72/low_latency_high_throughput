#!/bin/bash

# cur_time=`date +%s`
# let run_time=$cur_time+30
# let run_time2=$cur_time+40
# let run_time3=$cur_time+50
# 
# echo ${run_time}
ssh mininet@192.168.14.2 "screen -S test -d -m bash -c 'sleep 30; client_server/client 192.168.11.2 8000 1 0'" &
ssh mininet@192.168.12.2 "screen -S test -d -m bash -c 'sleep 50; client_server/client 192.168.11.2 8000 1 0'" &
ssh mininet@192.168.11.2 "screen -S test -d -m bash -c 'sleep 90; iperf -c 192.168.13.3 -i 1 -t 30'" &
