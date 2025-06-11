from common.common_term import *
from common.common_imports import *
from syncprims import send_request
from .QuitScreen import QuitScreen
from .PushChangesScreen import PushChangesScreen
from .NotifMsgScreen import NotifMsgScreen
from .ConfirmationScreen import ConfirmationScreen
from restart_card import restart_a_card
from logger import Logger
from http_session import http_session
import csv
import glob
import ipaddress
from pathlib import Path

class ModNetworkScreen(ModalScreen):
    
    CSS_PATH="../assets/modntwk_screen.css"
    BINDINGS = [
        ("q", "quit_app"),
        ("b", "back_menu"),
        ("up", "focus_previous"),
        ("down", "focus_next"),
        ("left", "focus_previous"), 
        ("right", "focus_next"),
    ]
    
    async def on_mount(self):
        
        self.dhcp_checkbox: Checkbox = self.query_one("#dhcp-checkbox")
        self.current_ip = self.query_one("#current-ip", Static)
        self.current_subnet = self.query_one("#current-subnet", Static)
        self.dhcp_checkbox.disabled = True
        self.dhcp_changed = False #flag to track if dhcp was modded, not the value itself
        self.pending_dhcp_change = self.dhcp_changed #by default
        self.set_flag = False
        self.path_to_batch = ""
        self.call_after_refresh(self.load_resources)

    def handle_task_result(self, task):
        # Check for exceptions
        if task.cancelled():
            Logger.log("Network data task was cancelled")
        elif task.exception():
            Logger.log(f"Network data task failed: {task.exception()}")

    # Pre-populate current Network settings 
    async def load_resources(self):
        try: 

            ntwk_dat = await send_request("GET_NTWK_OPS")
            ntwk_dict = dict(ntwk_dat)        
            ip = ntwk_dict['Static IP Address']
            subnet = ntwk_dict['Subnet Mask']
            dhcp = "ON" if int(ntwk_dict['IP Address Method']) == 1 else "OFF"
            Logger.log(f"received: [IP: {ip}], [subnet: {subnet}], [dhcp: {dhcp}]")
    
            self.current_ip.update(f"Current IP: {ip}" if ip else "Current IP: ERROR")
            self.current_subnet.update(f"Current subnet: {subnet}" if subnet else "Current subnet: ERROR")
            self.dhcp_checkbox.label = "Set DHCP (Currently: ON)" if dhcp else "Set DHCP (Currently: OFF)"
            self.dhcp_checkbox.disabled = False
            self.dhcp_checkbox.value = dhcp
            
        except Exception as e:
            Logger.log(f"Error fetching network data {e}")


    def compose(self) -> ComposeResult:
        yield Grid(
            Container(
                Label("Basic Network Settings"),
                Checkbox(f"Set DHCP (Currently: LOADING)", id="dhcp-checkbox"), 
                Vertical(
                    Horizontal(
                        Static("IP address:", id="ip-label"),
                        Input(placeholder="IP address", id="ip-field"),
                    id="ip-field-container"),
                    Horizontal(
                        Static("Subnet mask:", id="subnet-label"),
                        Input(placeholder="Subnet mask", id="subnet-mask-field"),
                    id="subnet-field-container"),
                    Horizontal(
                        Input(id="path-to-csv", placeholder="Path to batch file (.csv)", disabled=False),
                    id="csv-field-container"),
                id="upper-fields-container"),
                Horizontal(
                          Button("SET", id="set-button"),
                          Button("Apply Changes", id="apply-button"),
                          Button("Run Batch", id="run-button", disabled=True)),
                Vertical(
                        Static(f"Current IP: LOADING", id="current-ip"),
                        Static(f"Current subnet: LOADING", id="current-subnet"),
                id="current-network-settings"),
            id="configurations"),
            ListView(
                ListItem(Label(f"No data available.")),
                id="devices-update"),
            Horizontal(
                       Button("Q - Quit", id="quit-button"),
                       Button("B - Back", id="back-button"),
                       Label("Mode: Single (Default)", id="status-label"),
                 id="options"),
        id="ntwk-config-grid")

    def action_focus_next(self):
        self.focus_next()

    def action_focus_previous(self):
        self.focus_previous()

    def action_quit_app(self) -> None:
        self.app.push_screen(QuitScreen())

    @on(Button.Pressed, "#quit-button")
    def on_quit_pressed(self) -> None:
        self.app.push_screen(QuitScreen())

    def action_back_menu(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#set-button")
    async def on_set_pressed(self):
        ip_field = self.query_one("#ip-field", Input)
        subnet_mask_field = self.query_one("#subnet-mask-field", Input)
        if not ip_field.value or not subnet_mask_field.value:
            self.app.push_screen(NotifMsgScreen("One or more fields are empty.\nPlease enter valid values before setting changes."))
            return

        success: bool = await send_request("HOLD_CHANGES", {
            "Network.IPv4": [
                ("IP Address Method", "1" if self.dhcp_checkbox.value else "0"),
                ("Static IP Address", str(ip_field.value)),
                ("Subnet Mask", str(subnet_mask_field.value))
            ]           
        })
        self.set_flag = success # important in case apply changes is hit first
        notif_message = "Select Apply Changes now or at the main menu to push\n      all changes made to this device."
        if not success:
            Logger.log("Failure to update internal data structure [temp_dat] with values" + 
                       f"{ip_field.value}, {subnet_mask_field.value}, {self.dhcp_checkbox.value}")
            notif_message = "Failure setting user values locally. Either you submitted empty values or check log for details."
        self.app.push_screen(NotifMsgScreen(notif_message))
    
    @on(Button.Pressed, "#apply-button")
    async def on_apply_pressed(self):
        if self.set_flag:
            self.app.push_screen(PushChangesScreen())
        else:
            self.app.push_screen(NotifMsgScreen("No changes have been set.\nPlease set changes before applying."))

    @on(Checkbox.Changed, "#dhcp-checkbox")
    def handle_dhcp_checkbox(self, event: Checkbox.Changed):
        # save the value here, True for clicked, False for unclicked
        self.dhcp_changed = True 
        self.pending_dhcp_change = event.value

    @on(Input.Changed, "#path-to-csv")
    def handle_input_change(self, event: Input.Changed):
        run_button = self.query_one("#run-button")
        path: str = event.value.strip()
        self.path_to_batch = path
        run_button.disabled = not bool(path)

    @on(Button.Pressed, "#run-button")
    def on_run_batch_pressed(self):

        test_path = "\\".join([str(os.path.dirname(os.path.abspath(self.path_to_batch))), self.path_to_batch])
        if not os.path.exists(test_path): # verify file exists
            self.app.push_screen(NotifMsgScreen("Batch file not found. Check file path and try again."))
            return
        
        path_verified = Path(self.path_to_batch) # verify file is .csv
        if path_verified.suffix.lower() != '.csv':
            self.app.push_screen(NotifMsgScreen("Invalid file type.\nPlease select a .csv file."))
            return
        
        # get the list widget
        devices_listv = self.query_one("#devices-update", ListView)

        valid_entries: list = self.parse_batch_file()
        if not valid_entries: # if no valid entries in csv display this one
            Logger.log("no valid entries")
            devices_listv.append(ListItem(Label(f"No valid entries found.\n"))) 
            return

        invalid_i = int(valid_entries[-1]) # last list item is the # of invalid entries
        valid_entries.pop() # pop the invalid count
        devices_listv.clear() # clear it to prepare loading stuff on it

        for i, entry in enumerate(valid_entries, start=1): # add all the entries to the list view widget
            entry_id: str = entry['old_ip'].replace('.', '-')
            devices_listv.append(
                ListItem(
                    Label(f"Job #{i} [{entry['old_ip']}]", id=f"job-{entry_id}", markup=False), 
                    Label("Status: READY", id=f"status-{entry_id}"),
                    id=f"dev-{entry_id}")
            )

        total_processed = len(valid_entries) + invalid_i
        summary_msg = f"Batch file processed with {len(valid_entries)}/{total_processed} valid entries.\n{invalid_i} skipped.\n"
        summary_msg+= f"Are you sure you want to continue? (Invalid addresses or disabling DHCP may require a physical setup.)"
        
        # callback to be used after confirmation
        async def retrieve_choice(decision: bool):
            if decision: # perform the login each time
                self.app.run_worker(self.run_operations(valid_entries), exclusive=True)
            else:
                devices_listv.clear()
                devices_listv.append(ListItem(Label(f"No data available.\n"))) 
        
        self.app.push_screen(ConfirmationScreen(summary_msg), retrieve_choice)

    # run all the tasks associated with the valid entries to be processed
    # needs to be run in a worker thread so that the UI is not blocked and can be updated (like BatchScreen tasks)
    async def run_operations(self, valid_entries: list):
        tasks = [asyncio.create_task(self.perform_ntwk_change(entry)) for entry in valid_entries]
        await asyncio.gather(*tasks)
        for f in glob.glob("ini*.txt"):
            try:
                os.remove(f)
            except FileNotFoundError:
                pass

    # Parse the batch file and return a list of valid entries to be displayed
    # on the ListView widget. This function will validate the file and each entry.
    def parse_batch_file(self) -> list: 
        valid_entries = []
        invalid_i = 0
        try:
            with open(self.path_to_batch, 'r', newline='', encoding='utf-8') as f:
                sample = f.read(1024)
                f.seek(0)
                sniffer = csv.Sniffer()
                delim = sniffer.sniff(sample).delimiter

                reader = csv.DictReader(f, delimiter=delim)

                if reader.fieldnames:
                    headers = {header.lower().strip(): header for header in reader.fieldnames}
                else:
                    self.app.push_screen(NotifMsgScreen("CSV file may be be empty or invalid."))
                    return
                
                for row_n, row in enumerate(reader, start=2):

                    try:
                        old_ip_field = None
                        new_ip_field = None
                        subnet_field = None
                        dhcp_field = None
                    
                        for key in ['login ip', 'login', 'old ip', 'old', 'old ip field']:
                            if key in headers:
                                old_ip_field = row[headers[key]].strip()
                                break
                        for key in ['new ip', 'new', 'new ip field']:
                            if key in headers:
                                new_ip_field = row[headers[key]].strip()
                                break

                        for key in ['subnet', 'subnet mask', 'mask']:
                            if key in headers:
                                subnet_field = row[headers[key]].strip()
                                break
                        for key in ['dhcp','dhcp enabled', 'dhcp on']:
                            if key in headers:
                                dhcp_field = row[headers[key]].strip()
                                break
                        
                        if not old_ip_field or not new_ip_field or not subnet_field:
                            Logger.log(f"Required field in row missing - o:{old_ip_field} / n:{new_ip_field} / m:{subnet_field}")
                            invalid_i+=1 
                            continue
                        try: # validating IP address
                            ipaddress.IPv4Address(old_ip_field)
                            ipaddress.IPv4Address(new_ip_field)
                        except ipaddress.AddressValueError:
                            Logger.log(f"Row #{row_n} address parsing error - o:[{old_ip_field}] n:[{new_ip_field}]")
                            invalid_i+=1
                            continue
                        try: # validating subnet mask
                            if subnet_field.startswith('/'):
                                cidr = int(subnet_field[1:])
                                if not 0 <= cidr <= 32:
                                    raise ValueError(f"Invalid CIDR range provided {cidr}")
                                subnet_field = self.cidr_to_mask(cidr) # convert the CIDR notation to a subnet mask
                            else:
                                ipaddress.IPv4Address(subnet_field)
                        except (ValueError, ipaddress.AddressValueError):
                            Logger.log(f"Row #{row_n} subnet parsing error - m:[{subnet_field}]")
                            invalid_i+=1
                            continue

                        dhcp_enabled = True  # Default value
                        if dhcp_field:
                            dhcp_lower = dhcp_field.lower()
                        if dhcp_lower in ['false', 'no', 'off', 'disabled']:
                            dhcp_enabled = False
                        elif dhcp_lower in ['true', 'yes', 'on', 'enabled']:
                            dhcp_enabled = True

                        # add the verified entry
                        valid_entries.append({
                            'old_ip': old_ip_field,
                            'new_ip': new_ip_field,
                            'subnet': subnet_field,
                            'dhcp': dhcp_enabled
                        })
                    except Exception as e:
                        raise
                valid_entries.append(invalid_i)
                return valid_entries
        except FileNotFoundError:
            self.app.push_screen(NotifMsgScreen("Batch file not found."))
        except PermissionError:
            self.app.push_screen(NotifMsgScreen("Permission denied accessing batch file."))
        except UnicodeError:
            self.app.push_screen(NotifMsgScreen("Failure reading file.\nValidate file is of CSV format with UTF-8 encoding."))
        except csv.Error as e:
            self.app.push_screen(NotifMsgScreen(f"CSV parsing error:\n{str(e)}"))
        except Exception as e:
            Logger.log(f"Unexpected error processing CSV: {str(e)}")
            self.app.push_screen(NotifMsgScreen("General failure processing the CSV file."))

    # Perform the network change operation for a single entry
    # A temporary ini file is created with the new settings and imported to the device
    async def perform_ntwk_change(self, entry: dict):
        
        dhcp_method = "1" if entry['dhcp'] else "0"
        stat_label = self.query_one(f"#status-{entry['old_ip'].replace('.', '-')}")
        ini_content = f"""[Network.IPv4]
        IP Address Method: {dhcp_method}
        Static IP Address: {entry['new_ip']}
        Subnet Mask: {entry['subnet']}
        """
        # Create a temporary ini format txt file to change settings
        tmp_ini_file = f"ini-{entry['old_ip'].replace('.', '-')}.txt"
        with open(tmp_ini_file, 'w') as f:
            f.write(ini_content)

        credentials = await send_request("REQ_CREDS")
        stat_label.update("Status: IN PROGRESS")
        success = await http_session(entry['old_ip'], credentials[0], credentials[1], Operation.IMPORT, tmp_ini_file)
        if success: # import success, neeeds a restart
            stat_label.update("Status: UPLOAD COMPLETE. RESTARTING CARD")
            restart_success = await restart_a_card(entry['old_ip'], credentials[0], credentials[1])
            if restart_success: # import and restart success
                stat_label.update(f"Status: DONE")
            else: # restart failed
                stat_label.update(f"Status: RESTART FAILED")
                Logger.log(f"Restart failed for device {entry['old_ip']}")
        else: # import failed
            stat_label.update(f"Status: FAILED")

    @staticmethod
    def cidr_to_mask(cidr: int):
        ntwk = ipaddress.IPv4Network(f"0.0.0.0/{cidr}", strict=False)
        mask = (str(ntwk.netmask))
        return mask