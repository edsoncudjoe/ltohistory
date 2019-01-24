#!/usr/bin/env python

import csv
import datetime
import glob
import json
import logging
import os
import re
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import sys
sys.path.insert(0, '../Py-CatDV')
from pycatdv import Catdvlib

__author__ = "Edson Cudjoe"
__copyright__ = "Copyright 2015, Intervideo"
__credits__ = ["Edson Cudjoe"]
__license__ = "MIT"
__version__ = "1.0.1"
__maintainer__ = "Edson Cudjoe"
__email__ = "edson@intervideo.co.uk"
__status__ = "Development"
__date__ = "4 February 2015"

logging.basicConfig(format='%(process)d-%(levelname)s %(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S',
                    filename='logs/ltohistory.log',
                    filemode='a')


class LTOHistory(Catdvlib):

    def __init__(self, server, api, lto_system_ip):
        super(LTOHistory, self).__init__(server, api)
        self.lto_ip = lto_system_ip
        self.HOME = os.getcwd()

    def __str__(self):
        return super(LTOHistory, self).__str__()

    def byte2tb(self, byte):
        """Converts byte data from the LTO file to terabytes"""
        try:
            f = float(byte)
            tb = ((((f / 1024) / 1024) / 1024) / 1024)
            return tb
        except ValueError:
            print("Value could not be converted to float. {}".format(str(byte)))

    def set_lto_date_range(self):
        """
        Determines the date range as strings to be entered to the Space
        LTO History Manager
        """
        today = datetime.date.today()
        first = today.replace(day=1)
        last_mth = first - datetime.timedelta(days=1)
        beginning = last_mth.replace(day=1)
        end = last_mth.strftime("%Y/%m/%d")
        start = beginning.strftime("%Y/%m/%d")
        return start, end

    def open_chrome_browser(self):
        chrome_profile = webdriver.ChromeOptions()
        pref = {'download.default_directory': self.HOME}
        chrome_profile.add_experimental_option('prefs', pref)
        chrome_driver = '/usr/local/bin/chromedriver'
        try:
            gc = webdriver.Chrome(chrome_driver,
                                      chrome_options=chrome_profile)
            time.sleep(5)
            gc.get("http://{}/login/?p=/lto/catalogue/".format(self.lto_ip))
            return gc
        except Exception as gc_err:
            raise gc_err
        
    def open_firefox_browser(self):
        profile = webdriver.FirefoxProfile()
        profile.set_preference('browser.download.folderList', 2)
        profile.set_preference('browser.download.manager.showWhenStarting', False)
        profile.set_preference('browser.download.dir', os.getcwd())
        profile.set_preference('browser.helperApps.neverAsk.saveToDisk',
                               'application/json,text/javascript,text/json,'
                               'text/x-json')
        try:
            ffx = webdriver.Firefox(firefox_profile=profile)
            time.sleep(5)
            ffx.get("http://{}/login/?p=/lto/catalogue/".format(self.lto_ip))
            return ffx
        except Exception as ffx_err:
            raise ffx_err        

    def open_browser(self):
        try:
            self.browser = self.open_chrome_browser()
        except Exception as e:
            print('ERROR: {}'.format(e))
        return self.browser

    def browser_login(self, usr, pwd):
        """Login to the Space LTO web interface"""
        username = self.browser.find_element_by_name("txt_username")
        password = self.browser.find_element_by_name("txt_password")

        username.send_keys(usr)
        password.send_keys(pwd)

        btn = self.browser.find_element_by_tag_name("button")
        btn.click()
        time.sleep(1)

    def download_lto_history_file(self, username, password):
        """
        Automates getting the tape history file from the Space LTO
        web interface
        """
        try:
            window = self.open_browser()
            self.browser_login(usr=username, pwd=password)

            # Export to file tab
            tabs = window.find_elements_by_class_name("switcher-button")
            tabs[3].click()

            exp_format = window.find_element_by_id("sel_exporthist_format")
            for f in exp_format.find_elements_by_tag_name("option"):
                if f.text == "JSON":
                    f.click()
                    break
            set_from = window.find_element_by_id("txt_exporthist_from")
            set_to = window.find_element_by_id("txt_exporthist_to")

            dates = self.set_lto_date_range()
