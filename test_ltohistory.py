import json
import ltohistory as lh
import unittest
import sys
from selenium import webdriver
sys.path.insert(0, '../Py-CatDV')
from pycatdv import Catdvlib


class TestSpaceLTOInterface(unittest.TestCase):
    """Test automation of space LTO web interface"""

    def setUp(self):
        self.browser = webdriver.Firefox()
        self.browser.get("http://192.168.0.190/login/?p=/lto/catalogue/")

    def tearDown(self):
        self.browser.quit()

    def test_open_browser(self):
        """Test for correct URL"""
        firefox = self.browser
        self.assertIsInstance(firefox,
                              webdriver.firefox.webdriver.WebDriver)
        self.assertEqual('LTO Space Login', firefox.title.encode('utf-8'))

    def test_set_search_periods(self):
        today = lh.set_search_dates()
        self.assertEqual(type(today), type(()))

    def test_download_lto_file(self):
        lh.download_lto_file(username='admin', password='space')
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

