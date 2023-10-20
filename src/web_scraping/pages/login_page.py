from web_scraping.pages.base_page import BasePage
from common.constants.tj_site import LOGIN_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class LoginPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)

        if not "sajcas/login" in driver.current_url:
            self.driver.get()
            self.wait_load()

    username_by = (By.ID, "usernameForm")
    password_by = (By.ID, "passwordForm")
    login_button_by = (By.ID, "pbEntrar")

    def type_username(self, username):
        self.wait.until(EC.presence_of_element_located(self.username_by)).send_keys(
            username
        )

    def type_password(self, password):
        self.wait.until(EC.presence_of_element_located(self.password_by)).send_keys(
            password
        )

    def submit_login(self):
        self.wait.until(EC.element_to_be_clickable(self.login_button_by)).click()

    def login_as(self, username, password):
        self.type_username(username)
        self.type_password(password)
        self.submit_login()

        return self
