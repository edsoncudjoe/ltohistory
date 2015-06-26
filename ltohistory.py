#!/usr/bin/env python

__author__ = "Edson Cudjoe"
__version__ = "1.0.0"
__email__ = "edson@intervideo.co.uk"
__status__ = "Development"
__date__ = "4 February 2015"


import csv
import json
import re
import sys
import time
import tkFileDialog
from Tkinter import *
sys.path.insert(0, '../Py-CatDV') 
from pycatdv import Catdvlib

def byte2TB(byte):
	"""
	Converts byte data from the LTO file to terabytes
	"""
	try:	
		f = float(byte)
		tb = ((((f / 1024) / 1024) / 1024) / 1024)
		return tb
	except ValueError:
		print("Value could not be converted to float. {}".format(str(byte)))

def get_CatDV_data(textfile):
	"""
	Opens text file from CatDV output containing Intervideo barcodes.
	these barcodes are added to a list.
	"""
	catdv_list = []
	with open(textfile) as client_barcodes:
		reader = csv.reader(client_barcodes)
		for row in reader:
			try:
				catdv_list.append(row[0])
			except:
				pass
	return catdv_list

def make_csv_file(final):
	"""
	Creates a CSV file to be used with spreadsheets from the intervideo
	LTO tape barcode and size data.
	"""
	fname = raw_input('Enter name of csv file to save into: ')
	name_ext = fname + ".csv"
	with open(name_ext, 'wb') as csvfile:
		writedata = csv.writer(csvfile, delimiter=',')
		for i in range(len(final)):
			writedata.writerow(final[i])
	print('File has been created.')
    
def lto_to_list(data):
	"""
	Takes the output of CSV reader as input. Converts this data into a
	list to be compared with the individual client barcode lists 
	generated from CatDV data.
	"""
	collect = []
	final = []
	for item in data:
		try:
			collect.append((item[0], item[6])) 
		except:
			print('Unable to add data: {}'.format(item))
			continue
	for c in collect:
		if 'Name' in c[0]:
			final.append(c)
		else:
			if 'test' in c[0]:
				continue
			#1 file has been labelled incorrectly.
			# It will be temporarily skipped until the tape has been
			#fixed.
			elif 'Intervideo' in c[0]:
				continue
			else:
				gb = byte2TB(c[1])
				a = re.search(r'(IV\d\d\d\d)', c[0])
				final.append((str(a.group()), round(gb, 2))) 
	return final

# retrieve data from GBlabs JSON output
def get_json(submitted):
	lto = open(submitted, 'r')
	jfile = json.load(lto)
	return jfile

def json_to_list(json):
	json_collect = []
	for i in json['tapes']:
		json_collect.append((i['name'], i['used_size']))
	return json_collect 

def json_final(current):
	final = []
	for c in current:
		try:
			tb = byte2TB(c[1]) # converts GB byte data to TB
			a = re.search(r'(IV\d\d\d\d)', c[0]) #removes unicode
			final.append((str(a.group()), round(tb, 2))) 
		except AttributeError:
			pass
	return final

def get_client_items(name_size, clientlist):
	"""Separates main list for each client"""
	try:
		client_mnth = []
		for p in sorted(clientlist):
			for i in sorted(name_size):
				if i[0] in p:
					client_mnth.append(i)
		return client_mnth
	except:
		raise TypeError

def get_storage_size(client_items):
	"""Sum of disc size for each tape"""
	count = 0
	for i in client_items:
		count += i[1]
	return count

def catdv_login(user):
	"""Enter CatDV server login details to get access to the API"""
	try:
		user.get_auth()
		print('\nGetting catalog data...\n')
		user.get_session_key()
		user.get_catalog_name()
		time.sleep(1)
		print('Catalog names and ID\'s have been loaded')
	except:
		raise AttributeError

def show_catalog_names(user):
	try:
		print('\nCurrent catalogs available: ')
		for name in user.catalog_names:
			print name[0]
	except Exception, e:
		print(e)

