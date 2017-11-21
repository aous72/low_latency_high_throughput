#!/usr/bin/python

import urllib2
print '11->'
response = urllib2.urlopen('http://192.168.21.100:8080/stats/192.168.11.2/192.168.12.2/0/0')
print response.read()
response = urllib2.urlopen('http://192.168.21.100:8080/stats/192.168.11.2/192.168.13.2/0/0')
print response.read()
response = urllib2.urlopen('http://192.168.21.100:8080/stats/192.168.11.2/192.168.14.2/0/0')
print response.read()
print '12<-'
response = urllib2.urlopen('http://192.168.21.100:8080/stats/192.168.12.2/192.168.11.2/0/0')
print response.read()
response = urllib2.urlopen('http://192.168.21.100:8080/stats/192.168.13.2/192.168.11.2/0/0')
print response.read()
response = urllib2.urlopen('http://192.168.21.100:8080/stats/192.168.14.2/192.168.11.2/0/0')
print response.read()

print
print
print '12->'
response = urllib2.urlopen('http://192.168.22.100:8080/stats/192.168.12.2/192.168.11.2/0/0')
print response.read()
response = urllib2.urlopen('http://192.168.22.100:8080/stats/192.168.12.2/192.168.13.2/0/0')
print response.read()
response = urllib2.urlopen('http://192.168.22.100:8080/stats/192.168.12.2/192.168.14.2/0/0')
print response.read()
print '12<-'
response = urllib2.urlopen('http://192.168.22.100:8080/stats/192.168.11.2/192.168.12.2/0/0')
print response.read()
response = urllib2.urlopen('http://192.168.22.100:8080/stats/192.168.13.2/192.168.12.2/0/0')
print response.read()
response = urllib2.urlopen('http://192.168.22.100:8080/stats/192.168.14.2/192.168.12.2/0/0')
print response.read()

print
print
print '13->'
response = urllib2.urlopen('http://192.168.23.100:8080/stats/192.168.13.2/192.168.11.2/0/0')
print response.read()
response = urllib2.urlopen('http://192.168.23.100:8080/stats/192.168.13.2/192.168.12.2/0/0')
print response.read()
response = urllib2.urlopen('http://192.168.23.100:8080/stats/192.168.13.2/192.168.14.2/0/0')
print response.read()
print '13<-'
response = urllib2.urlopen('http://192.168.23.100:8080/stats/192.168.11.2/192.168.13.2/0/0')
print response.read()
response = urllib2.urlopen('http://192.168.23.100:8080/stats/192.168.12.2/192.168.13.2/0/0')
print response.read()
response = urllib2.urlopen('http://192.168.23.100:8080/stats/192.168.14.2/192.168.13.2/0/0')
print response.read()

print
print
print '14->'
response = urllib2.urlopen('http://192.168.24.100:8080/stats/192.168.14.2/192.168.11.2/0/0')
print response.read()
response = urllib2.urlopen('http://192.168.24.100:8080/stats/192.168.14.2/192.168.12.2/0/0')
print response.read()
response = urllib2.urlopen('http://192.168.24.100:8080/stats/192.168.14.2/192.168.13.2/0/0')
print response.read()
print '14<-'
response = urllib2.urlopen('http://192.168.24.100:8080/stats/192.168.11.2/192.168.14.2/0/0')
print response.read()
response = urllib2.urlopen('http://192.168.24.100:8080/stats/192.168.12.2/192.168.14.2/0/0')
print response.read()
response = urllib2.urlopen('http://192.168.24.100:8080/stats/192.168.13.2/192.168.14.2/0/0')
print response.read()

