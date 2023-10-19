from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from common.utils.string import remove_accents
from common.constants.tj_site import BASE_URL
import re


class TjCaseSearcher:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)

    def load_case_page(self, case_number):
        case_url = BASE_URL + "/cpopg/show.do?processo.numero=" + case_number
        self.driver.get(case_url)

        wait = WebDriverWait(self.driver, 10)
        wait.until(
            lambda driver: driver.execute_script("return document.readyState")
            == "complete"
        )

        return CasePage(self.driver)

    def login(self, credentials):
        login_url = (
            BASE_URL
            + "/sajcas/login?service=https%3A%2F%2Fesaj.tjsp.jus.br%2Fesaj%2Fj_spring_cas_security_check"
        )
        self.driver.get(login_url)

        input_cnpj = self.wait.until(
            EC.element_to_be_clickable((By.ID, "usernameForm"))
        )
        input_cnpj.send_keys(credentials.cnpj)

        input_pass = self.wait.until(
            EC.element_to_be_clickable((By.ID, "passwordForm"))
        )
        input_pass.send_keys(credentials.password)

        btn_login = self.wait.until(EC.element_to_be_clickable((By.ID, "pbEntrar")))
        btn_login.click()


class CasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)

    def has_incident(self):
        empty_incident_element_ref = "td#processoSemIncidentes"

        wait = WebDriverWait(self.driver, 2)
        try:
            empty_incident_ele = wait.until
            (
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, empty_incident_element_ref)
                )
            )
            if empty_incident_ele:
                return False

        except:
            return True

    def get_exectdo_name(self):
        try:
            trs = self.driver.find_elements(
                By.CSS_SELECTOR, "#tablePartesPrincipais tr.fundoClaro"
            )
            for tr in trs:
                participation_type = tr.find_element(
                    By.CLASS_NAME, "tipodeparticipacao"
                ).text.strip()

                if (
                    participation_type == "Exectdo"
                    or participation_type == "Ré"
                    or participation_type == "Reqdo"
                    or participation_type == "Reqda"
                ):
                    name_of_party_and_lawyer = tr.find_element(
                        By.CLASS_NAME, "nomeParteEAdvogado"
                    ).text

                    # re_pattern = r'(^.+)\n|\Z'
                    re_pattern = r".*?(?:\n|$)"
                    match = re.search(re_pattern, name_of_party_and_lawyer, re.DOTALL)
                    if match:
                        exectdo = match.group(0)

                        if exectdo.endswith("\n"):
                            exectdo = exectdo[:-1]

                        return remove_accents(exectdo).upper()

                else:
                    continue

        except Exception as e:
            raise Exception("Erro ao encontrar Exectdo do processo:", e)

    def get_judgment_execution(self):
        try:
            case_info_container = self.wait.until(
                EC.presence_of_element_located(
                    (By.ID, "containerDadosPrincipaisProcesso")
                )
            )

            span_judgmente_execution = case_info_container.find_element(
                By.CSS_SELECTOR, "span.unj-larger"
            )
            judgment_execution = span_judgmente_execution.text

            return judgment_execution

        except Exception as e:
            raise Exception("Erro ao encontrar a execução de sentença:", e)

    def is_private(self):
        reference_ele_id = "popupModalDiv"
        try:
            self.driver.find_element(By.ID, reference_ele_id)
            return True
        except NoSuchElementException as e:
            return False

    def get_class(self):
        class_ele_id = "classeProcesso"
        class_ele = self.driver.find_element(By.ID, class_ele_id)

        if class_ele:
            return class_ele.text


class TjCredentials:
    def __init__(self, cnpj, password):
        self.cnpj = cnpj
        self.password = password
