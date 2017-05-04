#!/usr/bin/env python

# __author__ = "Edson Cudjoe"
# __version__ = "1.0.0"
# __email__ = "edson@intervideo.co.uk"
# __status__ = "Development"
# __date__ = "4 February 2015"

import csv
import datetime
import glob
import json
import os
import re
import requests
import time
import tkFileDialog
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import sys
sys.path.insert(0, '../Py-CatDV')
from pycatdv import Catdvlib

HOME = os.getcwd()
c = Catdvlib('192.168.0.101:8080', '4')


def set_search_dates():
    """
    Determines the start and end dates as strings to be entered to the Space
    LTO History Manager
    """
    today = datetime.date.today()
    first = today.replace(day=1)
    last_mth = first - datetime.timedelta(days=1)
    beginning = last_mth.replace(day=1)
    end = last_mth.strftime("%Y/%m/%d")
    start = beginning.strftime("%Y/%m/%d")
    print('Start: {}. End: {}'.format(start, end))
    return start, end


def open_chrome_browser():
    ch_profile = webdriver.ChromeOptions()
    pref = {'download.default_directory': HOME}
    ch_profile.add_experimental_option('prefs', pref)
    chrome_driver = '/Applications/Google ' \
                    'Chrome.app/Contents/MacOS/chromedriver'
    try:
        gc = webdriver.Chrome(chrome_driver,
                                  chrome_options=ch_profile)
        time.sleep(5)
        gc.get("http://192.168.0.190/login/?p=/lto/catalogue/")
        assert 'LTO Space Login' == gc.title.encode('utf-8')
        return gc
    except Exception as gc_err:
        raise gc_err


def open_firefox_browser():
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
        ffx.get("http://192.168.0.190/login/?p=/lto/catalogue/")
        assert 'LTO Space Login' == ffx.title.encode('utf-8')
        return ffx
    except Exception as ffx_err:
        raise ffx_err


def open_browser():
    try:
        browser = open_chrome_browser()
    except Exception as e:
        print('ERROR: {}'.format(e))
    return browser


def browser_login(browser, usr, pwd):
    usrn = browser.find_element_by_name("txt_username")
    pswd = browser.find_element_by_name("txt_password")

    usrn.send_keys(usr)
    pswd.send_keys(pwd)

    btn = browser.find_element_by_tag_name("button")
    btn.click()
    time.sleep(1)


def download_lto_file(username, password):
    try:
        firefox = open_browser()
        browser_login(firefox, usr=username, pwd=password)
        tabs = firefox.find_elements_by_class_name("switcher-button")
        tabs[3].click()

        exp_format = firefox.find_element_by_id("sel_exporthist_format")
        for f in exp_format.find_elements_by_tag_name("option"):
            if f.text == "JSON":
                f.click()
                break

        set_from = firefox.find_element_by_id("txt_exporthist_from")
        set_to = firefox.find_element_by_id("txt_exporthist_to")

        dates = set_search_dates()

        if firefox.name == 'chrome':
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
        border_click = firefox.find_element_by_id("browse") 
        border_click.click()
        time.sleep(1)

        # download file
        export = firefox.find_element_by_id("btn_exporthist_save")
        export.click()
        time.sleep(10)

        firefox.quit()
    except IndexError:
        raise IndexError


def byte2tb(byte):
    """Converts byte data from the LTO file to terabytes"""
    try:
        f = float(byte)
        tb = ((((f / 1024) / 1024) / 1024) / 1024)
        return tb
    except ValueError:
        print("Value could not be converted to float. {}".format(str(byte)))


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


# retrieve data from GBlabs JSON output
def get_json(submitted):
    """
    Reads submitted JSON file and returns the JSON dictionary
    """
    # lto = open(submitted_lto_file, 'r')
    jfile = json.load(submitted)
    return jfile


def json_to_list(json_data_from_file):
    """Reads data from JSON dictionary. Returns data into a list"""
    json_collect = []
    for i in json_data_from_file['tapes']:
        json_collect.append((i['name'], i['used_size']))
    return json_collect


