import os
import sqlite3

class APIError:
    """ Raised when an API operation fails for some reason """
    def __init__(self, http_status_code, response, msg):
        self.http_status_code = http_status_code
        self.response = response
        self.msg = msg
        
    def __str__(self):
        ret = "HTTP " + str(http_status_code) + "\n"
        return ret + msg
                
                
def create_cache_database(path):
    """ Create a new SQLite3 database for use with Cache objects
    
    @type path: String
    @param path: path at which to create the database file
    
    @rtype: String
    @returns: the path to the new database file
    
    @raise IOError: if there is a problem creating the database file
    
    
    """
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("""CREATE TABLE items
                 (url text, metadata text)""")
    c.execute("""CREATE TABLE documents
                 (url text, data text)""")
    conn.commit()
    conn.close()
    
    
class Cache:
    """ Handles caching for HCSvLab API Client objects """
    
    def __init__(self, database):
        """ Create a new Cache object
        
        @type database: String
        @param database: the SQLite3 database to connect to
        
        @rtype: Cache
        @returns: the new Cache
        
        
        """
        pass
       
       
    def has_item(self, item_url):
        """ Check if the metadata for the given item is present in
        the cache
        
        @type item_url: String
        @param item_url: the URL of the item
        
        @rtype: Boolean
        @returns: True if the item is present, False otherwise
        
        @raise IOError: if there is a problem accessing the database
        
        
        """
        pass
        
        
    def has_document(self, document_url):
        """ Check if the content of the given document is present
        in the cache
        
        @type document_url: String
        @param document_url: the URL of the document
        
        @rtype: Boolean
        @returns: True if the data is present, False otherwise
        
        @raise IOError: if there is a problem accessing the database
        
        
        """
        pass       
        
    
    def get_item(self, item_url):
        """ Retrieve the metadata for the given item from the cache.
        
        @type item_url: String
        @param item_url: the URL of the item
        
        @rtype: String
        @returns: the item metadata, as a JSON string
        
        @raise IOError: if there is a problem accessing the database
        @raise ValueError: if the item is not in the cache
        
        
        """
        
        
    def get_document(self, item_url):
        """ Retrieve the content for the given document from the cache.
        
        @type item_url: String
        @param item_url: the URL of the document
        
        @rtype: String
        @returns: the document data
        
        @raise IOError: if there is a problem accessing the database
        @raise ValueError: if the item is not in the cache
        
        
        """

