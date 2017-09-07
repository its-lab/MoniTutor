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

    def tearDown(self):
        self.browser.quit()

    def wait_for_page_to_load(self):
        time.sleep(.5)

    def test_user_can_sign_up(self):
        # The MoniTutor stack was just set up. In order to get everything
        # prepared for the students, the admin first needs to register.
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

        # The admin fills out the registration form
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
        self.assertRaises(NoSuchElementException,
                          self.browser.find_element_by_class_name, "error")

        # The Admin is redirected to the welcome page and is now logged in.
        # As noone assigned admin privileges to the admin yet, he can not
        # acces the admin area
        self.assertIn(u"Welcome, Monty!",
                      self.browser.find_element_by_tag_name('h1').text,
                      "Welcome greeting not found")
        self.assertRaises(NoSuchElementException,
                          self.browser.find_element_by_link_text, "Admin")

        # After reading the Welcome message, the admin wants to sign out again.
        self.browser.find_element_by_link_text(u"Welcome, Monty").click()
        self.browser.find_element_by_partial_link_text(u"Logout").click()
        self.wait_for_page_to_load()
        self.assertIn(u"Log In",
                      self.browser.find_element_by_tag_name('h2').text,
                      "Log In banner not found")

        # To gain admin privileges, the admin navigates to the web2py database
        # backend, enters the admin password and adds his user to the admin
        # group
        self.browser.get("https://localhost/admin")
        self.wait_for_page_to_load()
        self.browser.find_element_by_id("password") \
            .send_keys("admin", Keys.ENTER)
        self.wait_for_page_to_load()
        self.browser \
            .get("https://localhost/MoniTutor/appadmin/insert/tutordb/auth_membership")
        self.wait_for_page_to_load()
        options = self.browser.find_elements_by_tag_name("option")
        self.assertIn([u"admin"],
                      [option.text.split()[:1] for option in options],
                      "Group 'admin' does not exist")
        self.browser.find_element_by_id("auth_membership_user_id") \
            .send_keys("a", Keys.TAB, "a", Keys.TAB, Keys.ENTER)
        self.wait_for_page_to_load()
        self.assertIn("new record inserted",
                      self.browser.find_element_by_class_name("alert-dismissable").text,
                      "Admin membership record was not added succesfully")


if __name__ == '__main__':
    unittest.main()
