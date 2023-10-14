from selenium.webdriver.support.ui import WebDriverWait
class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)

    def wait_load(self):
        self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")