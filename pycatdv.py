import requests
import json
import getpass
from settings import url

API_VERS = '4'


class Catdvlib(object):
    """
    A python wrapper for the CatDV Server REST API service

    """

    def __init__(self, server_url, api_vers):

        self.server = server_url
        self.api = str(api_vers)
        self.url = url
        self.iv_barcodes = []
        self.key = None
        self.username = None
        self.password = None

    def build_url_route(self):
        """build full login url to get session key

            The url consists of:

                1. protocol (http(s)://)
                2. server ip address
                3. port number
                4. api version number
                5. username
                6. password
        """
        def build_api_url(self, svr_address, api, username, password,
                          port=':8080'):
            if svr_address.startswith('http://'):
                self.url = svr_address + '/api/' + str(api) + '/' + \
                       'session?usr=' + username + '&pwd=' + password
                return self.url
            else:
                self.url = 'http://' + svr_address + '/api/' + \
                           str(api) + '/' + 'session?usr=' + username + \
                           '&pwd=' + password
                return self.url
        return build_api_url

    @build_url_route
    def login_url(self, svr_address, api,  username, password):
        return url

    def login(self):
        self.username = raw_input('Enter username: ')
        self.password = getpass.getpass('Enter password: ')
        pass

    # Generic methods
    def set_url(self):
        """
        Stores the location of the CatDV server.
        The user only needs to enter the server domain eg: 'google.com'
        """
        url_input = raw_input(
            'Enter address of the CatDV Sever (eg. \'localhost:8080\'): ')
        self.url = 'http://' + url_input
        return self.url

    def set_auth(self, username, password):
        """Api request with given login info"""
        self.auth = self.login_url(self.server, self.api, username, password)
        return self.auth

    def get_auth(self):
        """Enables the user to login to their CatDV database."""
        print('\nEnter login details for CatDV: ')
        usr = raw_input('Enter username: ')
        pwd = getpass.getpass('Enter password: ')
        self.set_auth(usr, pwd)
        return

    def get_rsa(self):
        full_key = self.url + '/session/key'
        try:
            full_rsa = requests.get(full_key)
            rsa_data = json.loads(full_rsa.text)
        except:
            raise Exception
        return rsa_data

    def get_session_key(self):
        """
        Extracts the session key from login to be used for future API calls.
        """

        connect_timeout = 60.0
        try:
            response = requests.get(self.auth,
                timeout=connect_timeout)
            self.status = response.status_code
            keydata = json.loads(response.text)
            self.key = keydata['data']['jsessionid']
            return self.key
        except requests.exceptions.ConnectTimeout as e:
            print "The server connection timed-out."
            raise e
        except requests.exceptions.ConnectionError as e:
            print('\nCan\'t access the API. Please check you have the right '
                  'domain address')
            raise e
        except Exception, e:
            print(e)

    def get_catalog_name(self):
        """Call to get information on all available catalogs."""
        catalogs = requests.get('http://' + self.server + "/api/" + API_VERS +
                                "/catalogs;jsessionid=" + str(self.key))
        catalog_data = json.loads(catalogs.text)
        self.catalog_names = []
        for i in catalog_data['data']:
            if i['ID'] > 1:
                self.catalog_names.append((i['groupName'], i['ID']))
        return self.catalog_names

    def get_catalog_clips(self, catalog_id):
        """
        Requests all clips from a client catalog. Filtered by catalog ID.
        """
        content_raw = requests.get(
            'http://' + self.server + "/api/" + API_VERS + \
            '/clips;jsessionid=' + self.key + \
            '?filter=and((catalog.id)eq({}))&include=userFields'.format(
                catalog_id))
        self.content_data = json.loads(content_raw.text)
        return self.content_data

    def clip_search(self):
        """Returns all clips that match the given search term"""
        entry = raw_input('Enter clip title: ')
        result = requests.get(
            'http://' + self.server + '/api/' + self.api + \
            '/clips;jsessionid=' + self.key + \
            '?filter=and((clip.name)has({}))&include=userFields'.format(entry))
        jdata = json.loads(result.text)
        return jdata['data']['items']

    def clip_gui_search(self, entry):
        """Returns all clips that match the given search term"""
        result = requests.get(
            'http://' + self.server + '/api/' + self.api + \
            '/clips;jsessionid=' + self.key + \
            '?filter=and((clip.name)has({}))&include=userFields'.format(entry))
        jdata = json.loads(result.text)
        return jdata

    def clip_id_search(self):
        """
        Retrieves all data for a clip specified by the unique ID.
        Returns JSON data.
        """
        clip_id = raw_input('Enter Clip ID \'eg: 480CADB5\': ')
        clip = requests.get(
            'http://' + self.server + '/api/' + API_VERS + '/clips;jsessionid=' + self.key + \
            '?filter=and((clip.clipref)has({}))'.format(clip_id))
        clip_info = json.loads(clip.text)
        return clip_info['data']['items']

    def delete_session(self):
        """HTTP delete call to the API"""
        return requests.delete(self.url + '/api/4/session')

    #Intervideo Specific
    def iv_clip_search(self):
        """Returns all clips that match the given search term"""
        entry = raw_input('Enter clip title: ')
        result = requests.get(
                'http://192.168.0.101:8080/api/' + API_VERS + '/clips;jsessionid=' + self.key
            + '?filter=and((clip.name)'
                'has({}))&include=userFields'.format(entry))
        jdata = json.loads(result.text)
        for i in jdata['data']['items']:
            if i['userFields']['U7']:
                print i['userFields']['U7'], i['name'], i['ID']
            else:
                print i['name'], i['ID']

    def get_iv_numbers(self, data):
        """Generator to identify Intervideo barcode numbers"""
        count = 0
        try:
            for i in data['data']['items']:
                if 'userFields' in i.keys():
                    if 'U7' in i['userFields']:
                        count += 1
                        yield i['userFields']['U7']
        except:
            print('Possible Error at position {}'.format(count))

    def collect_iv_numbers(self):
        """Collects Intervideo barcodes into a list."""
        try:
            iv_gen = self.get_iv_numbers(self.content_data)
            count = 0
            for i in range(len(self.content_data['data']['items'])):
                self.iv_barcodes.append(next(iv_gen))
                count += 1
        except StopIteration:
            print('Collected {} barcode numbers'.format(count))

    def sort_barcodes(self):
        """Sorts Intervideo barcode numbers and removes duplicates."""
        return sorted(set(self.iv_barcodes))

    
    def size_fmt(self, num, suffix='B'):
        for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)


    def get_filesize(self, catalog_id=15653):
        clips_url = \
        'http://192.168.0.101:8080/api/4/clips;jsessionid={}?filter' \
            '=and((catalog.id)eq({}))'.format(self.key, catalog_id)
        r_data = requests.get(clips_url)
        j_data = json.loads(r_data.text)
        for item in j_data['data']['items']:
            yield item['media']['fileSize']

    def stored_filesizes(self):
        gen = self.get_filesize()
        return list(gen)
   

if __name__ == '__main__':

    user = Catdvlib(server_url='http://192.168.0.101:8080', api_vers=4)
    try:
        user.get_auth()
        user.get_session_key()
        #user.clip_search()
    except Exception, e:
        print(e)
    finally:
        user.delete_session()

