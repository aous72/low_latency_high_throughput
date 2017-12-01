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
from mininet.node import Host, Controller
from mininet.link import Intf, TCLink
from mininet.log import setLogLevel, info
from mininet.cli import CLI

########################################################################################
class linux_router( Host ):
    "A host working as a simple linux router"

    def config( self, **params ):
        super( linux_router, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def set_routing_table(self, first_two_octets, subnet, dev):
        assert subnet in [11, 12, 13, 14, 21, 22, 23, 24]
        t = [10, 11, 12, 13, 14] if subnet in [11, 12, 13, 14] else [20, 21, 22, 23, 24]
        for x in t: #host config is only for non-default
            if x < subnet - 1:
                self.cmd('route add -net ' + first_two_octets + '.' + str(x) + '.0'
                    + ' netmask 255.255.255.0 gw ' 
                    + first_two_octets + '.' + str(subnet-1) + '.1'
                    + ' dev ' + dev)                
            if x > subnet:
                self.cmd('route add -net ' + first_two_octets + '.' + str(x) + '.0'
                    + ' netmask 255.255.255.0 gw ' 
                    + first_two_octets + '.' + str(subnet) + '.254'
                    + ' dev ' + self.name + '-eth0')        	

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( linux_router, self ).terminate()

########################################################################################
class one_stage( Topo ):
    "One stage of our network setup" 
    
    def build( self, *args, **params ):
    
        # default ip address
        base_ip = params[ 'ip' ]  # this is the first three octets
        first_two_octets = base_ip[0:base_ip.rfind('.')] # first two octets
        this_subnet = int(base_ip[base_ip.rfind('.')+1:]) # third octet as int
        default_route_ip = base_ip +'.1'
        default_route = 'via ' + default_route_ip

        #switches
        s1 = self.addSwitch( 's1', listenPort='6641')
        s2 = self.addSwitch( 's2', listenPort='6642')
        s3 = self.addSwitch( 's3', listenPort='6643')
        s4 = self.addSwitch( 's4', listenPort='6644')
        s5 = self.addSwitch( 's5', listenPort='6645')
        s6 = self.addSwitch( 's6', listenPort='6646')

        #hosts
        r1 = self.addHost( 'r1', cls=linux_router, ip=default_route_ip+'/24' )
        self.addLink( s1, r1, txo=False, rxo=False )
                
        h2 = self.addHost( 'h2', ip=base_ip+'.2/24', defaultRoute = default_route )
        self.addLink( h2, s3, txo=False, rxo=False )
        h3 = self.addHost( 'h3', ip=base_ip+'.3/24', defaultRoute = default_route )
        self.addLink( h3, s3, txo=False, rxo=False )
        
        #links between switches   
        self.addLink( s1, s2, bw=params[ 'low_bw'  ], delay=1, txo=False, rxo=False )
        self.addLink( s2, s3, txo=False, rxo=False )
        self.addLink( s3, s4, txo=False, rxo=False )
        self.addLink( s4, s5, bw=params[ 'low_bw'  ], delay=1, txo=False, rxo=False )
        self.addLink( s5, s6, delay=params[ 'ext_delay' ], txo=False, rxo=False )

        # out of band network switches
        s7 = self.addSwitch( 's7', listenPort='6647')
        s8 = self.addSwitch( 's8', listenPort='6648')
        s9 = self.addSwitch( 's9', listenPort='6649')
        
        # hosts
        r2 = self.addHost( 'r2', cls=linux_router, ip=first_two_octets + '.' 
            + str(this_subnet + 10) + '.1/24' )
        self.addLink( s7, r2, txo=False, rxo=False )

        # links between switches
        self.addLink( s7, s8, txo=False, rxo=False )
#        self.addLink( s8, s9, delay=1, txo=False, rxo=False )
        self.addLink( s8, s9, delay=params[ 'ext_delay' ], txo=False, rxo=False )
         
        # cross link between control and data
        r3 = self.addHost( 'r3', cls=linux_router )
        self.addLink( s2, r3, txo=False, rxo=False )
        self.addLink( s7, r3, txo=False, rxo=False )

########################################################################################
def add_root_node(net, first_two_octets, subnet):
    """
        add an extra node that is part of the root namespace
        and configure it to be accessible from the network
        Note that this host is not visible from inside mininet """

    base_ip = first_two_octets + '.' + str(subnet)    
    root_node = Host( 'root', inNamespace=False, ip=base_ip+'.100/24' )
    link = net.addLink( root_node, net.getNodeByName('s7'), txo=False, rxo=False )
    link.intf1.setIP(base_ip+'.100', 24);
    root_node.cmd('ip route flush table main'); # empty routing table
    root_node.cmd('route add -net ' + first_two_octets + '.' + str(subnet)
            + '.0 netmask 255.255.255.0 dev ' + link.intf1.name)
    root_node.cmd('route add default gw ' + base_ip + '.1' + ' dev ' + link.intf1.name)
    for x in range(subnet+1, 25): #host config is only for non-default route
        root_node.cmd('route add -net ' + first_two_octets + '.' + str(x) + '.0'
                + ' netmask 255.255.255.0 gw ' 
                + first_two_octets + '.' + str(subnet) + '.254'
                + ' dev ' + link.intf1.name)
    # cross link between data and control planes
    root_node.cmd('route add -net ' + first_two_octets + '.' + str(subnet - 10) 
                + '.0' + ' netmask 255.255.255.0 gw ' 
                + first_two_octets + '.' + str(subnet) + '.250')
    root_node.cmd('/usr/sbin/sshd -D -o UseDNS=no -u0 &')

    return root_node

########################################################################################
def create_network(argv):
    "Run one stage of network"

    # if we have forgotten to raise them
    call('ifconfig eth0 up', shell=True)    
    call('ifconfig eth1 up', shell=True)
    
    # about this network
    base_ip = argv[0][0:argv[0].rfind('.')] # the first three octets
    first_two_octets = base_ip[0:base_ip.rfind('.')] # first two octets    
    this_subnet = int(base_ip[base_ip.rfind('.')+1:]) # third octet as int
    
    # mininet
    topo = one_stage( ip = base_ip, low_bw=5, ext_delay=50000 )
    net = Mininet( topo, link=TCLink, 
                   controller=Controller('c0', ip='127.0.0.2', port=6653) )
    
    # add eth0 to router 1 and set its ip
    # set the subnet of eth0 to 1 smaller than current subnet; for example:
    # set it to 192.168.10.254 when the network subnet is 192.168.11.0
    r1 = net.getNodeByName('r1')
    Intf('eth0', r1)
    eth0_ip =  first_two_octets + '.' + str(this_subnet - 1) + '.254'
    r1.cmd('ifconfig eth0 ' + eth0_ip + ' netmask 255.255.255.0')
    
    # add eth1 to switch s6 and set its ip
    s6 = net.getNodeByName('s6')
    Intf('eth1', s6)
    eth1_ip = first_two_octets + '.' + str(this_subnet) + '.253'
    s6.cmd('ifconfig eth1 ' + eth1_ip + ' netmask 255.255.255.0')
    
    # add eth2 to router 2
    r2 = net.getNodeByName('r2')
    Intf('eth2', r2)
    eth2_ip =  first_two_octets + '.' + str(this_subnet + 10 - 1) + '.254'
    r2.cmd('ifconfig eth2 ' + eth2_ip + ' netmask 255.255.255.0')

    # add eth1 to switch s9 and set its ip
    s9 = net.getNodeByName('s9')
    Intf('eth3', s9)
    eth3_ip = first_two_octets + '.' + str(this_subnet + 10) + '.253'    
    s9.cmd('ifconfig eth3 ' + eth3_ip + ' netmask 255.255.255.0')
    
    # add routing tables
    r1.set_routing_table(first_two_octets, this_subnet, 'eth0')
    r2.set_routing_table(first_two_octets, this_subnet + 10, 'eth2')    
    for h in net.hosts:
        if h.name[0] != 'r': # host other than a router config
            for x in range(this_subnet+1, 15): #host config is only for non-default
                h.cmd('route add -net ' + first_two_octets + '.' + str(x) + '.0'
                    + ' netmask 255.255.255.0 gw ' 
                    + first_two_octets + '.' + str(this_subnet) + '.254')
            h.cmd('route add -net ' + first_two_octets + '.' + str(this_subnet + 10) 
                + '.0' + ' netmask 255.255.255.0 gw ' 
                + first_two_octets + '.' + str(this_subnet) + '.250')
            

    # configuration for router 3
    r3 = net.getNodeByName('r3')
    r3_eth0 = r3.intf('r3-eth0')
    r3_eth0.setIP(first_two_octets + '.' + str(this_subnet) + '.250', 24)
    r3_eth1 = r3.intf('r3-eth1')
    r3_eth1.setIP(first_two_octets + '.' + str(this_subnet + 10) + '.250', 24)
    r3.cmd('route add -net ' + first_two_octets + '.' + str(this_subnet)
            + '.0 netmask 255.255.255.0 dev r3-eth0')
    r3.cmd('route add -net ' + first_two_octets + '.' + str(this_subnet + 10)
            + '.0 netmask 255.255.255.0 dev r3-eth1')
    
    # run sshd on hosts
    for h in net.hosts:
        h.cmd('/usr/sbin/sshd -D -o UseDNS=no -u0 &')

    # root node    
    root_node = add_root_node(net, first_two_octets, this_subnet + 10)

    #net operation
    net.start()
    CLI( net )
    for h in net.hosts:
       h.cmd('kill %/usr/sbin/sshd')
       h.cmd('wait %/usr/sbin/sshd')
    root_node.cmd('kill %/usr/sbin/sshd')
    root_node.cmd('wait %/usr/sbin/sshd')
    net.stop()
    
    # reconfigure the interface for use when we exit mininet
    sleep(0.5)
    call('ifconfig eth0 up', shell=True)
    call('ifconfig eth1 up', shell=True)
    sleep(0.5)
    call('ifconfig eth0 ' + eth0_ip + ' netmask 255.255.255.0', shell=True)
    call('ifconfig eth1 ' + eth1_ip + ' netmask 255.255.255.0', shell=True)

########################################################################################
if __name__ == '__main__':
    setLogLevel( 'info' )
    if len(argv) != 2:
        print ('Please specify subnet')
    else:
       create_network(argv[1:])
