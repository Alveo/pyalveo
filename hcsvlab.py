import os
import sqlite3
import urllib2
import urllib
import json
import datetime
import uuid
import warnings

import dateutil.parser
import dateutil.tz
import yaml

import pdb

class APIError(Exception):
    """ Raised when an API operation fails for some reason """
    def __init__(self, http_status_code, response, msg):
        self.http_status_code = http_status_code
        self.response = response
        self.msg = msg

        Exception.__init__(self, str(self))    
        
    def __str__(self):
        ret = "HTTP " + str(self.http_status_code) + "\n"
        ret += self.response + "\n"
        return ret + self.msg
                
                
def create_cache_database(path, file_dir):
    """ Create a new SQLite3 database for use with Cache objects
    
    @type path: String
    @param path: path at which to create the database file
    @type file_dir: String
    @param file_dir: directory in which to store large files
    
    @rtype: String
    @returns: the path to the new database file
    
    @raise IOError: if there is a problem creating the database file
    
    
    """
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("""CREATE TABLE items
                 (url text, metadata text, datetime text)""")
    c.execute("""CREATE TABLE documents
                 (url text, path text, datetime text)""")
    c.execute("""CREATE TABLE primary_texts
                 (item_url text, primary_text text, datetime text)""")
    c.execute("""CREATE TABLE meta
                 (key text, value text)""")
    c.execute("INSERT INTO meta VALUES (?, ?)", ("file_dir", file_dir))
    conn.commit()
    conn.close()
    
    
