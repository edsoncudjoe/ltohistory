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

class SpaceLTOTests(unittest.TestCase):

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
    
    @unittest.skip("Update Geckodriver/Selenium before running")
    def test_open_firefox_browser(self):
        window = self.a.open_firefox_browser()
        self.assertEqual(window.title.encode('utf-8'), 'LTO Space Login')
        window.quit()
        
    def test_download_lto_history_file(self):
        window = self.a.open_browser()
        self.a.browser_login('admin', 'space')
        tabs = window.find_elements_by_class_name("switcher-button")
        self.assertEqual(type(tabs), type([]))

        # Find boxes to set date range
        set_from = window.find_element_by_id("txt_exporthist_from")
        set_to = window.find_element_by_id("txt_exporthist_to")
        self.assertEqual(type(set_from), webdriver.remote.webelement.WebElement)
        self.assertEqual(type(set_to), webdriver.remote.webelement.WebElement)

        # check download btn exists
        export = window.find_element_by_id("btn_exporthist_save")
        self.assertEqual(type(export), webdriver.remote.webelement.WebElement)
        window.quit()

    def test_get_lto_info_no_file_error(self):
        with self.assertRaises(Exception): self.a.get_lto_info()


class LTOHistoryFileTests(unittest.TestCase):

    def setUp(self):
        self.a = LTOHistory('192.168.0.101:8000', '4', '192.168.16.99')
        self.a.download_lto_history_file('admin', 'space')
        self.history_file = open(os.path.abspath('history.json'), 'r')

    def tearDown(self):
        for file in glob.glob(r'{}/*.json'.format(os.getcwd())):
            os.remove(file)

    def test_get_lto_info_finds_json_file(self):
        self.assertTrue(self.history_file)
        self.assertTrue(self.history_file.name.endswith('.json'))

    def test_get_json(self):
        data = self.a.get_json(self.history_file)
        self.assertEqual(type(data), type({}))

    def test_json_to_list(self):
        data = self.a.get_json(self.history_file)
        current = self.a.json_to_list(data)
        self.assertEqual(type(current), type([]))

    def test_json_final(self):
        """
        Test for list of tuples.
        First item in tuple should be tape number
        Second item should be tape size in TB
        """
        data = self.a.get_json(self.history_file)
        current = self.a.json_to_list(data)
        name_sizes = self.a.json_final(current)
        self.assertEqual(type(name_sizes), type([]), 'Expected a list')
        self.assertEqual(type(name_sizes[0]), type(()),'Expected a tuple')
        self.assertIn('IV', name_sizes[0][0],
                      'Barcode should start with \'IV\'')
        self.assertEqual(type(name_sizes[0][1]), float)


class CatDVTests(unittest.TestCase):
            
    @classmethod
    def setUpClass(cls):
        super(CatDVTests, cls).setUpClass()
        cls.a = LTOHistory('192.168.0.101:8080', '4', '192.168.16.99')
        cls.a.catdv_login(cls.a)
        
    def tearDown(self):
        time.sleep(5)
        self.a.delete_session()
        for file in glob.glob(r'{}/*.json'.format(os.getcwd())):
            os.remove(file)
            
    def test_catdv_login(self):
        self.assertGreater(len(self.a.key), 1)
        self.assertEqual(self.a.server, '192.168.0.101:8080')
        self.assertEqual(self.a.api, '4')
        
    def test_client_name_id(self):
        self.clients = self.a.client_name_id(self.a)
        self.assertEqual(type(self.clients), type({}))
        self.assertGreater(len(self.clients.keys()), 1)
    
    def test_catalog_group_names(self):
        self.a.download_lto_history_file('admin', 'space')
        history_file = open(os.path.abspath('history.json'), 'r')
        clients = self.a.client_name_id(self.a)
        cat_grp_names = {i: [0, 0] for i in clients.keys()}
        self.assertEqual(type(cat_grp_names.keys()), type([]))
      
    def test_calculate_written_data(self):
        """Test that a dictionary is created"""
        self.a.download_lto_history_file('admin', 'space')
        self.a.get_catalog_name()
        history_file = open(os.path.abspath('history.json'), 'r')
        clients = self.a.client_name_id(self.a)
        data = self.a.calculate_written_data(history_file,
                                             clients,
                                             self.a.server,
                                             self.a.api,
                                             self.a.key)
        self.assertEqual(type(data), type({}), 'should be a dictionary')
        

if __name__ == '__main__':
    test_classes = [SpaceLTOTests,
                    LTOHistoryFileTests,
                    CatDVTests]
    load = unittest.TestLoader()

    suites_list = []
    for t_class in test_classes:
        suite = load.loadTestsFromTestCase(t_class)
        suites_list.append(suite)

    combined = unittest.TestSuite(suites_list)

    run = unittest.TextTestRunner()
    results = run.run(combined)

