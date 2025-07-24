import socket
from pythonping import ping
from pysnmp.hlapi import *
import asyncio
import ipaddress

# This function retrieves status info from a single vertiv UPS device
# It uses SNMP to query the device for various status OIDs and prints the results.
# TODO should return a dict with the status info instead of printing it directly.
def ups_status_summary(ip, community_str="sidekick"):

    status_OIDs = {
        'Model': '1.3.6.1.4.1.476.1.42.2.4.2.1.4.1',
        'Card Type': '1.3.6.1.4.1.476.1.42.2.1.5.0',
        'Battery Status': '1.3.6.1.2.1.33.1.2.1.0',
        'Battery Charge %': '1.3.6.1.2.1.33.1.2.4.0',
        'Time Remaining (min)': '1.3.6.1.4.1.476.1.42.3.5.1.18.0',
        'Output Status': '1.3.6.1.2.1.33.1.4.1.0',
        'Output Load %': '1.3.6.1.2.1.33.1.4.4.1.5.1',
        'Battery Temperature (F)': '1.3.6.1.4.1.476.1.42.3.4.1.2.3.1.3.1'           
    }
    for name, oid in status_OIDs.items():
        for(errorIndication, errorStatus, _, varBinds) in getCmd(
            SnmpEngine(),
            CommunityData(community_str),
            UdpTransportTarget((ip, 161)),
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        ):
            if errorIndication or errorStatus:
                continue
            value = varBinds[0][1]
            if 'Status' in name:
                bat_stat = {1: 'unknown (CHK_BAT)', 2: 'Normal', 3: 'Low', 4: 'Depleted'}
                out_stat = {1: 'other', 2: 'none', 3: 'normal', 4: 'bypass', 5: 'battery', 6: 'booster', 7: 'reducer'}

                if 'Battery' in name:
                    stat_text = bat_stat.get(int(value), f'unknown({value})')
                else:
                    stat_text = out_stat.get(int(value), f'unknown({value})')
                print(f"{name}: {stat_text}")
            else:
                print(f"{name}: {value}")


# This function retrieves the alarms status from a Vertiv UPS device.
# It uses SNMP to query the device for active alarms and additional alarm details.
# TODO should return a dict with the alarms info instead of printing it directly.
def ups_alarms_stat(ip, community_str:str="sidekick"):
    alm_i = 0
    alms = []

    for(errorIndication, errorStatus, _, varBinds) in getCmd(
        SnmpEngine(),
        CommunityData(community_str),
        UdpTransportTarget((ip, 161)),
        ContextData(),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.33.1.6.1.0')),
        lexicoGraphicMode=False,
        ignoreNonIncreasingOid=True
    ):
        if errorIndication or errorStatus:
            break
        
        for varBind in varBinds:
            oid = str(varBind[0])
            value = str(varBind[1])

            if oid == '1.3.6.1.2.1.33.1.6.1.0':
                alm_i = int(value)
                print(f"Active alarms: {alm_i}")

            elif oid.startswith('1.3.6.1.2.1.33.1.6.2'):
                alms.append((oid, value))
                print(f"Alarm: {oid} = {value}")
    if alm_i < 0:
        print("No alarms.")

# This function performs an ARP lookup to retrieve the MAC address of a device.
# It uses SNMP to query the device for its MAC address because ARP requests may not work across subnets.
def mac_lookup(ip:str, community_str:str="sidekick"):
    
    vertiv_oui = "00:09:f5"
    # varBinds is the MIB variables (OIDs); multiple physical interfaces exist in the device
    for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
        SnmpEngine(),
        CommunityData(community_str),
        UdpTransportTarget((ip, 161)),
        ContextData(),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.6')), # OID for physical addr (MAC)
        lexicographicMode=False,
        ignoreNonIncreasingOid=True
    ):
        if errorIndication:
            print(f" {ip} error: {errorIndication}")
            pass # TODO handle error
        elif errorStatus:
            print(f"{ip} error: {errorStatus.prettyPrint()}")
            pass # TODO handle error
        else:
            value = varBinds[0][1]
            if hasattr(value, 'asOctets'):
                mac = ':'.join(f'{b:02x}' for b in value.asOctets())
                print(f"{ip} MAC: {mac}")
                if mac.startswith(vertiv_oui):
                    return True  
    return False

