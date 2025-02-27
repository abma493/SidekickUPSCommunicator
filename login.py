from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from common_imports import *
from logger import Logger


# Selenium driver set up
def setup(web: str):
    driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))
    try:
        driver.get(web)
    except WebDriverException as e:
        Logger.log(f"Failed to load page: {e}")
        return None, None

    try:
        wait = WebDriverWait(driver, default_timeout)
        wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "body")))
    except TimeoutException:
        Logger.log("Page failed to load completely.")
        driver.quit()
        return None, None

    return driver, wait


# Once a web session has been established, log in
def login(wait: WebDriverWait, driver, user : str, passwd : str) -> bool:	

	try:
		# Username in
		user_field = wait.until(EC.element_to_be_clickable((By.ID,"username")))
		user_field.clear()
		
		# Password in
		pswd_field = wait.until(EC.element_to_be_clickable((By.ID,"password")))
		pswd_field.clear()
		user_field.send_keys(user)
		pswd_field.send_keys(passwd)
		# credential verification / login
		login_b = wait.until(EC.element_to_be_clickable((By.ID, "login")))
		login_b.click()

		sleep(mini_wait)
		try:
			login_err = driver.find_element(By.ID, "loginError")
			if login_err.is_displayed():
				return False
		except NoSuchElementException:
			return True
		
	except TimeoutException:
		Logger.log("Login failed - Timeout while parsing elements\nCheck your network/VPN.")
		return False