class Cache(object):
    """ Handles caching for HCSvLab API Client objects """
    
    def __init__(self, database, max_age=0):
        """ Create a new Cache object
        
        @type database: String
        @param database: the SQLite3 database to connect to
        @type max_age: int
        @param max_age: cache entries older than this many seconds will be 
        ignored by the has_item, has_document and has_primary_text methods
        
        @rtype: Cache
        @returns: the new Cache
        
        
        """
        self.max_age = max_age
        if not os.path.isfile(database):
            raise ValueError("Database file does not exist")
        self.conn = sqlite3.connect(database)
        self.c = self.conn.cursor()
        self.c.execute("SELECT * FROM meta WHERE key=?", ("file_dir",))
        row = self.c.fetchone()
        if row is None:
            raise ValueError("Database not correctly initialized:"
                             "missing file directory path")
        self.file_dir = row[1]
        
        
    def __del__(self):
        """ Close the database connection """
        self.conn.close()
       

    def __exists_row_not_too_old(self, row):
        """ Check if the given row exists and is not too old """
        if row is None:
            return False
        record_time = dateutil.parser.parse(row[2])
        now = datetime.datetime.now(dateutil.tz.gettz())
        age = (record_time - now).total_seconds() 
        if age > self.max_age:
            return False
            
        return True
        
        
    def __now_iso_8601(self):
        """ Get the current local time as an ISO 8601 string """
        return datetime.datetime.now(dateutil.tz.gettz()).isoformat()
       
       
    def has_item(self, item_url):
        """ Check if the metadata for the given item is present in
        the cache
        
        @type item_url: String
        @param item_url: the URL of the item
        
        @rtype: Boolean
        @returns: True if the item is present, False otherwise
       
        
        """
        self.c.execute("SELECT * FROM items WHERE url=?", (item_url,))
        return self.__exists_row_not_too_old(self.c.fetchone())
        
        
    def has_document(self, doc_url):
        """ Check if the content of the given document is present
        in the cache
        
        @type doc_url: String
        @param doc_url: the URL of the document
        
        @rtype: Boolean
        @returns: True if the data is present, False otherwise
        
        
        """
        self.c.execute("SELECT * FROM documents WHERE url=?", (doc_url,))
        return self.__exists_row_not_too_old(self.c.fetchone())
        
        
    def has_primary_text(self, item_url):
        """ Check if the primary text corresponding to the
        given item is present in the cache
        
        @type item_url: String
        @param item_url: the URL of the item
        
        @rtype: Boolean
        @returns: True if the primary text is present, False otherwise
        
        
        """
        self.c.execute("SELECT * FROM primary_texts WHERE item_url=?",
                      (item_url,))
        return self.__exists_row_not_too_old(self.c.fetchone())

        
    def get_item(self, item_url):
        """ Retrieve the metadata for the given item from the cache.
        
        @type item_url: String
        @param item_url: the URL of the item
        
        @rtype: String
        @returns: the item metadata, as a JSON string
        
        @raise ValueError: if the item is not in the cache
        
        
        """
        self.c.execute("SELECT * FROM items WHERE url=?", (item_url,))
        row = self.c.fetchone()
        if row is None:
            raise ValueError("Item not present in cache")
        return row[1]
        
        
    def get_document(self, doc_url):
        """ Retrieve the content for the given document from the cache.
        
        @type doc_url: String
        @param doc_url: the URL of the document
        
        @rtype: String
        @returns: the document data
        
        @raise ValueError: if the item is not in the cache
        
        
        """
        self.c.execute("SELECT * FROM documents WHERE url=?", (doc_url,))
        row = self.c.fetchone()
        if row is None:
            raise ValueError("Item not present in cache")
        file_path = row[1]
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except IOError as e:
            raise IOError("Error reading file " + file_path + 
                          " to retrieve document " + doc_url + 
                          ": " + e.message)    
        
        
    def get_primary_text(self, item_url):
        """ Retrieve the primary text for the given item from the cache.
        
        @type item_url: String
        @param item_url: the URL of the item
        
        @rtype: String
        @returns: the primary text
        
        @raise ValueError: if the primary text is not in the cache
        
        
        """
        self.c.execute("SELECT * FROM primary_texts WHERE item_url=?", 
                      (item_url,))
        row = self.c.fetchone()
        if row is None:
            raise ValueError("Item not present in cache")
        return row[1]       
        
        
    def add_item(self, item_url, item_metadata):
        """ Add the given item to the cache database, updating
        the existing metadata if the item is already present
        
        @type item_url: String
        @param item_url: the URL of the item
        @type item_metadata: String
        @param item_metadata: the item's metadata, as a JSON string
        
        
        """
        self.c.execute("INSERT INTO items VALUES (?, ?, ?)", 
                  (item_url, item_metadata, self.__now_iso_8601()))
        self.conn.commit()
        
        
    def __generate_filepath(self):
        """ Generate a unique file path within the file_dir directory
        
        @rtype: String
        @returns: a unique file path
        
        
        """
        file_path = os.path.join(self.file_dir, uuid.uuid4())
        if os.path.exists(file_path):
            warnings.warn("something has almost certainly gone wrong")
            return self.__generate_filepath()
        return file_path
            
        
    def add_document(self, doc_url, data):
        """ Add the given document to the cache database, updating
        the existing content data if the document is already present
        
        @type doc_url: String
        @param doc_url: the URL of the document
        @type data: String
        @param data: the document's content data
        
        
        """
        file_path = self.__generate_filepath()
        with open(file_path, 'w') as f:
            f.write(data)
        self.c.execute("INSERT INTO documents VALUES (?, ?, ?)", 
                  (doc_url, file_path, self.__now_iso_8601()))
        self.conn.commit()
        
        
    def add_primary_text(self, item_url, primary_text):
        """ Add the given primary text to the cache database, updating
        the existing record if the primary text is already present
        
        @type item_url: String
        @param item_url: the URL of the corresponding item
        @type primary_text: String
        @param primary_text: the item's primary text
        
        
        """
        self.c.execute("INSERT INTO primary_texts VALUES (?, ?, ?)", 
                  (item_url, primary_text, self.__now_iso_8601()))
        self.conn.commit()
        
        
