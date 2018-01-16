#!/bin/bash

sudo rm /var/log/auth.log*
sudo rm /var/log/syslog*
sudo rm /var/log/wtmp*

sudo ifconfig eth4 up
sudo dhclient eth4
sudo service ntp stop
sudo ntpdate time.nist.gov
sudo service ntp start
sudo ifconfig eth4 down






