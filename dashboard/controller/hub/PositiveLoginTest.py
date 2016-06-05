import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

class DemonstrationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # cls.driver = webdriver.Chrome("../node/OptiRun - Copy/drivers/chromedriver.exe")
        cls.driver = webdriver.Ie("../node/OptiRun - Copy/drivers/IEDriverServer.exe")
        # cls.driver = webdriver.Firefox()

    @classmethod
    def tearDownClass(cls):
        if cls.driver is not None:
            cls.driver.quit()

    def test_this_is_a_demonstration(self):
        driver = self.driver

        # Go to the Altibox TV Overalt start page
        driver.get("https://tvoveraltstg.altibox.no/")

        # Wait for the Login button to appear, then locate and click the button
        WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.CLASS_NAME, 'btn-login')))
        login_button = driver.find_element_by_class_name('btn-login')
        login_button.click()

if __name__ == "__main__":
    unittest.main(argv=['TestCase'])