# This function scans a classful network and retrieves Vertiv UPS devices.
# It supports segmentation of the network into subnets and can handle both contiguous
# and non-contiguous subnets. It uses ping to check for device availability and 
# SNMP to identify devices by their MAC address.
#
# params:
#       prefix       - The classful address of the network. It must have a
#                      CIDR notation to complete the syntax (e.g., 10.30.0.0/16)
#                      If a CIDR mask is not included, a /16 class B is assumed 
#       segmentation - Defines the subnet mask used to segment the network into subnetworks
#                      If this field is empty, assume /23 (2 subnets, 253 hosts)
#       contiguous   - Defines whether a classful network has contiguous subnets
#                      e.g., A classful ntwk 10.30.0.0/16 segmented with /23:
#                      10.30.0.0/23, 10.30.2.0/23, ...(undefined)..., 10.30.18.0/23
#       cont_n       - Set the number of contiguous subnets in the addressing schema
#                      If set to 0, this param tells the function to scan only the given
#                      subnet provided with prefix/segmentation. "contiguous" var should
#                      be set to False if this var is set to 0. 
#       non_cont_arr - Array of non-contiguous subnets defined in the addressing schema
#       assume       - By default, scanNet interpolates the network addr of device used to login
#                      to Sidekick. If assume=True, then "prefix" is set to the network addr of
#                      the user's computer. This may be helpful when the user needs quick info
#                      while being on-site.
#       attempts     - Used by ping function to custom set the # of tries
#       interval     - Used by ping function to custom set the interval # in-between attempts
#       OUI          - Used to set the OUI match for the arp request used to ID device found by ping
async def scanNet(prefix:str | None, 
            segmentation:int=23, 
            contiguous:bool=False, 
            cont_n:int=0, 
            noncont_arr:list=None, 
            assume:bool=False, 
            attempts:int=3, 
            interval:int=1
            ):
    
    if assume: # retrieve network IP from PC's IP. Assumes /16 classful.
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
             s.close()
        octets = str(ip).split('.')
        octets[-1] = '0'
        prefix = '.'.join(octets) + "/16"
    
    base_network = ipaddress.IPv4Network(prefix)
    #TODO if prefix CIDR and segmentation value MATCH, what would this do?
    subnets = list(base_network.subnets(new_prefix=segmentation))

    if contiguous and cont_n > 0:
        tasks = [asyncio.create_task(scan_subnet(subnet, attempts, interval)) for subnet in subnets[:cont_n]]
        await asyncio.gather(*tasks)
    
    if noncont_arr is not None:
        for network in noncont_arr:
            try:
                subnet = ipaddress.IPv4Network(network)
                if subnet.prefixlen == segmentation:
                    await scan_subnet(subnet, attempts, interval)
                else:
                    print(f"Skipping {network} as it does not match the segmentation {segmentation}.")
            except ValueError as e: # TODO Error will need better handling
                print(f"Invalid subnet {network}: {e}")

# subroutine to be called as a thread by asyncio
async def scan_subnet(subnet, attempts:int, interval:int):
    hosts  = subnet.hosts()
    for host in hosts:
        response = await asyncio.to_thread(ping, str(host), count=attempts, timeout=1, interval=interval)
        if response.success():
            is_vertiv_ups = await asyncio.to_thread(mac_lookup, str(host))
            if is_vertiv_ups:
                print("Vertiv UPS found ^")
        else:
            print(f"{str(host)}: unreachable")


# TESTING THE FUNCTION
asyncio.run(scanNet("10.26.0.0/16", 23, True, 5, None, False))



