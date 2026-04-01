help_pages = [
            {
                "title": "Quick Help Menu",
                "content": """See the official user guide for more details on using Sidekick.

Main features:
• Compatibility with Vertiv GXT4/GXT5 UPS devices 
• Batch operations for multiple devices (Import/Export/Firmware upgrade)
• UPS stats and reports available with SNMP
• Single & Batch Network settings modification
• Easy retrieval of diagnostics files of 1+ devices
• Simple restart of device web card
• Simple interface for terminal users
• Supports RDU101 and IS-UNITY Vertiv UPS devices

Use your left/right cursor keys or press tab to navigate the help menu."""
            },
            {
                "title": "(1) Making Network Changes",
                "content": """Select Option 1.

Options available:
• For an individual device,
    > Enter its IP address
    > Enter its subnet mask
    > Enable/Disable DHCP
    > View current network configuration
• For batch operations,
    > Enter path to batch file (must be a .csv file).
    > CSV headers (1st row) must be: Old IP, New IP, Subnet Mask, DHCP.
    > Example: 
        Old IP,New IP,Subnet Mask,DHCP
        10.10.5.1, 10.10.5.2, 255.255.0.0, on
    > The batch file must be in the same directory as the application.
    > Select "Run Batch" to apply changes to all devices in the file.

Note that batch operations may take a while to complete due to required restarts."""
            },
            {
                "title": "(2) Retrieving Diagnostics Files",
                "content": """Select Option 2.

Features:
• Select "Retrieve from this device only" to get diagnostics file from the current device	
• To retrieve from multiple devices:
    > Select "Retrieve from batch devices"
    > You must specify a batch file path under "Edit" in the main menu.
    > Without a valid batch file, this option will be disabled.
•  All diagnostics files will be saved in the current working directory as a .gzipped file

"""
            },
            {
                "title": "(3) Pushing a firmware update",
                "content": """Select Option 3.

Features:
• Select "Update Now" to push firmware update to the current device
• This operation requires a valid firmware file path
    > Set this path under "Edit" in the main menu.
    > Without a valid firmware file, this option will be disabled.
• This process may take 10-15 minutes depending on network connection and restart time of device.

"""
            },  
            {
                "title": "(4) Restarting the web card",
                "content": """Select Option 4.

Features:
• This option allows you to restart the web card of the current device.
• A restart will not affect the UPS operation, 
  but it will temporarily disconnect the web interface.
• A restart may take 3-5 minutes to complete.

"""
            },
            {
                "title": "(5) Performing batch operations",
                "content": """Select Option 5.

Features:
• Export configurations from multiple devices
• Import configuration files to multiple devices
• Perform firmware updates on a batch of devices

Set up batch mode by pressing 'E - Edit' and selecting
either 'Batch (RDU101)' or 'Batch (IS-UNITY)' mode."""
            },
            {
                "title": "(6) UPS statistics and reports",
                "content": """Select Option 6.

Features:
• With SNMP features enabled on your device(s), you can query devices for meaningful stats.
• Make sure to import the "snmp_enable" config included in Sidekick's folder to enable SNMP on your devices.
• Generate reports with a file listing all the IPs of the devices you wish to query.
• Reports can be generated based on parameters configured by the user in the Report view.

For more information see the README.md file in Sidekick's home folder."""
            },
            {
                "title": "Editing operation modes and files",
                "content": """Configure the application operating mode.

Available modes:
• Single (Default) - Work with one device at a time
• Batch (RDU101) - Batch operations for RDU101 devices
• Batch (IS-UNITY) - Batch operations for IS-UNITY devices

In batch mode, you must specify:
• Path to batch file (list of IP addresses)
• With only this file specified, you can perform an export operation

Optionally, you can specify:
• Path to config file (for import operations)
• Path to firmware file (for firmware updates)
"""
            },
            {
                "title": "Gotchas and Pitfalls",
                "content": """
What is a "General Failure" ?
• This is a "catchall" error used in:
    > http request error(s) besides 404 (i.e., 503 (Unavailable), 500 (Internal Server Error))
    > Broad application errors that users cannot resolve.
• For more information, check the logs produced during operation.

What if Sidekick hangs or crashes during an operation?
• If this happens, check the logs to see up to where the operation was completed.
• Check the logs for how many devices were processed.
• You may perform a restart on a per-device basis from this application, 
  or from the web.

Aborting a batch job during operation:
• Aborting does NOT guarantee request is reversed.
• Once sent to the web server, a request cannot be cancelled.
• Abort will simply terminate all active jobs to resume application."""
            }
        ]