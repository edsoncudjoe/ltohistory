import json
import ltohistory as lh
import unittest
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
sys.path.insert(0, '../Py-CatDV')
from pycatdv import Catdvlib


class TestSpaceLTOInterface(unittest.TestCase):
    """Test automation of space LTO web interface"""

    def setUp(self):
        self.lto_url = "http://192.168.0.190/login/?p=/lto/catalogue/"

    def tearDown(self):
        if self.browser:
            self.browser.quit()

    def test_firefox_browser(self):
        """Open firefox browser"""
        self.browser = lh.open_firefox_browser()
        self.browser.get(self.lto_url)
        self.assertIsInstance(self.browser,
                              webdriver.firefox.webdriver.WebDriver)
        # self.assertEqual('LTO Space Login', firefox.title.encode('utf-8'))

    def test_chrome_browser(self):
        self.browser = lh.open_chrome_browser()
        self.browser.get(self.lto_url)
        self.assertIsInstance(self.browser,
                              webdriver.chrome.webdriver.WebDriver)

    def test_download_lto_file(self):
        self.browser = lh.open_browser()
        lh.browser_login(self.browser, usr='admin', pwd='space')
        tabs = self.browser.find_elements_by_class_name("switcher-button")
        tabs[3].click()

        exp_format = self.browser.find_element_by_id("sel_exporthist_format")
        for f in exp_format.find_elements_by_tag_name("option"):
            if f.text == "JSON":
                f.click()
                break

        set_from = self.browser.find_element_by_id("txt_exporthist_from")
        set_to = self.browser.find_element_by_id("txt_exporthist_to")

        dates = lh.set_search_dates()

        if self.browser.name == 'chrome':
            set_from.clear()
            set_from.send_keys(dates[0])
            set_to.clear()
            set_to.send_keys(dates[1])
        else:
            set_from.send_keys(Keys.COMMAND + "a")
            set_from.send_keys(Keys.DELETE)
            set_from.send_keys(dates[0])
            time.sleep(1)
            set_to.send_keys(Keys.COMMAND + "a")
            set_to.send_keys(Keys.DELETE)
            set_to.send_keys(dates[1])

        time.sleep(3)
        # click on blank area to close calender
        border_click = self.browser.find_element_by_id("browse")
        border_click.click()
        time.sleep(1)

        # download file
        export = self.browser.find_element_by_id("btn_exporthist_save")
        export.click()
        time.sleep(10)

        fn = open('history.json')
        assert fn


class TestLtoHistory(unittest.TestCase):
    """Tests for collecting correct data"""

    c = None

    @classmethod
    def setUpClass(cls):
        cls.c = Catdvlib()
        cls.c.get_auth()
        cls.key = cls.c.get_session_key()

    @classmethod
    def tearDownClass(cls):
        cls.c.delete_session()

    def test_catdv_login(self):
        """Test whether login returns a successful status code"""
        self.assertEqual(len(self.key), 32)

    def test_get_lto_info(self):
        """Test data loaded from lto file loads correctly"""
        filename = open('history.json', 'r')
        assert filename
        jdata = json.load(filename)
        collection = [(i['name'], i['used_size']) for i in jdata['tapes']]
        self.assertGreater(len(collection), 1)

    def test_client_name_id(self):
        """
        Test length of created dictionary to find out if it has
        been populated.
        """
        self.c.get_catalog_name()
        self.name_id = lh.client_name_id(self.c)
        self.assertGreater(len(self.name_id), 2)

if __name__ == '__main__':
    test_classes = [TestSpaceLTOInterface, TestLtoHistory]
    load = unittest.TestLoader()

    suites_list = []
    for t_class in test_classes:
        suite = load.loadTestsFromTestCase(t_class)
        suites_list.append(suite)

    combined = unittest.TestSuite(suites_list)

    run = unittest.TextTestRunner()
    results = run.run(combined)

