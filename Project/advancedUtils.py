import socket
import subprocess
from pythonping import ping
from pysnmp.hlapi.v3arch.asyncio import *
from logger import Logger
import asyncio
import ipaddress


# This is a static dictionary of rekevant SNMP MIB objects for UPS devices (RFC 1628)
# Specifically alerts thrown by UPS devices.
UPS_ALARMS = {
    '1.3.6.1.2.1.33.1.6.3.1':  'Replace Battery',
    '1.3.6.1.2.1.33.1.6.3.2':  'On Battery',
    '1.3.6.1.2.1.33.1.6.3.3':  'Low Battery',
    '1.3.6.1.2.1.33.1.6.3.4':  'Depleted Battery',
    '1.3.6.1.2.1.33.1.6.3.5':  'Temperature Bad',
    '1.3.6.1.2.1.33.1.6.3.6':  'Input Bad',
    '1.3.6.1.2.1.33.1.6.3.7':  'Output Bad',
    '1.3.6.1.2.1.33.1.6.3.8':  'Output Overload',
    '1.3.6.1.2.1.33.1.6.3.9':  'On Bypass',
    '1.3.6.1.2.1.33.1.6.3.10': 'Bypass Bad',
    '1.3.6.1.2.1.33.1.6.3.11': 'Output Off As Requested',
    '1.3.6.1.2.1.33.1.6.3.12': 'UPS Off As Requested',
    '1.3.6.1.2.1.33.1.6.3.13': 'Charger Failed',
    '1.3.6.1.2.1.33.1.6.3.14': 'UPS Output Off',
    '1.3.6.1.2.1.33.1.6.3.15': 'UPS System Off',
    '1.3.6.1.2.1.33.1.6.3.16': 'Fan Failure',
    '1.3.6.1.2.1.33.1.6.3.17': 'Fuse Failure',
    '1.3.6.1.2.1.33.1.6.3.18': 'General Fault (See card on the web)',
    '1.3.6.1.2.1.33.1.6.3.19': 'Battery Test Failed',
    '1.3.6.1.2.1.33.1.6.3.20': 'Communications Lost',
    '1.3.6.1.2.1.33.1.6.3.21': 'Awaiting Initial Delay',
    '1.3.6.1.2.1.33.1.6.3.22': 'Shutdown Pending',
    '1.3.6.1.2.1.33.1.6.3.23': 'Shutdown Imminent',
    '1.3.6.1.2.1.33.1.6.3.24': 'Test In Progress',
}