def get_barcodes(group_id):
	"""Gets a list of IV barcodes for user-specified client."""
	user.iv_barcodes = []
	user.get_catalog_clips(group_id)
	user.collect_iv_numbers()
	return user.sort_barcodes()

def client_name_id(user):
	"""Puts client names and id numbers into a dictionary"""
	print('\nBuilding client list.')
	clients = {}
	try:
		for name in user.catalog_names:
			clients[name[0]] = name[1]
		return clients
	except Exception, e:
		print(e)

def total_sizes(client_dict, name_size):
	"""Returns total amount archived for each client/catalog group"""
	try:
		for item in client_dict.items():
			api = get_barcodes(item[1])
			two = set(get_client_items(name_size, api))
			terabytes = get_storage_size(two)
			
			print('\n{0}TB written for {1}\n'.format(terabytes, item[0]))
	except:
		raise TypeError

def get_lto_info():
	"""Collects LTO information into a list. User chooses LTO file."""
	name_size = None
	get_lto = True
	while get_lto:
		fname = tkFileDialog.askopenfilename(title='Open LTO file', 
			**LTOFILETYPES)		
		if fname:
			print('File loaded.\n')
		if '.json' in fname: 
			jdata = get_json(fname)
			current = json_to_list(jdata)
			name_size = json_final(current)
			get_lto = False
		elif '.csv' in fname:
			lto_file = open(fname)
			data = csv.reader(lto_file)
			name_size = lto_to_list(data)
			get_lto = False
		else:
			print('\nNo file submitted.')
			get_lto = False
		if name_size:
			return name_size

def get_catdv_textfiles(name_size):
	"""Opens CatDV text files to collect barcode information"""
	manual_collect = {}
	while True:
		client_name = raw_input('Client name: ')
		client_file = tkFileDialog.askopenfilename(title='Open CatDV text file')
		if client_file:
			barcode_list = set(get_CatDV_data(client_file))
			items = set(get_client_items(name_size, barcode_list))
			size = get_storage_size(items)
			manual_collect[client_name] = size
		new = raw_input('Add another client?: ').lower()
		if new == 'n':
			break
	return manual_collect

def print_manual(collected):
	for name, size in collected.items():
		print('Archived: {}TB for {}'.format(size, name))

LTOFILETYPES = options = {}
options['filetypes'] = [
	('all files', '.*'), ('json files', '.json'), ('csv files', '.csv')]
root = Tk()
root.withdraw()

user = Catdvlib()
def main():
	try:
		lt_info = get_lto_info()

		start = True
		while start:
			auth = raw_input('Login to CatDV Api? [y/n]: ').lower()
			if auth == 'y':
				catdv_login(user)

				names_and_groupid = client_name_id(user)
				total_sizes(names_and_groupid, lt_info)

				start = False
			
			elif auth == 'n':	
				print('You have chosen not to access CatDV.')
				manual = raw_input('\nDo you wish to locate the files '
					'manually? [Y/n]: ').lower()
				if manual == 'y':
					text = get_catdv_textfiles(lt_info)
					print_manual(text)
					start = False
				else:
					break
			else:
				print('Not a recognised input. Please try again.')

		create_csv = raw_input(
			'Do you wish to write the months archived tape barcodes' 
			'+ sizes to a csv file? [y/n]: ')
		if create_csv == 'y':
			make_csv_file(name_size)
		else:
			print('You have chosen not to write to a csv file.')
	except NameError, e: # Name_size var has not been created. check CatDV 
		print(e, 'Check CatDV data inputs: API login and/or filenames.')
	except AttributeError:
		print('\nUnable to access the CatDV API. Please try again later.')
	except TypeError:
		print('Unable to perform this process due to a missing file.')
	finally:
		user.delete_session()
		try:
			if lto_file:
				lto_file.close()
		except NameError:
			print('Closing application')
		print('Goodbye!')

if __name__ == '__main__':
	main()
