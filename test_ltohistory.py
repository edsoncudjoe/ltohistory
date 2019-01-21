import glob
import json
import os
import unittest
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

import ltohistory as lh
from pycatdv import Catdvlib

from ltohistory import LTOHistory

class LTOHistoryTests(unittest.TestCase):

    def setUp(self):
        self.a = LTOHistory('192.168.0.101:8000', '4', '192.168.16.99')


    def test_catdv_api_version(self):
        self.assertEqual(self.a.api, '4')

    def test_catdv_server_url(self):
        self.assertEqual(self.a.server, '192.168.0.101:8000')

    def test_set_lto_date_range(self):
        date_range = self.a.set_lto_date_range()
        self.assertEqual(type(date_range), type(()))

    def test_open_chrome_browser(self):
        tab = self.a.open_chrome_browser()
        self.assertEqual(tab.title.encode('utf-8'), 'LTO Space Login')
        tab.quit()

    def test_download_lto_history_file(self):
        window = self.a.open_browser()
        self.a.browser_login('admin', 'space')
        tabs = window.find_elements_by_class_name("switcher-button")
        self.assertEqual(type(tabs), type([]))

        # Find boxes to set date range
        set_from = window.find_element_by_id("txt_exporthist_from")
        self.assertEqual(type(set_from), webdriver.remote.webelement.WebElement)

        window.quit()


class TestSpaceLTOInterface(unittest.TestCase):
    """Test automation of space LTO web interface"""

    def setUp(self):
        self.lto_url = "http://192.168.0.190/login/?p=/lto/catalogue/"

    def tearDown(self):
        if self.browser:
            self.browser.quit()

    @unittest.skip("No longer used")
    def test_firefox_browser(self):
        """Open firefox browser"""
        self.browser = lh.open_firefox_browser()
        self.browser.get(self.lto_url)
        self.assertIsInstance(self.browser,
                              webdriver.firefox.webdriver.WebDriver)
        # self.assertEqual('LTO Space Login', firefox.title.encode('utf-8'))
    @unittest.skip("skipped during main rebuild")
    def test_chrome_browser(self):
        """Open the Chrome driver"""
        self.browser = lh.open_chrome_browser()
        self.browser.get(self.lto_url)
        self.assertIsInstance(self.browser,
                              webdriver.chrome.webdriver.WebDriver)
    @unittest.skip("skipped during main rebuild")
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
        cls.c = Catdvlib(server_url='192.168.0.101:8080', api_vers=4)
        cls.c.set_auth(username='web', password='python')
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
        self.assertGreater(len(collection), 1, 'list should not be empty')

    def test_client_name_id(self):
        """
        Test length of created dictionary to find out if it has
        been populated.
        """
        self.c.get_catalog_name()
        self.name_id = lh.client_name_id(self.c)
        self.assertGreater(len(self.name_id), 2)

    @unittest.skip("No longer used")
    def test_total_sizes(self):
        clients = {u'NGTV': 4627, u'ContentMedia': 66924, u'Power': 1602,
                   u'Dreamworks': 15653}
        lto_info = [('IV0624', 1.17), ('IV0625', 1.17)]
        lh.total_sizes(client_dict=clients, name_size=lto_info)
        pass

    def test_calculate_written_data(self):
        lto_info = lh.get_lto_info()
        self.c.get_catalog_name()
        names = lh.client_name_id(self.c)
        group_data = lh.calculate_written_data(lto_info, names,
                                               server=self.c.server,
                                               api_vers=self.c.api,
                                               key=self.c.key)
        self.assertEqual(type(group_data), type({}), 'group data shoud be a '
                                                     'dictionary')
        self.assertIn('NGTV', group_data.keys(), 'NGTV should be one of the '
                                                 'group names')

if __name__ == '__main__':
    test_classes = [LTOHistoryTests, TestSpaceLTOInterface, TestLtoHistory]
    load = unittest.TestLoader()

    suites_list = []
    for t_class in test_classes:
        suite = load.loadTestsFromTestCase(t_class)
        suites_list.append(suite)

    combined = unittest.TestSuite(suites_list)

    run = unittest.TextTestRunner()
    results = run.run(combined)

