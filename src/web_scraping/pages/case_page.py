from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.relative_locator import locate_with
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from common.utils.string import remove_accents
from common.constants.tj_site import BASE_URL
from web_scraping.common.exceptions.invalid_page_exception import InvalidPageException
from web_scraping.pages.base_page import BasePage
from web_scraping.components.base_component import BaseComponent
import re


class CasePage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)

        if not "processo.codigo" in self.driver.current_url:
            raise InvalidPageException("Esta não é a página de um processo")

    participants_by = (By.CSS_SELECTOR, "#tablePartesPrincipais tr.fundoClaro")
    private_by = (By.ID, "popupModalDiv")
    class_by = (By.ID, "classeProcesso")
    main_case_by = (By.CLASS_NAME, "processoPrinc")
    judgment_execution_by = (
        By.CSS_SELECTOR,
        "#containerDadosPrincipaisProcesso .row:nth-child(1) .unj-larger",
    )
    incidents_by = (By.CSS_SELECTOR, "a.incidente")

    def has_incident(self):
        try:
            self.get_incidents()
            return True
        except NoSuchElementException:
            return False

    def get_exectdo_name(self):
        participants = self.get_participants()
        for participant in participants:
            if participant.get_type() in ["Exectdo", "Ré", "Reqdo", "Reqda"]:
                return participant.get_name()
            else:
                continue

    def get_participants(self):
        participants = self.driver.find_elements(*self.participants_by)
        return [Participant(participant) for participant in participants]

    def get_judgment_execution(self):
        try:
            return self.driver.find_element(*self.judgment_execution_by).text
        except:
            pass

    def is_private(self):
        try:
            self.driver.find_element(*self.private_by)
            return True
        except NoSuchElementException:
            return False

    def navigate_to_main_case(self):
        self.driver.find_element(*self.main_case_by).click()
        return CasePage(self.driver)

    def has_main_case(self):
        try:
            self.driver.find_element(*self.main_case_by)
            return True
        except NoSuchElementException:
            return False

    def get_class(self):
        try:
            return self.driver.find_element(*self.class_by).text
        except:
            pass

    def get_incidents(self):
        incidents = self.driver.find_elements(*self.incidents_by)
        return [Incident(incident) for incident in incidents]


class Participant(BaseComponent):
    def __init__(self, root):
        super().__init__(root)

    type_by = (By.CLASS_NAME, "tipodeparticipacao")
    name_by = (By.CLASS_NAME, "nomeParteEAdvogado")

    def get_type(self):
        return self.root.find_element(*self.type_by).text.strip()

    def get_name(self):
        part_name = self.root.find_element(*self.name_by).text
        re_pattern = r".*?(?:\n|$)"
        match = re.search(re_pattern, part_name, re.DOTALL)
        if match:
            part_name = match.group(0)

            if part_name.endswith("\n"):
                part_name = part_name[:-1]

            return remove_accents(part_name).upper()


class Incident(BaseComponent):
    def __init__(self, root):
        super().__init__(root)
        self.case_class = self.root.text
        self.link = self.root.get_attribute("href")

    def get_case_link(self):
        return self.link

    def get_class(self):
        return self.case_class