def json_final(current_json_list):
    """
    Converts given filesize into TB. returns list of tuples containing
    IV barcode numbers plus file size.
    """
    final = []
    for c in current_json_list:
        try:
            tb = byte2tb(c[1])  # converts GB byte data to TB
            a = re.search(r'(IV\d\d\d\d)', c[0])
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
        print('get_clientitems.client_mnth: {}'.format(client_mnth))
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
        assert user.key
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


def get_barcodes(catalog_id):
    """Gets a list of IV barcodes for user-specified client."""
    c.iv_barcodes = []
    c.get_catalog_clips(catalog_id)
    c.collect_iv_numbers()
    return c.sort_barcodes()


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
    assert client_dict
    assert len(name_size) > 0
    print(client_dict)
    print(name_size)
    try:
        for item in client_dict.items():
            barcodes = get_barcodes(item[1])
            print('Barcodes: {}'.format(barcodes))

            two = set(get_client_items(name_size, barcodes))
            print('Two: {}'.format(two))

            terabytes = get_storage_size(two)
            print('T: {}'.format(terabytes))

            print('\n{0}TB written for {1}\n'.format(terabytes, item[0]))
    except Exception, e:
        print e


def get_lto_info():
    """Collects LTO information into a list."""
    name_size = None
    get_lto = True
    while get_lto:
        fname = open('history.json', 'r')
        assert fname.name.endswith('.json')
        if '.json' in fname.name:
            jdata = get_json(fname)
            current = json_to_list(jdata)
            name_size = json_final(current)
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


def get_catdv_textfiles(name_size):
    """Opens CatDV text files to collect barcode information"""
    manual_collect = {}
    while True:
        client_name = raw_input('Client name: ')
        client_file = tkFileDialog.askopenfilename(
            title='Open CatDV text file')
        if client_file:
            barcode_list = set(get_catdv_data(client_file))
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


def calculate_written_data(lto_data, names_dict, server, api_vers, key):
    """
    Searches the CatDV API based on the IV barcode number.
    Collects the group name details from the results.
    Calculates how TB has been written based on the amount detailed on
    the Space LTO results.
    """

    cat_grp_names = {i: [0, 0] for i in names_dict.keys()}
    print('Querying the CatDV Server. Please wait...')

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
    return cat_grp_names




LTOFILETYPES = options = {}
options['filetypes'] = [
    ('all files', '.*'), ('json files', '.json'), ('csv files', '.csv')]


def main():


    print("Select LTO output file")
    try:
        download_lto_file(username='admin', password='space')

        lt_info = get_lto_info()
        print(lt_info)
        start = True
        while start:
            auth = raw_input('Login to CatDV Api? [y/n]: ').lower()
            if auth == 'y':
                catdv_login(c)

                names_and_groupid = client_name_id(c)

                calculate_written_data(lt_info, names_and_groupid,
                                       server=c.server,
                                       api_vers=c.api,
                                       key=c.key)

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

        delete_lto_file = raw_input('Do you wish to delete the downloaded '
                                    'LTO history file(s)? [y/n]: ').lower()
        if delete_lto_file == 'y':
            for file in glob.glob(r'*.json'):
                print('Deleted: {}'.format(file))
                os.remove(file)
        else:
            print('File will be saved in {}'.format(os.getcwd()))
    except NameError, e:  # Name_size var has not been created. check CatDV
        print(e, 'Check CatDV data inputs: API login and/or filenames.')
    except AttributeError:
        print('\nUnable to access the CatDV API. Please try again later.')
    except TypeError:
        print('Unable to perform this process due to a missing file.')
    except IndexError:
        print("Incorrect LTO login details")
    finally:
        c.delete_session()
        try:
            if lto_file:
                lto_file.close()
        except NameError:
            print('Closing application')
        print('Goodbye!')


if __name__ == '__main__':
    main()