#            print(dates)
#            raw_input('\ncontinue?:')

            if window.name == 'chrome':
                set_from.clear()
                set_from.send_keys(dates[0])
                time.sleep(5)
                set_to.clear()
#                raw_input('entering date {}'.format(dates[1]))
                time.sleep(2)
                set_to.click()
                # Current bug chromedriver number 5058 on selenium GH issues
                # chromedriver is unable to press '3' key

                set_to.send_keys(dates[1])
#                raw_input('correct?')
            else:
                set_from.send_keys(Keys.COMMAND + "a")
                set_from.send_keys(Keys.DELETE)
                set_from.send_keys(dates[0])
                time.sleep(1)
                set_to.send_keys(Keys.COMMAND + "a")
                set_to.send_keys(Keys.DELETE)
                set_to.send_keys(dates[1])

            time.sleep(1)
            # click on blank area to close calender
            border_click = window.find_element_by_id("browse")
            border_click.click()
            time.sleep(1)
#            dl = raw_input('continue to download')
            # download file
            export = window.find_element_by_id("btn_exporthist_save")
            export.click()
            time.sleep(10)

            window.quit()
        except IndexError:
            raise IndexError

    def get_lto_info(self):
        """Collects LTO information into a list."""
        name_size = None
        get_lto = True
        while get_lto:
            fname = open(os.path.abspath('history.json'), 'r')
            assert fname.name.endswith('.json')
            if '.json' in fname.name:
                jdata = self.get_json(fname)
                current = self.json_to_list(jdata)
                name_size = self.json_final(current)
                get_lto = False
            elif '.csv' in fname.name:
                lto_file = open(fname)
                data = csv.reader(lto_file)
                name_size = lto_to_list(data)
                get_lto = False
            else:
                print('\nNo file submitted.')
                get_lto = False
            if name_size:
                return name_size

    def get_json(self, submitted):
        """
        Reads submitted JSON file and returns a dictionary
        """
        # lto = open(submitted_lto_file, 'r')
        jfile = json.load(submitted)
        return jfile

    def json_to_list(self, json_data_from_file):
        """Reads data from JSON dictionary. Returns data into a list"""
        json_collect = []
        for i in json_data_from_file['tapes']:
            json_collect.append((i['name'], i['used_size']))
        return json_collect

    def json_final(self, current_json_list):
        """
        Converts given filesize into TB. returns list of tuples containing
        IV barcode numbers plus file size.
        """
        final = []
        for c in current_json_list:
            try:
                tb = self.byte2tb(c[1])  # converts GB byte data to TB
                a = re.search(r'(IV\d\d\d\d)', c[0])
                final.append((str(a.group()), round(tb, 2)))
            except AttributeError:
                pass
        return final

    def catdv_login(self, user_instance):
        """Enter CatDV server login details to get access to the API"""
        try:
            user_instance.get_auth()
            user_instance.get_session_key()
            user_instance.get_catalog_name()
            time.sleep(1)
        except Exception as e:
            logging.error('Incorrect login')
            raise e
    
    def client_name_id(self, user):
        """
        Puts client names and id numbers from tuple into a dictionary
        """
        clients = {}
        try:
            for name in user.catalog_names:
                clients[name[0]] = name[1]
            return clients
        except Exception as e:
            print(e)
    
    def calculate_written_data(self, lto_data, names_dict, server, api_vers,
                               key):
        """
        Searches the CatDV API based on the IV barcode number.
        Collects the group name details from the results.
        Calculates how TB has been written based on the amount detailed on
        the Space LTO results.
        """
        try:
            cat_grp_names = {i: [0, 0] for i in names_dict.keys()}
            #print('Querying the CatDV Server. Please wait...')
            
            #create api request for 'IV0XXX' barcode
            for i in lto_data:
                raw_data = requests.get('http://{}/api/{}/clips;'
                                        'jsessionid={}'
                                        '?filter=and((clip.userFields[U7])'
                                        'has({}))&include='
                                        'userFields'.format(server,
                                                            api_vers, key,
                                                            i[0]))
        
                assert raw_data.status_code == 200
                res = json.loads(raw_data.text)
                grp_nm = res['data']['items'][0]['groupName']
                cat_grp_names[grp_nm][0] += 1
                cat_grp_names[grp_nm][1] += i[1]
                time.sleep(1)
        
            for ca in cat_grp_names.items():
                print('{}TB written over {} tapes for {}'.format(ca[1][1], ca[1][0],
                                                                 ca[0]))
        except Exception as e:
            print(e)
            
        return cat_grp_names

    def total_sizes(self, client_dict, name_size):
        """Returns total amount archived for each client/catalog group"""
        assert client_dict
        assert len(name_size) > 0
        print(client_dict)
        print(name_size)
        try:
            for item in client_dict.items():
                barcodes = self.get_barcodes(item[1])
                print('Barcodes: {}'.format(barcodes))
    
                two = set(self.et_client_items(name_size, barcodes))
                print('Two: {}'.format(two))
    
                terabytes = self.get_storage_size(two)
                print('T: {}'.format(terabytes))
    
                print('\n{0}TB written for {1}\n'.format(terabytes, item[0]))
        except Exception as e:
            print(e)

    def get_barcodes(self, catalog_id, user):
        """Gets a list of IV barcodes for user-specified client."""
        user.iv_barcodes = []
        user.get_catalog_clips(catalog_id)
        user.collect_iv_numbers()
        return user.sort_barcodes()

    def get_client_items(self, name_size, clientlist):
        """Separates main list for each client"""
        try:
            client_mnth = []
            for p in sorted(clientlist):
                for i in sorted(name_size):
                    if i[0] in p:
                        client_mnth.append(i)
            print('get_clientitems.client_mnth: {}'.format(client_mnth))
            return client_mnth
        except:
            raise TypeError

    def get_storage_size(self, client_items):
        """Sum of disc size for each tape"""
        count = 0
        for i in client_items:
            count += i[1]
        return count

    def show_catalog_names(self, user):
        try:
            print('\nCurrent catalogs available: ')
            for name in user.catalog_names:
                print(name[0])
        except Exception as e:
            print(e)