class Client:
    """ Client object used to manipulate HCSvLab objects and interface
    with the API 

    
    """
    def __init__(self, api_key, cache, use_cache=True, 
                 update_cache=True, verbose=False):
        """ Construct a new Client

        @type api_key: String
        @param api_key: the API key to use
        @type cache_db: Cache
        @param cache_db: the Cache to use
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
        pass


    def __init__(self, config_file):
        """ Construct a new Client using the specified configuration file

        @type config_file: String
        @param config_file: path to the configuration file

        @rtype: Client
        @returns: the new Client
        """
        pass
        
        
    def __eq__(self, other):
        """ Return true if another Client has all identical fields
        
        @type other: Client
        @param other: the other Client to compare to.
        
        @rtype: Boolean
        @returns: True if the Clients are identical, otherwise False
        
        
        """
        
        
    def __ne__(self, other):
        """ Return true if another Client does not have all identical fields
        
        @type other: Client
        @param other: the other Client to compare to.
        
        @rtype: Boolean
        @returns: False if the Clients are identical, otherwise True
        
        
        """
        return not __eq__(other)


    def __init__(self):
        """ Construct a new Client using the default configuration file 
        
        @rtype: Client
        @returns: the new Client
        
        
        """
        pass

 
    def get_api_version(self):
        """ Retrieve the API version from the server

        @rtype: String
        @returns: the API version string returned by the server
        
        @raise APIError: when the API request is not successful


        """
        pass


    def get_annotation_context(self):
        """ Retrieve the annotation context from the serve

        @rtype: Dict
        @returns: the annotation context
        
        @raise APIError: when the API request is not successful


        """
        pass


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
        pass
    
    
    def get_item(self, item_url):
        """ Retrieves the item metadata from the server, as an Item object
        
        @type item_url: String
        @param item_url: URL of the item

        @rtype: Item
        @returns: the corresponding metadata, as an Item object
        
        @raise APIError: when the API request is not successful

        
        """

        
    def get_primary_text(self, item_url):
        """ Retrieve the primary text for an item from the server
         
        @type item_url: String
        @param item_url: URL of the item
        
        @rtype: String
        @returns: the item's primary text if it has one, otherwise None
        
        """
        
        
    def get_item_annotatons(self, item_url, type=None, label=None):
        """ Retrieve the annotations for an item from the server
        
        @type item_url: String
        @param item_url: URL of the item
        @type type: String
        @param type: return only results with a matching Type field
        @type label: String
        @param label: return only results with a matching Label field
        
        @rtype: String
        @returns: the annotations as a JSON string
        
    
        """
        
    def upload_annotation(self, item_url, annotation):
        """ Upload the given annotation to the server
        
        @type item_url: String
        @param item_url: the URL of the item corresponding to the annotation
        @type annotation: String
        @param annotation: the annotation, as a JSON string
        
        @rtype: String
        @returns: the server response
        
        
        """

        
    def get_collection_info(self, collection_url):
        """ Retrieve information about the specified Collection from the server
        
        @type collection_url: String
        @param collection_url: the URL of the collection
        
        @rtype: Dict
        @returns: a Dict containing information about the Collection
        
        
        """
        
        
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
        
    def search_metadata(self, query):
        """ Submit a search query to the server and retrieve the results
        
        @type query: String
        @param query: the search query
        
        @rtype: ItemGroup
        @returns: the search results
        
        @raise APIError: when the API request is not successful
        
         
        """
        
        
    def get_item_list(self, item_list_url):
        """ Retrieve an item list from the server as an ItemList object

        @type item_list_url: String
        @param item_list_url: URL of the item list to retrieve

        @rtype: ItemList
        @returns: The ItemList


        """
        pass
        

class ItemGroup:
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
        self.url = url
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
        return (url == other.url and 
                item_urls == other.item_urls and  
                client == other.client)
        
    def __ne__(self, other):
        """ Return true if another ItemGroup does not have all identical fields
        
        @type other: ItemGroup
        @param other: the other ItemGroup to compare to.
        
        @rtype: Boolean
        @returns: False if the ItemGroups are identical, otherwise True
        
        
        """
        return not __eq__(other)        

        
    def __contains__(self, item):
        """ Check if the given item is in this ItemGroup

        @param item: either an item URL as a String, or an Item object

        @rtype: Boolean
        @returns: True if the item is present, False otherwise


        """
        
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

    def intersection(self, other):
        """ Returns the intersection of this ItemGroup with another ItemGroup 
        which has the an identical Client
        
        @type other: ItemGroup
        @param other: the other ItemGroup
        
        @rtype: ItemGroup
        @returns: a new ItemGroup containing all items that appear in both groups
        
        @raise ValueError: if the other ItemGroup does not have the same Client
       
       
        """
       
        
    def __iter__(self):
        """ Iterate over the item URLs in this ItemGroup """

        return iter(item_urls)

        
    def __len__(self):
        """ Return the number of items in this ItemGroup

        @rtype: int
        @returns: the number of items in this ItemGroup


        """
        return len(item_urls)


    def get_all(self):
        """ Retrieve the metadata for all items in this list from the server,
        as Item objects

        @rtype: List
        @returns: a List of the corresponding Item objects
        
        @raise APIError: when the API request is not successful


        """
        pass

    def item_url(self, item_index):
        """ Return the URL of the specified item

        @type item_index: int
        @param item_index: the index of the item URL

        @rtype: String
        @returns: the URL of the item

        
        """
        pass


    def __getitem__(self, key):
        """ Return the URL of the specified item

        @type key: int
        @param key: the index of the item URL

        @rtype: String
        @returns: the URL of the item

        
        """
        try:
            return item_url(int(key))
        except IndexError, ValueError:
            raise KeyError


    def item_urls(self):
        """ Return a list of all item URLs for this ItemGroup

        @rtype: List
        @returns: List of item URLs


        """
        pass


    def get_item(self, item_index):
        """ Retrieve the metadata for a specific item in this ItemGroup
        
        @type item_index: int
        @param item_index: the index of the item
        
        @rtype: Dict
        @returns: the metadata
        
        @raise APIError: when the API request is not successful
        
        
        """
        pass

        
    def save_as_itemlist(name):
        """ Save this ItemGroup to the server as a new item list, with the
        specified name

        @type name: String
        @param name: the name to give the new item list

        @rtype: String
        @returns: the URL of the newly created item list
        
        @raise APIError: when the API request is not successful

      
        """

        
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
        super(self.__class__, self).__init__(item_urls, client) #augh
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
        
    def url(self):
        """ Return the URL corresponding to this ItemList
        
        @rtype: String
        @returns: the URL
        

        """
        pass

    def refresh(self):
        """ Update this ItemList by re-downloading it from the server
        
        @raise APIError: when the API request is not successful


        """
        pass
        
    def append(items):
        """ Add some items to this ItemList and save the changes to the server

        @param items: the items to add, either as a List of Item objects, an
            ItemList, a List of item URLs as Strings, a single item URL as a
            String, or a single Item object
        
        @raise APIError: when the API request is not successful
        
        
        """
        
    def __eq__(self, other):
        """ Return true if another ItemList has all identical fields
        
        @type other: ItemList
        @param other: the other ItemList to compare to.
        
        @rtype: Boolean
        @returns: True if the ItemLists are identical, otherwise False
        
        
        """
        
    def __ne__(self, other):
        """ Return true if another ItemList does not have all identical fields
        
        @type other: ItemList
        @param other: the other ItemList to compare to.
        
        @rtype: Boolean
        @returns: False if the ItemLists are identical, otherwise True
        
        
        """
        return not __eq__(other)
        
        
        
class Item:
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
        self.url = metadata['url']
        self.metadata = metadata
        self.client = client
        
        
    def metadata(self):
        """ Return the metadata for this Item
        
        @rtype: Dict
        @returns: the metadata for this Item
        
        
        """
        
        
    def url(self):
        """ Return the URL for this Item
        
        @rtype: String
        @returns: the URL for this Item
        
        
        """
        
    def get_documents(self):
        """ Get the metadata for each of the documents corresponding
        to this Item, each as a Document object
        
        @rtype: List
        @returns: a list of Document object corresponding to this
            Item's documents
           
           
        """

        
    def get_document(self, index):
        """ Get the metadata for the specified document
        
        @type index: int
        @param index: the index of the document
        
        @rtype: Document
        @returns: the metadata for the specified document
        
        
        """
        
        
    def get_primary_text(self):
        """ TODO """
        
        
    def get_annotation(self, type=None, label=None):
         """ Retrieve the annotations for this item from the server
        
        @type type: String
        @param type: return only results with a matching Type field
        @type label: String
        @param label: return only results with a matching Label field
        
        @rtype: String
        @returns: the annotations as a JSON string
        
    
        """   
        
            
    def upload_annotation(self, annotation):
        """ Upload the given annotation to the server

        @type annotation: String
        @param annotation: the annotation, as a JSON string
        
        @rtype: String
        @returns: the server response
        
        
        """
        
    def __str__(self):
        """ Return the URL of this Item
        
        @rtype: String
        @returns: the URL of this Item
        
        
        """
        
    def __eq__(self, other):
        """ Return true if and only if this Item is identical to another
        
        @type other: Item
        @param other: the other Item
        
        @rtype: Boolean
        @returns: True if both Items have all identical fields, otherwise False
        
        
        """
        
        
    def __ne__(self, other):
        """ Return true if and only if this Item is not identical to another
        
        @type other: Item
        @param other: the other Item
        
        @rtype: Boolean
        @returns: False if both Items have all identical fields, otherwise True
        
        
        """     
        
        
        
class Document:
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
        self.url = metadata['url']
        self.metadata = metadata
        self.client = client
        
        
    def metadata(self):
        """ Return the metadata for this Document
        
        @rtype: Dict
        @returns: the metadata for this Document
        
        
        """
        
        
    def url(self):
        """ Return the URL for this Document
        
        @rtype: String
        @returns: the URL for this Document
        
        
        """
        
        
    def __str__(self):
        """ Return the URL of this Document
        
        @rtype: String
        @returns: the URL of this Document
        
        
        """
        
    def __eq__(self, other):
        """ Return true if and only if this Document is identical to another
        
        @type other: Document
        @param other: the other Document
        
        @rtype: Boolean
        @returns: True if both Documents have all identical fields, otherwise False
        
        
        """
        
    def __ne__(self, other):
        """ Return true if and only if this Document is not identical to another
        
        @type other: Document
        @param other: the other Document
        
        @rtype: Boolean
        @returns: False if both Documents have all identical fields, otherwise True
        
        
        """
        
    def get_content(self):
        """ Retrieve the content for this Document from the server
        
        @rtype: TODO
        @returns: the content data
        
        
        """
        
    def download_content(self, path):
        """ Download the content for this document to a file
        
        @type path: String
        @param path: the path to which to write the data
        
        @rtype: String
        @returns: the path to the downloaded file
        
        
        """
        