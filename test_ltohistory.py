import ltohistory as lh
from pycatdv import Catdvlib
import unittest
import Tkinter as tk


class TestLtoHistory(unittest.TestCase):
	"""Tests for collecting correct data"""
	@classmethod
	def setUpClass(cls):
		cls._user = Catdvlib()
		lh.catdv_login(cls._user)
		cls.root = tk.Tk()

	@classmethod
	def tearDownClass(cls):
		cls._user.delete_session()
		cls.root.withdraw()
		print("logged out")

	def test_catdv_login(self):
		"""Test whether login returns a succesful status code"""		
		self.assertEqual(self._user.status, 200)

	def test_get_lto_info(self):
		"""Test data loaded from lto file loads correctly"""
		self.lto_data = lh.get_lto_info()
		self.assertGreater(len(self.lto_data), 1)

	def test_client_name_id(self):
		"""
		Test length of created dictionary to find out if it has 
		been populated.
		"""
		self.name_id = lh.client_name_id(self._user)
		self.assertGreater(len(self.name_id), 2)

if __name__ == '__main__':
	unittest.main()