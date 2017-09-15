from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from monitutorTestCases import MoniTutorWebTest
import unittest
import time


class AdminTests(MoniTutorWebTest):

    def test_create_user(self):
        # The MoniTutor stack was just set up. In order to get everything
        # prepared for the students, the admin first needs to register.
        self.browser.get("https://"+self.hostname)

        # The Admin is redirected to the Login page.
        self.assertIn(u"Log In",
                      self.browser.find_element_by_tag_name('h2').text,
                      "Log In banner not found")

        # To create a new user, the admin clicks on  Sign up and is then
        # redirected to the registration form
        self.click_sign_up_button()
        self.wait_for_page_to_load()
        self.assertIn(u"Sign Up",
                      self.browser.find_element_by_tag_name('h2').text,
                      "Sign Up banner not found")
        self.register()

        # The Admin is redirected to the welcome page and is now logged in.
        # As noone assigned admin privileges to the admin yet, he can not
        # acces the admin area
        self.assertIn(u"Welcome, "+self.testuser["name"]+"!",
                      self.browser.find_element_by_tag_name('h1').text,
                      "Welcome greeting not found")
        self.assertRaises(NoSuchElementException,
                          self.browser.find_element_by_link_text, "Admin")

        # After reading the Welcome message, the admin wants to sign out again.
        self.logout()
        self.wait_for_page_to_load()
        self.assertIn(u"Log In",
                      self.browser.find_element_by_tag_name('h2').text,
                      "Log In banner not found")

    def test_gain_admin_privs(self):
        # To gain admin privileges, the admin navigates to the web2py database
        # backend, enters the admin password and adds his user to the admin
        # group
        self.browser.get("https://"+self.hostname+"/admin")
        self.wait_for_page_to_load()
        self.browser.find_element_by_id("password") \
            .send_keys(self.admin_password, Keys.ENTER)
        self.wait_for_page_to_load()
        self.browser \
            .get("https://" +
                 self.hostname +
                 "/MoniTutor/appadmin/insert/tutordb/auth_membership")
        self.wait_for_page_to_load()
        options = self.browser.find_elements_by_tag_name("option")
        self.assertIn([u"admin"],
                      [option.text.split()[:1] for option in options],
                      "Group 'admin' does not exist")
        self.browser.find_element_by_id("auth_membership_user_id") \
            .send_keys(self.testuser["username"],
                       Keys.TAB,
                       "admin",
                       Keys.TAB,
                       Keys.ENTER)
        self.wait_for_page_to_load()
        self.assertIn("new record inserted",
                      self.browser.find_element_by_class_name("alert-dismissable").text,
                      "Admin membership record was not added succesfully")

    def test_import_and_init_scenario(self):
        # The admin now want's to create a scenario. After the login the
        # administrator uses the upload function to reuse an old scenario and
        # initiates it after the upload finishes.
        self.browser.get("https://"+self.hostname)
        self.wait_for_page_to_load()
        self.login()
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
        self.wait_for_page_to_load()
        self.browser.find_element_by_class_name("fa-eye").click()


