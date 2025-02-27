from common_imports import *
from selenium.webdriver.support.ui import Select

class IP_Opts:
        # Folder traversal (Config -> Ntwk -> IPv4)
    def __init__(self, driver, wait: WebDriverWait):
        self.driver = driver
        self.wait = wait

    def load_network_folder(self):
        self.driver.switch_to.default_content() # make sure frame context is not an issue
        self.wait.until(EC.frame_to_be_available_and_switch_to_it("navigationFrame"))

        config_folder = self.wait.until(lambda x: x.find_element(By.ID, "report164160"))
        config_folder.click()

        network_folder = self.wait.until(EC.element_to_be_clickable((By.ID, "report163850")))
        network_folder.click()

        IPv4_folder = self.wait.until(EC.element_to_be_clickable((By.ID, "report164130")))
        IPv4_folder.click()


    def set_IP(self, IP):
        # editing the IPv4 folder (in this sample we are just inserting a static IP)
        self.driver.switch_to.default_content()
        self.wait.until(EC.frame_to_be_available_and_switch_to_it("detailArea"))

        edit_b = self.wait.until(EC.element_to_be_clickable((By.ID, "editButton")))
        edit_b.click()

        if self.isset_IPv4(): # is IPv4 enabled?
            IP_field = self.wait.until(EC.element_to_be_clickable((By.ID, "str6139")))
            IP_field.send_keys(IP)
            submit_b = self.wait.until(EC.element_to_be_clickable((By.ID, "submitButton")))
            submit_b.click()


    def enable_dhcp(self):
        try:
            select_element = self.wait.until(EC.presence_of_element_located((By.ID, "enum6138")))
            dropdown = Select(select_element)
            dropdown.select_by_value("0")
            sleep(2)
        except Exception as e:
            print(f'DHCP enable operation failed: {e}')

    def get_dhcp():
        pass

    def isset_IPv4(self) -> bool:
        return self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='checkbox' and @id='chkbx6137']"))).is_selected()

        