# Check if the UPS device's webcard is reachable via ping
def is_reachable(ip: str) -> bool:
    try:
        result = subprocess.run(
            ['ping', '-n', '1', '-w', '2000', ip],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


# This function retrieves status info from a single vertiv UPS device
# It uses SNMP to query the device for various status OIDs and prints the results.
async def ups_status_summary(ip, community_str="sidekick"):

    status_OIDs = {
        'Location': '1.3.6.1.2.1.1.6.0',
        'Model': '1.3.6.1.4.1.476.1.42.2.4.2.1.4.1',
        'Card Type': '1.3.6.1.4.1.476.1.42.2.1.5.0',
        'Battery Status': '1.3.6.1.2.1.33.1.2.1.0',
        'Battery Charge %': '1.3.6.1.2.1.33.1.2.4.0',
        'Time Remaining (min)': '1.3.6.1.4.1.476.1.42.3.5.1.18.0',
        'Output Status': '1.3.6.1.2.1.33.1.4.1.0',
        'Output Load %': '1.3.6.1.2.1.33.1.4.4.1.5.1',
        'Battery Temperature (F)': '1.3.6.1.4.1.476.1.42.3.4.1.2.3.1.3.1'           
    }

    snmp_engine = SnmpEngine()

    try:

        transport = await UdpTransportTarget.create((ip, 161), timeout=10, retries=1)

        for name, oid in status_OIDs.items():
            try:
                iterator = get_cmd(
                    snmp_engine,
                    CommunityData(community_str),
                    transport, 
                    ContextData(),
                    ObjectType(ObjectIdentity(oid))
                )

                errorIndication, errorStatus, errorIndex, varBinds = await iterator
                if errorIndication or errorStatus:
                    Logger.log(f"ups_status_summary OID ERROR - {name} | errInd={errorIndication} | errStat={errorStatus}", level="ERROR")
                    return None

                value = varBinds[0][1]
                if 'Status' in name:
                    bat_stat = {1: 'unknown (CHK_BAT)', 2: 'Normal', 3: 'Low', 4: 'Depleted'}
                    out_stat = {1: 'Other', 2: 'None', 3: 'Normal', 4: 'Bypass', 5: 'Battery', 6: 'Booster', 7: 'Reducer'}
                    if 'Battery' in name:
                        stat_text = bat_stat.get(int(value), f'unknown({value})')
                    else: # output status
                        stat_text = out_stat.get(int(value), f'unknown({value})')
                    print(f"{name}: {stat_text}")
                    status_OIDs[name] = stat_text
                else:
                    print(f"{name}: {value}")
                    status_OIDs[name] = value 
            
            except Exception as e:
                print(f"Error querying {name}: {e}")

    finally:
        snmp_engine.close_dispatcher()

    status_OIDs['IP'] = ip
    return status_OIDs


# for report loader function
async def run_report(below_batt: bool    = False,       # parameter by user for filter 
                     batt_threshold: int = 70,          # parameter by user for filter
                     audible_alm: bool   = False,       # parameter by user for filter
                     below_load: bool    = False,       # parameter by user for filter
                     load_threshold: int = 0,           # parameter by user for filter
                     batt_stat: str      = "Any",       # parameter by user for filter
                     ip_list: str        = "",          # user passes batch file of IPs
                     dyn_scan: bool      = False        # user marks use of scanNet (ignores ip_list)
                     ):
    report_tally = 0

    from datetime import datetime
    import glob
    date_str = datetime.now().strftime("%m-%d-%Y")
    existing = glob.glob(f"report-{date_str}-*.txt")
    n = len(existing) + 1
    report_filename = f"report-{date_str}-{n}.txt"

    # 1. read file and parse IPs to list
    # 2. for each item in list, run ups_status_summary
    # 3. retrieve dict from previous func call and assess based on passed parameters
    # 4. units that pass check added to report tally (tally that denotes unit satisfies conditions requested by user)
    # 5. additional details from dict entry for specific IP are parsed into an output file
    # 6. when loop ends, parse the tally to line: "Devices met criteria: 4" AND
    # 7. parse this line - "parameter summary: BATT below 70%, AA: ON, LOAD above 40%"
    # 8. parse this last line - "report created 11-19-2025 @ 12:54pm"
    with open(report_filename, "w") as file:


        if not dyn_scan:
            with open(ip_list, 'r', encoding='utf-8') as f:
                
                lines = [line.strip() for line in f.readlines() if line.strip()]
                Logger.log(f"[run_report] Processing {len(lines)} IPs: {lines}")
                for line in lines:

                    ups_stats: dict = await ups_status_summary(line)
                    if not ups_stats:
                        Logger.log(f"[{line}] SNMP failure - skipping.")
                        file.write(f"\n[{line}] SNMP failure. Check the README for support or verify your SNMP settings of your target system.\n")
                        continue
                    Logger.log(f"[run_report] [{line}] stats: BattCharge={ups_stats['Battery Charge %']} BattStat={ups_stats['Battery Status']} Load={ups_stats['Output Load %']}")
                    if audible_alm:
                        alms = await ups_alarms_stat(line)
                        Logger.log(f"[run_report] [{line}] alarms={alms}")
                        if alms:
                            Logger.log(f"Alarm check [{line}] PRESENT - adding to report.")
                            report_tally += 1
                            file.write(f"\nUPS Unit {line}\n=================\n")
                            for k, v in ups_stats.items():
                                file.write(f"{k}: {v}\n")
                            continue
                        else:
                            Logger.log(f"[{line}] No alarms — skipped (audible_alm filter).")
                            continue
                    if below_batt and int(ups_stats['Battery Charge %']) > batt_threshold:
                        continue
                    if not below_batt and int(ups_stats['Battery Charge %']) < batt_threshold:
                        continue
                    if below_load and int(ups_stats['Output Load %']) > load_threshold:
                        continue
                    if not below_load and int(ups_stats['Output Load %']) < load_threshold:
                        continue
                    if batt_stat != "Any" and ups_stats['Battery Status'] != batt_stat:
                        continue
                    Logger.log(f"[{line}] PASSED all filters — adding to report.")
                    report_tally += 1
                    file.write(f"\nUPS Unit {line}\n=================\n")
                    for k, v in ups_stats.items():
                        file.write(f"{k}: {v}\n")
                
                file.write(f"\n=================\nDevices met criteria: {report_tally}\n")
                file.write(f"Parameter summary:\nBATT {"below" if below_batt else "above"} {batt_threshold}\n"
                        f"ALARM: {"ON" if audible_alm else "OFF"}\n"
                        f"LOAD {"below" if below_load else "above"} {load_threshold}\n")
                now = datetime.now()
                timestamp = now.strftime("report created %m-%d-%Y @ %I:%M%p").lower()
                file.write(timestamp)
        else:
            pass # scanNet work


# This function retrieves the alarms status from a Vertiv UPS device.
# It uses SNMP to query the device for active alarms and additional alarm details.
async def ups_alarms_stat(ip, community_str:str="sidekick"):
    alm_i = 0
    alms = []

    snmp_engine = SnmpEngine()
    snmp_engine.get_mib_builder().load_modules('UPS-MIB')

    try:
        transport = await UdpTransportTarget.create((ip, 161))

        iterator = get_cmd(
            snmp_engine,
            CommunityData(community_str),
            transport, 
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.33.1.6.1.0'))
        )

        errorIndication, errorStatus, errorIndex, varBinds = await iterator

        if errorIndication or errorStatus:
            return alms

        for varBind in varBinds:
            oid = str(varBind[0])
            value = str(varBind[1])

            if oid == '1.3.6.1.2.1.33.1.6.1.0':
                alm_i = int(value)
                print(f"Active alarms: {alm_i}")

            elif oid.startswith('1.3.6.1.2.1.33.1.6.2'):
                alms.append((oid, value))
                print(f"Alarm: {oid} = {value}")
        if alm_i == 0:
            print("No alarms present.")
        else:
            print("\n!!!!!!!!!!!!!!!!!!!!!!!")
            async for (err_ind, err_stat, err_idx, var_binds) in walk_cmd(
                snmp_engine,
                CommunityData(community_str),
                transport,
                ContextData(),
                ObjectType(ObjectIdentity('1.3.6.1.2.1.33.1.6.2'))
            ):
                if err_ind or err_stat:
                    break

                for var_bind in var_binds:
                    oid_str = str(var_bind[0])
                    if '.1.6.2.1.2.' not in oid_str:
                        continue
                    raw_oid = var_bind[1].prettyPrint()
                    name = UPS_ALARMS.get(raw_oid, raw_oid)
                    alms.append(name)
                    print(f"Alarm: {name}")
                            
    finally:
        snmp_engine.close_dispatcher()
    
    return alms
    

# This function performs an ARP lookup to retrieve the MAC address of a device.
# It uses SNMP to query the device for its MAC address because ARP requests may not work across subnets.
async def mac_lookup(ip:str, community_str:str="sidekick"):
    
    vertiv_oui = "00:09:f5"

    snmp_engine = SnmpEngine()

    try:
        transport = await UdpTransportTarget.create((ip, 161))

        iterator = get_cmd(
            snmp_engine,
            CommunityData(community_str),
            transport, 
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.6')) # OID for physical addr (MAC)
        )

        errorIndication, errorStatus, errorIndex, varBinds = await iterator

        if errorIndication:
            print(f" {ip} error: {errorIndication}")
            pass # TODO handle error
        elif errorStatus:
            print(f"{ip} error: {errorStatus.prettyPrint()}")
            pass # TODO handle error
        else:
            # varBinds is the MIB variables (OIDs); multiple physical interfaces exist in the device
            value = varBinds[0][1]
            if hasattr(value, 'asOctets'):
                mac = ':'.join(f'{b:02x}' for b in value.asOctets())
                print(f"{ip} MAC: {mac}")
                if mac.startswith(vertiv_oui):
                    return True  
    finally:
        snmp_engine.close_dispatcher()
    return False            

# This function scans a classful network and retrieves Vertiv UPS devices.
# It supports segmentation of the network into subnets and can handle both contiguous
# and non-contiguous subnets. It uses ping to check for device availability and 
# ARP to identify devices by their MAC address.
#
# TODO This function is unavailable and incomplete in the current version (3.0)
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
#       assume       - By default, scanNet interpolates the network addr of the device used to login
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
                print(f"Vertiv UPS found {host}")
        else:
            print(f"{str(host)}: unreachable")