class Client(object):
    """ Client object used to manipulate HCSvLab objects and interface
    with the API 
   
   
    """
    def __init__(self, api_key, cache, api_url,
                 use_cache=True, update_cache=True, verbose=False):
        """ Construct a new Client

        @type api_key: String
        @param api_key: the API key to use
        @type cache: Cache
        @param cache: the Cache to use
        @type api_url: String
        @param api_url: the base URL for the API server used
        @type use_cache: Boolean
        @param use_cache: True to fetch available data from the 
            cache database, False to always fetch data from the server
        @type update_cache: Boolean
        @param update_cache: True to update the cache database with
            downloaded data, False to never write to the cache
        @type verbose: Boolean
        @param verbose: True to print status messages from the server,
            False for silence

        @rtype: Client
        @returns: the new Client
        """
        self.api_key = api_key
        self.api_url = api_url
        self.cache = cache
        self.use_cache = use_cache
        self.update_cache = update_cache
        self.verbose = verbose

        
    @classmethod
    def with_config_file(self, config_file):
        """ Construct a new Client using the specified configuration file

        @type config_file: String
        @param config_file: path to the configuration file

        @rtype: Client
        @returns: the new Client
        """
        f = open(config_file, 'r')
        c = yaml.safe_load(f.read())
        f.close()
        return Client(c['api_key'], c['cache'], c['api_url'], c['use_cache'],
                      c['update_cache'], c['verbose'])
        
        
    @classmethod
    def default_config(self):
        """ Construct a new Client using the default configuration file 
        
        @rtype: Client
        @returns: the new Client
        
        
        """
        file_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(file_dir, 'config.yaml')
        return Client.with_config_file(file_path)

    
    def __eq__(self, other):
        """ Return true if another Client has all identical fields
        
        @type other: Client
        @param other: the other Client to compare to.
        
        @rtype: Boolean
        @returns: True if the Clients are identical, otherwise False
        
        
        """
        return (self.api_key == other.api_key and
                self.cache == other.cache and
                self.use_cache == other.use_cache and
                self.update_cache == other.update_cache and
                self.verbose == other.verbose)
        
    def __ne__(self, other):
        """ Return true if another Client does not have all identical fields
        
        @type other: Client
        @param other: the other Client to compare to.
        
        @rtype: Boolean
        @returns: False if the Clients are identical, otherwise True
        
        
        """
        return not self.__eq__(other)


    def api_request(self, url, data=None):
        """ Perform an API request to the given URL, optionally 
        including the specified data
        
        @type url: String
        @param url: the URL to which to make the request
        @type data: String
        @param data: the data to send with the request, if any
        
        @rtype: String
        @returns: the response from the server
        
        
        """
        headers = {'X-API-KEY': self.api_key, 'Accept': 'application/json'}
        if data is not None:
            headers['Content-Type'] = 'application/json'
            
        req = urllib2.Request(url, data=data, headers=headers)
        try:
            opener = urllib2.build_opener(urllib2.HTTPHandler())
            response = opener.open(req)
        except urllib2.HTTPError as err:
            raise APIError(err.code, err.reason, "Error accessing API")
            
        return response.read()
        
 
    def get_api_version(self):
        """ Retrieve the API version from the server

        @rtype: String
        @returns: the API version string returned by the server
        
        @raise APIError: when the API request is not successful


        """
        resp = json.loads(self.api_request(self.api_url + '/version'))
        return resp['API version']


    def get_annotation_context(self):
        """ Retrieve the JSON-LD annotation context from the server

        @rtype: Dict
        @returns: the annotation context
        
        @raise APIError: when the API request is not successful


        """
        return json.loads(self.api_request(self.api_url + '/schema/json-ld'))
       


    def get_item_lists(self):
        """ Retrieve metadata about each of the Item Lists associated
        with this Client's API key
        
        Returns a List of Dicts, each containing metadata regarding 
        an Item List, with the following key-value pairs:
            
        name: the name of the Item List
        url: the URL of the Item List
        num_items: the number of items in the Item List
            
        @rtype: List
        @returns: a List of Dicts, each containing metadata regarding
            an Item List
        
        @raise APIError: when the API request is not successful


        """
        return json.loads(self.api_request(self.api_url + '/item_lists.json'))
    
    
    def get_item(self, item_url, force_download=False):
        """ Retrieve the item metadata from the server, as an Item object
        
        @type item_url: String
        @param item_url: URL of the item

        @rtype: Item
        @returns: the corresponding metadata, as an Item object
        @type force_download: Boolean
        @param force_download: True to download from the server
            regardless of the cache's contents
            
        @raise APIError: when the API request is not successful

        
        """
        if (self.use_cache and 
                not force_download and 
                self.cache.has_item(item_url)):
            item_json = self.cache.get_item(item_url)
        else:
            item_json = self.api_request(item_url)
            if self.update_cache:
                self.cache.add_item(item_url, item_json)
                
        return Item(json.loads(item_json), self)
        
        
    def get_document(self, doc_url, force_download=False):
        """ Retrieve the data for the given document from the server
        
        @type doc_url: String
        @param doc_url: the URL of the document
        @type force_download: Boolean
        @param force_download: True to download from the server
            regardless of the cache's contents
            
        @raise APIError: when the API request is not successful
        
        
        """
        if (self.use_cache and 
                not force_download and 
                self.cache.has_document(doc_url)):
            doc_data = self.cache.get_document(doc_url)
        else:
            doc_data = self.api_request(doc_url)
            if self.update_cache:
                self.cache.add_document(doc_url, doc_data)
            
        return doc_data
        
        
    def get_primary_text(self, item_url, force_download=False):
        """ Retrieve the primary text for an item from the server
         
        @type item_url: String
        @param item_url: URL of the item
        @type force_download: Boolean
        @param force_download: True to download from the server
            regardless of the cache's contents
        
        @rtype: String
        @returns: the item's primary text if it has one, otherwise None
        
        @raises APIError: if the request was not successful
        
        
        """
        metadata = self.get_item(item_url).metadata()
        
        try:
            primary_text_url = item['primary_text_url']
        except KeyError:
            return None
            
        if primary_text_url == 'No primary text found':
            return None
        
        if (self.use_cache and 
                not force_download and 
                self.cache.has_primary_text(item_url)):        
            primary_text = self.cache.get_primary_text(item_url)
        else:
            primary_text = self.api_request(primary_text_url)
            if update_cache:
                self.cache.add_primary_text(item_url, primary_text)
        
        return primary_text
        
        
    def get_item_annotations(self, item_url, type=None, label=None):
        """ Retrieve the annotations for an item from the server
        
        @type item_url: String
        @param item_url: URL of the item
        @type type: String
        @param type: return only results with a matching Type field
        @type label: String
        @param label: return only results with a matching Label field
        
        @rtype: String
        @returns: the annotations as a JSON string, if the item has
            annotations, otherwise None
        
        @raises APIError: if the request was not successful
        
        
        """
        md = get_item(item_url).metadata()
        try:
            return self.api_request(md['annotations_url'])
        except KeyError:
            return None
        
        
    def upload_annotation(self, item_url, annotation):
        """ Upload the given annotation to the server
        
        @type item_url: String
        @param item_url: the URL of the item corresponding to the annotation
        @type annotation: String
        @param annotation: the annotation, as a JSON string
        
        @rtype: String
        @returns: the server's success message, if successful
        
        @raises APIError: if the upload was not successful
        
        
        """
        resp = self.api_request(item_url + '/annotations', annotation)
        return self.__check_success(resp)
        
        
    def get_collection_info(self, collection_url):
        """ Retrieve information about the specified Collection from the server
        
        @type collection_url: String
        @param collection_url: the URL of the collection
        
        @rtype: Dict
        @returns: a Dict containing information about the Collection
        
        @raises APIError: if the request was not successful
        
        
        """
        return self.api_request(collection_url)
        
        
    def __check_success(self, resp_json):
        """ Check a JSON server response to see if it was successful
        
        @type resp_json: String
        @param resp_json: the response string
        
        @rtype: String
        @returns: the success message, if it exists
        
        @raises APIError: if the success message is not present
        
        
        """
        resp = json.loads(resp_json)
        if "success" not in resp.keys():
            try:
                raise APIError(resp["error"])
            except KeyError:
                raise APIError(str(resp))
        return resp["success"]
        
    
    def download_items(self, items, file_path, format='zip'):
        """ Retrieve a file from the server containing the metadata
        and documents for the speficied items
            
        @type items: iterable
        @param items: iterable whose iterator produces the URLs of the items
            to download as Strings (for example, a list of the Strings)
        @type file_path: String
        @param file_path: the path to which to save the file
        @type format: String
        @param format: the file format to request from the server: specify
            either 'zip' or 'warc'
            
        @rtype: String
        @returns: the file path
        
        @raise APIError: when the API request is not successful
        
        
        """
        download_url = self.api_url + '/catalog/download_items'
        data = api_request(download_url, json.dumps(items))
        
        with open(file_path, 'w') as f:
            f.write(data)
            
        return file_path
        
        
    def search_metadata(self, query):
        """ Submit a search query to the server and retrieve the results
        
        @type query: String
        @param query: the search query
        
        @rtype: ItemGroup
        @returns: the search results
        
        @raise APIError: when the API request is not successful
        
         
        """
        query_url = (self.api_url + 
                     '/catalog/search?' + 
                     urllib.urlencode((('metadata', query),)))
                     
        resp = json.loads(self.api_request(query_url))
        return ItemGroup(resp['items'], self)
        
        
    def get_item_list(self, item_list_url):
        """ Retrieve an item list from the server as an ItemList object

        @type item_list_url: String
        @param item_list_url: URL of the item list to retrieve

        @rtype: ItemList
        @returns: The ItemList


        """
        resp = json.loads(self.api_request(item_list_url))
        return ItemList(resp['items'], self, item_list_url, resp['name'])


    def get_item_list_by_name(self, item_list_name):
        """ Retrieve an item list from the server as an ItemList object

        @type item_list_name: String
        @param item_list_name: name of the item list to retrieve

        @rtype: ItemList
        @returns: The ItemList

        @raises APIError: if the request was not successful
        
        
        """
        url_name = urllib.urlencode((('name', item_list_name),))
        resp = self.api_request(self.api_url + '/item_lists?' + url_name)
        item_list_url = json.loads(resp)[0]['item_list_url']
        return self.get_item_list(item_list_url)
        
        
    def add_to_item_list(self, item_urls, item_list_url):
        """ Instruct the server to add the given items to the specified
        Item List
            
        @type item_urls: List
        @param item_urls: List of URLs for the items to add
        @type item_list_url: String
        @param item_list_url: the URL of the list to which to add the items
        
        @rtype: String
        @returns: the item list URL
        
        @raises APIError: if the request was not successful
        
        
        """
        
        data = json.dumps(item_urls)
        resp = self.api_request(item_list_url, data)
        self.__check_success(resp)
        return item_list_url
        
        
    def add_to_item_list_by_name(self, item_urls, item_list_name):
        """ Instruct the server to add the given items to the specified
        Item List
            
        @type item_urls: List
        @param item_urls: List of URLs for the items to add
        @type item_list_name: String
        @param item_list_name: name of the item list to retrieve
        
        @rtype: String
        @returns: the item list URL
        
        @raises APIError: if the request was not successful
        
        
        """
        url_name = urllib.urlencode((('name', item_list_name),))
        request_url = self.api_url + '/item_lists?' + url_name
        return self.add_to_item_list(item_urls, request_url)
        
        

