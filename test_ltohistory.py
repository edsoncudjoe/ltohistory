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
        data = self.a.get_json(self.history_file)
        current = self.a.json_to_list(data)
        name_sizes = self.a.json_final(current)
        self.assertEqual(type(name_sizes), type([]))

@unittest.skip("Repeated and updated elsewhere")
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

class CatDVTests(unittest.TestCase):
    pass


if __name__ == '__main__':
    test_classes = [SpaceLTOTests,
                    LTOHistoryFileTests,
                    TestLtoHistory,
                    CatDVTests]
    load = unittest.TestLoader()

    suites_list = []
    for t_class in test_classes:
        suite = load.loadTestsFromTestCase(t_class)
        suites_list.append(suite)

    combined = unittest.TestSuite(suites_list)

    run = unittest.TextTestRunner()
    results = run.run(combined)