def get_catdv_data(textfile):
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
        except Exception:
            print('Unable to add data: {}'.format(item))
            continue
    for c in collect:
        if 'Name' in c[0]:
            final.append(c)
        else:
            if 'test' in c[0]:
                continue
            # 1 file has been labelled incorrectly.
            # It will be temporarily skipped until the tape has been
            # fixed.
            elif 'Intervideo' in c[0]:
                continue
            else:
                gb = byte2tb(c[1])
                a = re.search(r'(IV\d\d\d\d)', c[0])
                final.append((str(a.group()), round(gb, 2)))
    return final

def print_manual(collected):
    for name, size in collected.items():
        print('Archived: {}TB for {}'.format(size, name))


def main():

    print("Getting LTO History file")
    try:
        a = LTOHistory('192.168.0.101:8080', '4', '192.168.16.99')
        a.download_lto_history_file('admin', 'space')
        hist_data = a.get_lto_info()
        print(hist_data)
        
        start = True
        while start:
            auth = raw_input('Login to CatDV Api? [y/n]: ').lower()
            if auth == 'y':
                a.catdv_login(a)
                client_name_and_gid = a.client_name_id(a)
                a.calculate_written_data(hist_data,
                                         client_name_and_gid,
                                         a.server,
                                         a.api,
                                         a.key)
                start = False
            else:
                print('Unable to provide other options')
                break
    except TypeError:
        print('Your CatDV username or password is incorrect')
        logging.exception("Exception:")
    except Exception as e:
        logging.exception("Exception ocurred")
    finally:
        for file in glob.glob(r'{}/*.json'.format(os.getcwd())):
            os.remove(file)
            
        a.delete_session()

if __name__ == '__main__':
    main()