class ItemGroup(object):
    """ Represents an ordered group of HCSvLab items""" 

    def __init__(self, item_urls, client):
        """ Construct a new ItemGroup
        
        @type item_urls: List
        @param item_urls: List of URLs of items in this group (as Strings)
        @type client: Client
        @param client: the API client to use for API operations

        @rtype: ItemGroup
        @returns: the new ItemGroup
        """  
        self.item_urls = item_urls
        self.client = client

        
    def set_client(self, new_client):
        """ Set the Client for this ItemGroup
        
        @type new_client: Client
        @param new_client: the new Client
        
        @rtype: Client
        @returns: the new Client
        
        
        """
        self.client = new_client
        return new_client
        
        
    def __eq__(self, other):
        """ Return true if another ItemGroup has all identical fields
        
        @type other: ItemGroup
        @param other: the other ItemGroup to compare to.
        
        @rtype: Boolean
        @returns: True if the ItemGroups are identical, otherwise False
        
        
        """
        return (item_urls == other.item_urls and client == other.client)
        
        
    def __ne__(self, other):
        """ Return true if another ItemGroup does not have all identical fields
        
        @type other: ItemGroup
        @param other: the other ItemGroup to compare to.
        
        @rtype: Boolean
        @returns: False if the ItemGroups are identical, otherwise True
        
        
        """
        return not self.__eq__(other)        

        
    def __contains__(self, item):
        """ Check if the given item is in this ItemGroup

        @param item: either an item URL as a String, or an Item object

        @rtype: Boolean
        @returns: True if the item is present, False otherwise


        """
        return str(item) in self.item_urls
        
        
    def __add__(self, other):
        """ Returns the union of this ItemGroup and another ItemGroup 
        which has an identical Client
        
        @type other: ItemGroup
        @param other: the other ItemGroup
        
        @rtype: ItemGroup
        @returns: A new ItemGroup containing the union of the member items
            of this and the other group
            
        @raise ValueError: if the other ItemGroup does not have the same Client
        
        
        """
        if self.client != other.client:
            raise ValueError("To add ItemGroups, they must have the same Client")
        combined_list = self.item_urls
        combined_list += [url for url in other.item_urls if url not in self.item_urls]
        return ItemGroup(combined_list, self.client)
        
    def __sub__(self, other):
        """ Returns the relative complement of this ItemGroup in another
        ItemGroup which has an identical Client
        
        @type other: ItemGroup
        @param other: the other ItemGroup
        
        @rtype: ItemGroup
        @returns: a new ItemGroup containing all member items of this
            ItemGroup except those also appearing in the other ItemGroup
        
        @raise ValueError: if the other ItemGroup does not have the same Client
        
        
        """
        if self.client != other.client:
            raise ValueError("To subtract ItemGroups, they must have the same Client")
        new_list = [url for url in self.item_urls if url not in other.item_urls]
        return ItemGroup(new_list, self.client)
        

    def intersection(self, other):
        """ Returns the intersection of this ItemGroup with another ItemGroup 
        which has the an identical Client
        
        @type other: ItemGroup
        @param other: the other ItemGroup
        
        @rtype: ItemGroup
        @returns: a new ItemGroup containing all items that appear in both groups
        
        @raise ValueError: if the other ItemGroup does not have the same Client
       
       
        """
        if self.client != other.client:
            raise ValueError("To intersect ItemGroups, they must have the same Client")
        new_list = [url for url in self.item_urls if url in other.item_urls]
        return ItemGroup(new_list, self.client)
        
    def __iter__(self):
        """ Iterate over the item URLs in this ItemGroup """

        return iter(self.item_urls)

        
    def __len__(self):
        """ Return the number of items in this ItemGroup

        @rtype: int
        @returns: the number of items in this ItemGroup


        """
        return len(self.item_urls)


    def get_all(self, force_download=False):
        """ Retrieve the metadata for all items in this list from the server,
        as Item objects

        @rtype: List
        @returns: a List of the corresponding Item objects
        @type force_download: Boolean
        @param force_download: True to download from the server
            regardless of the cache's contents
        
        @raise APIError: when the API request is not successful


        """
        cl = self.client
        return [cl.get_item(item, force_download) for item in self.item_urls]

        
    def item_url(self, item_index):
        """ Return the URL of the specified item

        @type item_index: int
        @param item_index: the index of the item URL

        @rtype: String
        @returns: the URL of the item

        
        """
        return self.item_urls[item_index]


    def __getitem__(self, key):
        """ Return the URL of the specified item

        @type key: int
        @param key: the index of the item URL

        @rtype: String
        @returns: the URL of the item

        
        """
        try:
            return self.item_url(int(key))
        except (IndexError, ValueError) as e:
            raise KeyError(e.message)


    def urls(self):
        """ Return a list of all item URLs for this ItemGroup

        @rtype: List
        @returns: List of item URLs


        """
        return item_urls


    def get_item(self, item_index, force_download=False):
        """ Retrieve the metadata for a specific item in this ItemGroup
        
        @type item_index: int
        @param item_index: the index of the item
        @type force_download: Boolean
        @param force_download: True to download from the server
            regardless of the cache's contents
        
        @rtype: Dict
        @returns: the metadata
        
        @raise APIError: when the API request is not successful
        
        
        """
        return self.client.get_item(self.item_urls[item_index], force_download)

        
    def add_to_item_list_by_name(name):
        """ Add the items in this ItemGroup to the specified Item List on
        the server, creating the item list if it does not already exist

        @type name: String
        @param name: the name of the Item List

        @rtype: String
        @returns: the URL of the Item List
        
        @raise APIError: when the API request is not successful

      
        """
        return self.client.add_to_item_list_by_name(self.item_urls, name)
        
        
    def add_to_item_list(item_list_url):
        """ Add the items in this ItemGroup to the specified Item List on
        the server, creating the item list if it does not already exist

        @type item_list_url: String
        @param item_list_url: the URL of the Item List

        @rtype: String
        @returns: the URL of the Item List
        
        @raise APIError: when the API request is not successful

      
        """ 
        return self.client.add_to_item_list(self.item_urls, item_list_url)
        
        
