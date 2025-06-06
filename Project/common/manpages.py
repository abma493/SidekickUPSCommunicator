help_pages = [
            {
                "title": "Vertiv Communicator for UPS devices v.2.1",
                "content": """This tool allows you to configure and manage Vertiv GXT4/GXT5

Main features:
• Single device configuration
• Batch operations for multiple devices
• Firmware updates
• Network settings modification
• Configuration file import/export

Press '>' to continue or '<' to go back."""
            },
            {
                "title": "(1) Making Network Changes",
                "content": """Select Option 1.

Options available:
• Set static IP address
• Configure subnet mask
• Enable/Disable DHCP
• View current network configuration

Changes require a device restart to take effect."""
            },
            {
                "title": "(6) Restarting the web card",
                "content": """Safely restart the web card of a UPS device.

This option will:
• Save current configuration
• Restart the device web interface
• Automatically re-login after restart
• Restore your session

The process typically takes 2-3 minutes."""
            },
            {
                "title": "7. Push Batch Configuration File",
                "content": """Apply configurations to multiple devices at once.

Batch operations support:
• Export configurations from multiple devices
• Import configuration files to multiple devices
• Perform firmware updates on a batch of devices

Set up batch mode by pressing 'E - Edit' and selecting
either 'Batch (RDU101)' or 'Batch (IS-UNITY)' mode."""
            },
            {
                "title": "Editing Operation Modes and files",
                "content": """Configure the application operating mode.

Available modes:
• Single (Default) - Work with one device at a time
• Batch (RDU101) - Batch operations for RDU101 devices
• Batch (IS-UNITY) - Batch operations for IS-UNITY devices

In batch mode, you must specify:
• Path to batch file (list of IP addresses)
• Path to config file (for import operations)
• Path to firmware file (for firmware updates)"""
            },
            {
                "title": "Gotchas and Pitfalls",
                "content": """

What is a "General Failure" ?
• This is a "catchall" error for http request error besides 404.
• This error mostly presents during 503 (Unavailable) codes from server. 
• For more information, check the logs produced during operation.

Aborting a batch job during operation:
• Aborting does NOT guarantee request is reversed.
• Once sent to the server, the web server will not halt at an abort call.
• Abort will simply terminate the coroutine of this application."""
            }
        ]