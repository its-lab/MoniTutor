from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import unittest
import time


class NewAdminTest(unittest.TestCase):

    def setUp(self):
        self.profile = webdriver.FirefoxProfile()
        self.profile.accept_untrusted_certs = True
        self.profile.assume_untrusted_cert_issuer = True
        self.browser = webdriver.Firefox(firefox_profile=self.profile,
                                         capabilities={"marionette": False})
        self.testuser = { "name": "Monty",
                          "surname": "Python",
                          "email": "monty.python@example.net",
                          "username": "administrator",
                          "password": "securepassowrd"}
        self.hostname = "localhost"
        self.admin_password = "admin"
        self.path_to_scenario_file = "~/monitutor_scenarios/example.json"


    def tearDown(self):
        self.browser.quit()

    def wait_for_page_to_load(self):
        time.sleep(1)

    def test_user_can_sign_up(self):
        # The MoniTutor stack was just set up. In order to get everything
        # prepared for the students, the admin first needs to register.
        self.browser.get("https://"+self.hostname)

        # The Admin is redirected to the Login page.
        self.assertIn(u"Log In",
                      self.browser.find_element_by_tag_name('h2').text,
                      "Log In banner not found")

        # To create a new user, the admin clicks on  Sign up and is then
        # redirected to the registration form
        submit_row = self.browser.find_element_by_id("submit_record__row")
        all_buttons = submit_row.find_elements_by_tag_name("button")
        for button in all_buttons:
            if button.text == u"Sign Up":
                button.click()
                break
        self.wait_for_page_to_load()
        self.assertIn(u"Sign Up",
                      self.browser.find_element_by_tag_name('h2').text,
                      "Sign Up banner not found")

        # The admin fills out the registration form
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
                       Keys.ENTER)
        self.wait_for_page_to_load()
        self.assertRaises(NoSuchElementException,
                          self.browser.find_element_by_class_name, "error")

        # The Admin is redirected to the welcome page and is now logged in.
        # As noone assigned admin privileges to the admin yet, he can not
        # acces the admin area
        self.assertIn(u"Welcome, "+self.testuser["name"]+"!",
                      self.browser.find_element_by_tag_name('h1').text,
                      "Welcome greeting not found")
        self.assertRaises(NoSuchElementException,
                          self.browser.find_element_by_link_text, "Admin")

        # After reading the Welcome message, the admin wants to sign out again.
        self.browser.find_element_by_link_text(u"Welcome, "+self.testuser["name"]).click()
        self.browser.find_element_by_partial_link_text(u"Logout").click()
        self.wait_for_page_to_load()
        self.assertIn(u"Log In",
                      self.browser.find_element_by_tag_name('h2').text,
                      "Log In banner not found")

        # To gain admin privileges, the admin navigates to the web2py database
        # backend, enters the admin password and adds his user to the admin
        # group
        self.browser.get("https://"+self.hostname+"/admin")
        self.wait_for_page_to_load()
        self.browser.find_element_by_id("password") \
            .send_keys(self.admin_password, Keys.ENTER)
        self.wait_for_page_to_load()
        self.browser \
            .get("https://"+self.hostname+"/MoniTutor/appadmin/insert/tutordb/auth_membership")
        self.wait_for_page_to_load()
        options = self.browser.find_elements_by_tag_name("option")
        self.assertIn([u"admin"],
                      [option.text.split()[:1] for option in options],
                      "Group 'admin' does not exist")
        self.browser.find_element_by_id("auth_membership_user_id") \
            .send_keys(self.testuser["username"], Keys.TAB, "admin", Keys.TAB, Keys.ENTER)
        self.wait_for_page_to_load()
        self.assertIn("new record inserted",
                      self.browser.find_element_by_class_name("alert-dismissable").text,
                      "Admin membership record was not added succesfully")

        # The admin now want's to create a scenario. After the login the
        # administrator uses the upload function to reuse an old scenario and
        # initiates it after the upload finishes.
        self.browser.get("https://"+self.hostname)
        self.wait_for_page_to_load()
        self.browser.find_element_by_id("auth_user_username") \
            .send_keys(self.testuser["username"],
                       Keys.TAB,
                       self.testuser["password"],
                       Keys.ENTER)
        self.wait_for_page_to_load()
        self.assertIn("Admin",
                      self.browser.find_element_by_link_text("Admin").text,
                      "Can not find admin menu after login")
        self.browser.find_element_by_link_text("Admin").click()
        self.assertIn("Scenarios",
                      self.browser.find_element_by_link_text("Scenarios").text,
                      "Can not find scenario button in admin menu")
        self.browser.find_element_by_link_text("Scenarios").click()
        self.wait_for_page_to_load()
        self.browser.find_element_by_id("new").click()
        self.wait_for_page_to_load()
        self.browser.find_element_by_id("import").click()
        self.wait_for_page_to_load()
        self.browser.find_element_by_name("scenariofile") \
            .send_keys(self.path_to_scenario_file)
        self.browser.find_element_by_id("form2").submit()
        self.wait_for_page_to_load()
        self.browser.find_element_by_id("1-init").click()
        self.wait_for_page_to_load()
        self.assertTrue(self.browser.find_element_by_class_name("progress"),
                      "Couldn't find progress bar after scenario initiation")
        max_scenario_init_time = 20
        try:
            while self.browser.find_element_by_class_name("progress-bar"):
                time.sleep(2)
                max_scenario_init_time -= 2
                if max_scenario_init_time < 1:
                    self.fail("Scenario initiation didn't finish")
        except NoSuchElementException:
            pass
        self.browser.find_element_by_class_name("fa-eye").click()


if __name__ == '__main__':
    unittest.main()