class ItemList(ItemGroup):
    """ Represents a HCSvLab Item List residing on the server 
    
        Extends ItemGroup with additional Item List-specific functionality
       
       
    """        
    def __init__(self, item_urls, client, url, name):
        """ Construct a new ItemGroup 
        
        @type item_urls: List
        @param item_urls: a List of the item URLs in this Item List
        @type client: Client
        @param client: the API client to use for API operations
        @type url: String
        @param url: the URL of this Item List
        @type name: String
        @param name: the name of this Item List
        
        @rtype: ItemList
        @returns: the new ItemList
        
        
        """
        super(ItemList, self).__init__(item_urls, client) #augh
        self.url = url
        self.name = name
        
    def __str__(self):
        """ Return the URL corresponding to this ItemList
        
        @rtype: String
        @returns: the URL
        

        """
        return url()
        
    
    def name(self):
        """ Return the name of this Item List
        
        @rtype: Strig
        @returns: the name of this Item List
        
        
        """
        return self.name
        
        
    def url(self):
        """ Return the URL corresponding to this ItemList
        
        @rtype: String
        @returns: the URL
        

        """
        return self.url
        

    def refresh(self):
        """ Update this ItemList by re-downloading it from the server
        
        @raise APIError: when the API request is not successful


        """
        refreshed = self.client.get_item_list(self.url)
        self.item_urls = refreshed.urls()
        self.name = refreshed.name()
        
        
    def append(items):
        """ Add some items to this ItemList and save the changes to the server

        @param items: the items to add, either as a List of Item objects, an
            ItemList, a List of item URLs as Strings, a single item URL as a
            String, or a single Item object
        
        @raise APIError: when the API request is not successful
        
        
        """
        self.client.add_to_item_list(items, self.url)
        self.item_urls += items
        
        
    def __eq__(self, other):
        """ Return true if another ItemList has all identical fields
        
        @type other: ItemList
        @param other: the other ItemList to compare to.
        
        @rtype: Boolean
        @returns: True if the ItemLists are identical, otherwise False
        
        
        """
        return (self.url == other.url and
                self.name == other.name and
                super.__eq__(other))
        
        
    def __ne__(self, other):
        """ Return true if another ItemList does not have all identical fields
        
        @type other: ItemList
        @param other: the other ItemList to compare to.
        
        @rtype: Boolean
        @returns: False if the ItemLists are identical, otherwise True
        
        
        """
        return not self.__eq__(other)
        
        
        
