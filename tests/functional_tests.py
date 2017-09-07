from selenium import webdriver
import unittest


class NewAdminTest(unittest.TestCase):

    def setUp(self):
        self.profile = webdriver.FirefoxProfile()
        self.profile.accept_untrusted_certs = True
        self.browser = webdriver.Firefox(firefox_profile=self.profile)

    def tearDown(self):
        self.browser.close()

    def test_can_register_and_init_new_scenario_via_upload(self):
        # The MoniTutor stack was just set up. In order to get everything
        # prepared for the students, he first needs to register.
        self.browser.get("https://localhost")

        # The Admin is redirected to the Login page.
        self.assertIn(u"Log In",
                      self.browser.find_element_by_tag_name('h2').text,
                      "Log In banner not found")


if __name__ == '__main__':
    unittest.main()
