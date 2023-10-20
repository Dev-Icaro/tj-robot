from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from common.utils.string import remove_accents
from web_scraping.pages.base_page import BasePage
from web_scraping.components.base_component import BaseComponent
import re


class CasePage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)

    empty_incident_by = (By.CSS_SELECTOR, "td#processoSemIncidentes")
    participants_by = (By.CSS_SELECTOR, "#tablePartesPrincipais tr.fundoClaro")
    private_by = (By.ID, "popupModalDiv")
    class_by = (By.ID, "classeProcesso")
    judgment_execution_by = (
        By.CSS_SELECTOR,
        "#containerDadosPrincipaisProcesso .row:nth-child(1) .unj-larger",
    )

    def has_incident(self):
        try:
            empty_incident_ele = WebDriverWait(self, 2).until
            (EC.presence_of_element_located(self.empty_incident_by))
            if empty_incident_ele:
                return False
        except:
            return True

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

    def get_class(self):
        try:
            return self.driver.find_element(*self.class_by).text
        except:
            pass


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


class TjCredentials:
    def __init__(self, cnpj, password):
        self.cnpj = cnpj
        self.password = password