class Item(object):
    """ Represents a single HCSvLab item """
    
    def __init__(self, metadata, client):
        """ Create a new Item object
        
        @type metadata: Dict
        @param metadata: the metadata for this Item        
        @type client: Client
        @param client: the API client to use for API operations

        @rtype: Item
        @returns: the new Item
        
        
        """
        self.url = metadata['catalog_url']
        self.metadata = metadata
        self.client = client
        
        
    def metadata(self):
        """ Return the metadata for this Item
        
        @rtype: Dict
        @returns: the metadata for this Item
        
        
        """
        return self.metadata
        
        
    def url(self):
        """ Return the URL for this Item
        
        @rtype: String
        @returns: the URL for this Item
        
        
        """
        return self.url
        
        
    def get_documents(self):
        """ Return the metadata for each of the documents corresponding
        to this Item, each as a Document object
            
        @rtype: List
        @returns: a list of Document object corresponding to this
            Item's documents    
        """
        return[Document(doc, self.client) for doc in self.metadata['Documents']]
        
        
    def get_document(self, index=0):
        """ Return the metadata for the specified document, as a
        Document object
        
        @type index: int
        @param index: the index of the document
            
        @rtype: Document
        @returns: the metadata for the specified document
        
        
        """
        return Document(self.metadata['Documents'][index], self.client)
        
        
    def get_primary_text(self, force_download=False):
        """ Retrieve the primary text for this item from the server
        
        @type force_download: Boolean
        @param force_download: True to download from the server
            regardless of the cache's contents
        
        @rtype: String
        @returns: the primary text
        
        
        """
        return self.client.get_primary_text(self.url, force_download)
        
        
    def get_annotations(self, type=None, label=None):
        """ Retrieve the annotations for this item from the server
        
        @type type: String
        @param type: return only results with a matching Type field
        @type label: String
        @param label: return only results with a matching Label field
        
        @rtype: String
        @returns: the annotations as a JSON string
        
    
        """   
        return self.client.get_item_annotations(self.url, type, label)
        
            
    def upload_annotation(self, annotation):
        """ Upload the given annotation to the server

        @type annotation: String
        @param annotation: the annotation, as a JSON string
        
        @rtype: String
        @returns: the server response
        
        
        """
        return self.client.upload_annotation(self.url, annotation)
        
        
    def __str__(self):
        """ Return the URL of this Item
        
        @rtype: String
        @returns: the URL of this Item
        
        
        """
        return self.url()
        
        
    def __eq__(self, other):
        """ Return true if and only if this Item is identical to another
        
        @type other: Item
        @param other: the other Item
        
        @rtype: Boolean
        @returns: True if both Items have all identical fields, otherwise False
        
        
        """
        return (self.url == other.url and 
                self.metadata == other.metadata and
                self.client == other.client)
        
        
    def __ne__(self, other):
        """ Return true if and only if this Item is not identical to another
        
        @type other: Item
        @param other: the other Item
        
        @rtype: Boolean
        @returns: False if both Items have all identical fields, otherwise True
        
        
        """   
        return not self.__eq__(other)

    
    def add_to_item_list(self, item_list_url):
        """ Add this item to the specified Item List on the server
        
        @type item_list_url: String
        @param item_list_url: the URL of the Item list
        
        @rtype: String
        @returns: the URL of the Item List
        
        
        """
        return self.client.add_to_item_list([self.url], item_list_url)
        
        
    def add_to_item_list_by_name(self, name):
        """ Add this item to the specified Item List on the server
        
        @type name: String
        @param name: the name of the Item list
        
        @rtype: String
        @returns: the URL of the Item List
        
        
        """
        return self.client.add_to_item_list_by_name([self.url], name)    
        
        
