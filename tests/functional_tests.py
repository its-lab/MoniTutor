from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import unittest
import time


class NewAdminTest(unittest.TestCase):

    def setUp(self):
        self.profile = webdriver.FirefoxProfile()
        self.profile.accept_untrusted_certs = True
        self.profile.assume_untrusted_cert_issuer = True
        self.browser = webdriver.Firefox(firefox_profile=self.profile,
                                         capabilities={"marionette": False})

    def tearDown(self):
        self.browser.close()

    def wait_for_page_to_load(self):
        time.sleep(.5)

    def test_user_can_sign_up(self):
        # The MoniTutor stack was just set up. In order to get everything
        # prepared for the students, he first needs to register.
        self.browser.get("https://localhost")

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

        # The admin fills out the registration form and is redirected to the
        # welcome page
        self.browser.find_element_by_id("auth_user_first_name") \
            .send_keys("Monty",
                       Keys.TAB,
                       "Python",
                       Keys.TAB,
                       "montypython@example.com",
                       Keys.TAB,
                       "administrator",
                       Keys.TAB,
                       "securepassword",
                       Keys.TAB,
                       "securepassword",
                       Keys.ENTER)
        self.wait_for_page_to_load()

        # The Admin is redirected to the welcome page and is now logged in
        self.assertIn(u"Welcome, Monty!",
                      self.browser.find_element_by_tag_name('h1').text,
                      "Welcome greeting not found")


if __name__ == '__main__':
    unittest.main()
