from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import unittest
import time


class MoniTutorWebTest(unittest.TestCase):

    def setUp(self):
        self.profile = webdriver.FirefoxProfile()
        self.profile.accept_untrusted_certs = True
        self.profile.assume_untrusted_cert_issuer = True
        self.browser = webdriver.Firefox(firefox_profile=self.profile)
        self.testuser = {"name": "Monty",
                         "surname": "Python",
                         "email": "monty.python@example.net",
                         "username": "administrator",
                         "hmac_secret": "securehmacsecret",
                         "password": "securepassword"}
        self.hostname = "localhost"
        self.admin_password = "admin"
        self.path_to_scenario_file = "~/monitutor_scenarios/example.json"

    def tearDown(self):
        self.browser.quit()

    def wait_for_page_to_load(self):
        time.sleep(1)

    def login(self):
        self.browser.find_element_by_id("auth_user_username") \
            .send_keys(self.testuser["username"],
                       Keys.TAB,
                       self.testuser["password"],
                       Keys.ENTER)

    def register(self):
        # The user fills out the registration form
        self.browser.find_element_by_id("auth_user_first_name") \
            .send_keys(self.testuser["name"],
                       Keys.TAB,
                       self.testuser["surname"],
                       Keys.TAB,
                       self.testuser["email"],
                       Keys.TAB,
                       self.testuser["username"],
                       Keys.TAB,
                       self.testuser["password"],
                       Keys.TAB,
                       self.testuser["password"],
                       Keys.TAB,
                       self.testuser["hmac_secret"],
                       Keys.ENTER)
        self.wait_for_page_to_load()
        self.assertRaises(NoSuchElementException,
                          self.browser.find_element_by_class_name, "error")

    def logout(self):
        self.browser.find_element_by_link_text(u"Welcome, " +
                                               self.testuser["name"]).click()
        self.browser.find_element_by_partial_link_text(u"Logout").click()

    def click_sign_up_button(self):
        submit_row = self.browser.find_element_by_id("submit_record__row")
        self.click_button_with_text_inside_element(submit_row, u"Sign Up")

    def click_button_with_text_inside_element(self, element, button_text):
        all_buttons = element.find_elements_by_tag_name("button")
        for button in all_buttons:
            if button.text == button_text:
                button.click()
                break

    def get_panel_element_by_header_text(self, header_text):
        for panel in self.browser.find_elements_by_class_name("panel"):
            if header_text in panel.find_element_by_class_name("panel-heading").text:
                return panel
        raise NoSuchElementException