class Document(object):
    """ Represents a single HCSvLab document """
    
    def __init__(self, metadata, client):
        """ Create a new Document
        
        @type metadata: Dict
        @param metadata: the metadata for this Document
        @type client: Client
        @param client: the API client to use for API operations
        
        @rtype: Document
        @returns: the new Document
        
        
        """
        self.url = metadata['catalog_url']
        self.metadata = metadata
        self.client = client
        
        
    def metadata(self):
        """ Return the metadata for this Document
        
        @rtype: Dict
        @returns: the metadata for this Document
        
        
        """
        return self.metadata
        
        
    def url(self):
        """ Return the URL for this Document
        
        @rtype: String
        @returns: the URL for this Document
        
        
        """
        return self.url
        
        
    def __str__(self):
        """ Return the URL of this Document
        
        @rtype: String
        @returns: the URL of this Document
        
        
        """
        return self.url()
        
        
    def __eq__(self, other):
        """ Return true if and only if this Document is identical to another
        
        @type other: Document
        @param other: the other Document
        
        @rtype: Boolean
        @returns: True if both Documents have all identical fields, otherwise False
        
        
        """
        return (self.url == other.url and
                self.metadata == other.metadata and
                self.client == other.client)
        
        
    def __ne__(self, other):
        """ Return true if and only if this Document is not identical to another
        
        @type other: Document
        @param other: the other Document
        
        @rtype: Boolean
        @returns: False if both Documents have all identical fields, otherwise True
        
        
        """
        return not self.__eq__(other)
        
        
    def get_content(self, force_download=False):
        """ Retrieve the content for this Document from the server
        
        @type force_download: Boolean
        @param force_download: True to download from the server
            regardless of the cache's contents
        
        @rtype: String
        @returns: the content data
        
        
        """
        return self.client.get_document(self.url, force_download)
        
        
    def download_content(self, path, force_download=False):
        """ Download the content for this document to a file
        
        @type path: String
        @param path: the path to which to write the data
        @type force_download: Boolean
        @param force_download: True to download from the server
            regardless of the cache's contents
        
        @rtype: String
        @returns: the path to the downloaded file
        
        
        """
        data = self.client.get_document(self.url, force_download)
        with open(path, 'w') as f:
            f.write(data)
        return path