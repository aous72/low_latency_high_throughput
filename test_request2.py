#!/usr/bin/python

import urllib2
print '11->'
response = urllib2.urlopen('http://192.168.21.100:8080/stats/192.168.11.2/192.168.12.2/0/0')
print response.read()
response = urllib2.urlopen('http://192.168.21.100:8080/stats/192.168.12.2/192.168.11.2/0/0')
print response.read()
