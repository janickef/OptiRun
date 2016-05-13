from netifaces import interfaces, ifaddresses, AF_INET

for ifaceName in interfaces():
    addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':'No IP addr'}] )]
    print '%s: %s' % (ifaceName, ', '.join(addresses))

print
print

import socket

# from http://commandline.org.uk/python/how-to-find-out-ip-address-in-python/
def getNetworkIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('lnor010710', 0))
    return s.getsockname()

print getNetworkIp()



s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('8.8.8.8', 0))  # connecting to a UDP address doesn't send packets
local_ip_address = s.getsockname()[0]
print local_ip_address

print socket.gethostbyname('0.0.0.0')