class UserTests(MoniTutorWebTest):

    def get_panel_element_by_header_text(self, header_text):
        for panel in self.browser.find_elements_by_class_name("panel"):
            if header_text in panel.find_element_by_class_name("panel-heading").text:
                return panel
        raise NoSuchElementException

    def test_start_a_scenario(self):
        # A student want's to start working on a scenario. After the login,
        # the student sees the welcome screen and a button that says
        # "Available Scenarios".
        self.browser.get("https://"+self.hostname)
        self.login()
        self.wait_for_page_to_load()
        self.assertIn(
            u"Available scenarios",
            self.browser
                .find_element_by_link_text(u"Available scenarios").text,
            "Available scenarios button not found after login")
        self.browser.find_element_by_link_text(u"Available scenarios") \
            .click()
        self.wait_for_page_to_load()

        # After the button was clicked, the user selects the Scenario with the
        # caption "Scenario used for functional tests" and clicks on the
        # "Start scenario" button
        try:
            scenario_panel = \
                self.get_panel_element_by_header_text("Scenario used for functional tests")
        except NoSuchElementException:
            self.fail("Scenario 'Scenario used for functional tests' not available")
        scenario_panel.find_element_by_class_name("init").click()

        # A loading bar apears and a message tells the student to be patient
        # while the scenario is starting up. To pass some time,
        # the student gets himself a coffee while the process finishes
        self.wait_for_page_to_load()
        self.assertIn("Please be patient",
                      scenario_panel.find_element_by_class_name("init").text,
                      "Loading indicator not found after starting scenario")
        max_scenario_init_time = 20
        try:
            while scenario_panel.find_element_by_class_name("init"):
                time.sleep(2)
                max_scenario_init_time -= 2
                if max_scenario_init_time < 1:
                    self.fail("Scenario initiation didn't finish")
        except NoSuchElementException:
            pass
        except StaleElementReferenceException:
            pass

    def test_check_scenario_progress(self):
        # After the initiation process is finished, the student clicks on
        # "Show progress"
        self.browser.get("https://"+self.hostname)
        self.login()
        self.wait_for_page_to_load()
        self.browser.find_element_by_link_text(u"Available scenarios").click()
        self.wait_for_page_to_load()
        scenario_panel = \
            self.get_panel_element_by_header_text("Scenario used for functional tests")
        self.assertIn(u"Show progress",
                      scenario_panel.find_element_by_link_text("Show progress").text,
                      "'Show progress' button not found after scenario start")
        scenario_panel.find_element_by_link_text("Show progress").click()
        self.wait_for_page_to_load()

        # The Student is now presented with his scenario-progress
        self.assertIn("Scenario - Scenario used for functional tests",
                      self.browser.find_element_by_class_name("active").text,
                      "Couldn't find name of scenario in breadcrumb")

        # Before the student starts working ob the objectives, he or she checks
        # if the 'ITS Client' host is connected to the MoniTutor system by
        # clicking on the refresh button left of the ITS Client panel.
        self.assertIn(u"ITS Client",
                      [host.text for host in
                          self.browser.find_elements_by_class_name("col-sm-4")],
                      "Host 'ITS Client' not found on Page")
        for host_row in self.browser.find_elements_by_css_selector(".row"):
            if "ITS Client" in host_row.find_element_by_class_name("col-sm-4").text:
                itsclient_row = host_row
                break
        max_time = 40
        while "Connected" not in itsclient_row.find_element_by_class_name("col-sm-6").text:
            itsclient_row.find_element_by_class_name("fa-refresh").click()
            time.sleep(2)
            max_time -= 2
            self.failIf(max_time <= 0, "ITS Client is not connected")

        # After the status of ITS Client changed to Connected, the student
        # clicks on the refresh button of the first milestone in oderder to see
        # if anything is left to do.
        self.assertIn("Stage 1 tests",
                      [panel.text for
                       panel in
                       self.browser.find_elements_by_class_name("panel-body")],
                      "Milestone 'Stage 1 tests' not found")
        self.browser.find_element_by_css_selector(".fa-refresh.milestone").click()
        max_time = 40
        try:
            while "fa-spinner" in self.browser \
              .find_element_by_class_name("fa-pulse") \
              .get_attribute("class"):
                time.sleep(1)
                max_time -= 1
                self.failIf(max_time <= 0)
        except NoSuchElementException:
            pass
        expected_check_results = \
            {"Ping test with variable susbstitution":
                u"1 packets transmitted, 1 packets received, 0% packet lossOK",
             "Find /etc/hosts":
                u"OK - exists",
             "Find /etc/hosty":
                u"ERROR - Datei /etc/hosty nicht gefunden"
             }
        for check_name in expected_check_results:
            self.assertIn(expected_check_results[check_name],
                          [message.text
                           for message
                           in self.browser.find_elements_by_class_name("col-sm-6")],
                          check_name+" reutrned unexpected result")


if __name__ == '__main__':
    adminTests = unittest.TestLoader().loadTestsFromTestCase(AdminTests)
    userTests = unittest.TestSuite()
    userTests.addTest(UserTests("test_start_a_scenario"))
    runner = unittest.TextTestRunner()
    runner.run(adminTests)
    runner.run(userTests)
