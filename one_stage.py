#!/usr/bin/python

"""
one_stage.py: builds one stage of our network, where we intend to replicate
              this design in other networks

	One side of the network connect to the external network E1 using a real ethernet 
	network card eth0, which obtains its ip address from a DHCP server at the external
	network E1.
	
	The real ethernet card is connected to a router that connects to an 
	internal network I1 on the other size, using ip address ending with .1
	
	The internal network I1 has a dhcp server, a few host, a few switches, and connected
	to an external network E2 on the other side using another real interface eth1.  
	The dhcp server assigns ip addresses to this interface and any other interfaces
	on that external network E2.
	
	The internal network has a few switches, some of which is to overcome issues with 
	the way mininet operates.

"""

from sys import argv
from subprocess import call
from time import sleep

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.link import Intf, TCLink
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.util import moveIntf

########################################################################################
class dhcp_server( Node ):
    "A host working as a dhcp server"

    def config( self, **params ):
        super( dhcp_server, self).config( **params )
        s = self.params[ 'ip' ].split('.')
        self.cmd( 'dhcpd -cf /home/mininet/dhcpd' + s[2] + '.conf '
        	+ self.defaultIntf().name)

    def terminate( self ):
    	self.cmd('/etc/init.d/isc-dhcp-server stop')
        super( dhcp_server, self ).terminate()
        
########################################################################################
class linux_router( Node ):
    "A host working as a simple linux router"

    def config( self, **params ):
        super( linux_router, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( linux_router, self ).terminate()

########################################################################################
class one_stage( Topo ):
    "One stage of our network setup" 
    
    def build( self, *args, **params ):
    
        # default ip address
        base_ip = params[ 'ip' ]
        default_route_ip = base_ip +'.1'
        default_route = 'via ' + default_route_ip
        
        #switches
        s1,s2,s3,s4,s5,s6 = [self.addSwitch( s ) for s in 's1','s2','s3','s4','s5','s6']
                
        r1 = self.addHost( 'r1', cls=linux_router, ip=default_route_ip+'/24' )
        self.addLink( s1, r1, bw=params[ 'high_bw' ] )
                
        h2 = self.addHost( 'h2', ip=base_ip+'.2/24', defaultRoute = default_route )
        self.addLink( h2, s1, bw=params[ 'high_bw' ] )
        h3 = self.addHost( 'h3', ip=base_ip+'.3/24', defaultRoute = default_route )
        self.addLink( h3, s1, bw=params[ 'high_bw' ] )
        h4 = self.addHost( 'h4', ip=base_ip+'.4/24', defaultRoute = default_route )
        self.addLink( h4, s4, bw=params[ 'high_bw' ] )
        
        dhcp = self.addHost( 'dhcp', cls=dhcp_server, ip=base_ip+'.5/24',
            defaultRoute = default_route  )
        self.addLink( dhcp, s4, bw=params[ 'high_bw' ]  )        
                
        self.addLink( s1, s2, bw=params[ 'high_bw' ] )
        self.addLink( s2, s3, bw=params[ 'low_bw'  ], delay=params[ 'in_delay'  ] )        
        self.addLink( s3, s4, bw=params[ 'high_bw' ] )
        self.addLink( s4, s5, bw=params[ 'high_bw' ] )
        self.addLink( s5, s6, bw=params[ 'high_bw' ], delay=params[ 'ext_delay' ] )
                                    
########################################################################################
def run(argv):
    "Run one stage of network"

	# if we have forgotten to raise them
    call('ifconfig eth0 up', shell=True)    
    call('ifconfig eth1 up', shell=True)
    
	# about this network
    base_ip = argv[0][0:argv[0].rfind('.')] # the first three octets
    first_two_octets = base_ip[0:base_ip.rfind('.')] # first two octets    
    this_subnet = int(base_ip[base_ip.rfind('.')+1:]) # third octet as int
    	
    # mininet
    topo = one_stage( ip = base_ip, low_bw=5, high_bw=10, 
    				  in_delay=10000, ext_delay=60000 )
    net = Mininet( topo, link=TCLink )
    
    # add eth0 to router and set its ip
    # set the subnet of eth0 to 1 smaller than current subnet; for example:
    # set it to 192.168.10.254 when the network subnet is 192.168.11.0
    r1 = net.getNodeByName('r1')
    Intf('eth0', r1)
    eth0_ip =  first_two_octets + '.' + str(this_subnet - 1) + '.254'
    r1.cmd('ifconfig eth0 ' + eth0_ip + ' netmask 255.255.255.0')
    
    # add eth1 to switch s6 and set its ip
    s6 = net.getNodeByName('s6')
    Intf('eth1', s6)
    s6.cmd('ifconfig eth1 ' + base_ip + '.253' + ' netmask 255.255.255.0')
    
    # add routing tables
    for h in net.hosts:
        if h.name[0] == 'r': # router config
            for x in range(10, 14): #host config is only for non-default
                if x < this_subnet - 1:
                    h.cmd('route add -net ' + first_two_octets + '.' + str(x) + '.0'
                        + ' netmask 255.255.255.0 gw ' 
                        + first_two_octets + '.' + str(this_subnet-1) + '.1'
                        + ' dev eth0')                
                if x > this_subnet:
                    h.cmd('route add -net ' + first_two_octets + '.' + str(x) + '.0'
                        + ' netmask 255.255.255.0 gw ' 
                        + first_two_octets + '.' + str(this_subnet) + '.254'
                        + ' dev r1-eth0')
        else: # host other than a router config
            for x in range(this_subnet+1, 14): #host config is only for non-default
                h.cmd('route add -net ' + first_two_octets + '.' + str(x) + '.0'
                    + ' netmask 255.255.255.0 gw ' 
                    + first_two_octets + '.' + str(this_subnet) + '.254')
    
    # other hosts configuration
    for h in net.hosts:
        # prevent jumbo packets
        h.cmd( 'ethtool -K %s-eth0 tso off gso off ufo off' % h)
        # run sshd
        h.cmd('/usr/sbin/sshd -D -o UseDNS=no -u0 &')
    
    #net operation
    net.start()
    CLI( net )
    for h in net.hosts:
       h.cmd('kill %/usr/sbin/sshd')
    net.stop()
    
    # reconfigure the interface for use when we exit mininet
    sleep(0.5)
    call('ifconfig eth0 up', shell=True)
    sleep(0.5)
    call('ifconfig eth0 ' + eth0_ip + ' netmask 255.255.255.0', shell=True)

########################################################################################
if __name__ == '__main__':
    setLogLevel( 'info' )
    if len(argv) != 2:
        print 'Please specify subnet'
    else:
	    run(argv[1:])

            
            
            
            
            