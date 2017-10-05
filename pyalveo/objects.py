"""Object based interface to the Alveo API"""


import os

try:
    from urllib.parse import unquote
except ImportError:
    from urllib import unquote

class ItemGroup(object):
    """ Represents an ordered group of Alveo items"""

    def __init__(self, item_urls, client):
        """ Construct a new ItemGroup

        :type item_urls: List or ItemGroup
        :param item_urls: List of URLs of items in this group,
            or an ItemGroup object
        :type client: Client
        :param client: the API client to use for API operations

        :rtype: ItemGroup
        :returns: the new ItemGroup
        """
        self.item_urls = list(item_urls)
        self.client = client


    def set_client(self, new_client):
        """ Set the Client for this ItemGroup

        :type new_client: Client
        :param new_client: the new Client

        :rtype: Client
        :returns: the new Client


        """
        self.client = new_client
        return new_client


    def __eq__(self, other):
        """ Return true if another ItemGroup has all identical fields

        :type other: ItemGroup
        :param other: the other ItemGroup to compare to.

        :rtype: Boolean
        :returns: True if the ItemGroups are identical, otherwise False


        """
        return (self.urls() == other.urls() and self.client == other.client)


    def __ne__(self, other):
        """ Return true if another ItemGroup does not have all identical fields

        :type other: ItemGroup
        :param other: the other ItemGroup to compare to.

        :rtype: Boolean
        :returns: False if the ItemGroups are identical, otherwise True


        """
        return not self.__eq__(other)


    def __contains__(self, item):
        """ Check if the given item is in this ItemGroup

        :param item: either an item URL as a String, or an Item object

        :rtype: Boolean
        :returns: True if the item is present, False otherwise


        """
        return str(item) in self.item_urls


    def __add__(self, other):
        """ Returns the union of this ItemGroup and another ItemGroup
        which has an identical Client

        :type other: ItemGroup
        :param other: the other ItemGroup

        :rtype: ItemGroup
        :returns: A new ItemGroup containing the union of the member items
            of this and the other group

        @raises ValueError: if the other ItemGroup does not have the same Client


        """
        if self.client != other.client:
            raise ValueError("To add ItemGroups, they must have the same Client")
        combined_list = self.item_urls
        combined_list += [url for url in other.item_urls if url not in self.item_urls]
        return ItemGroup(combined_list, self.client)


    def __sub__(self, other):
        """ Returns the relative complement of this ItemGroup in another
        ItemGroup which has an identical Client

        :type other: ItemGroup
        :param other: the other ItemGroup

        :rtype: ItemGroup
        :returns: a new ItemGroup containing all member items of this
            ItemGroup except those also appearing in the other ItemGroup

        @raises ValueError: if the other ItemGroup does not have the same Client


        """
        if self.client != other.client:
            raise ValueError("To subtract ItemGroups, they must have the same Client")
        new_list = [url for url in self.item_urls if url not in other.item_urls]
        return ItemGroup(new_list, self.client)


    def intersection(self, other):
        """ Returns the intersection of this ItemGroup with another ItemGroup
        which has the an identical Client

        :type other: ItemGroup
        :param other: the other ItemGroup

        :rtype: ItemGroup
        :returns: a new ItemGroup containing all items that appear in both groups

        @raises ValueError: if the other ItemGroup does not have the same Client


        """
        if self.client != other.client:
            raise ValueError("To intersect ItemGroups, they must have the same Client")
        new_list = [url for url in self.item_urls if url in other.item_urls]
        return ItemGroup(new_list, self.client)


    def __iter__(self):
        """ Iterate over the item URLs in this ItemGroup

        :rtype: iterator
        :returns: an iterator over the item URLs in this ItemGroup
        """

        return iter(self.item_urls)


    def __len__(self):
        """ Return the number of items in this ItemGroup

        :rtype: int
        :returns: the number of items in this ItemGroup


        """
        return len(self.item_urls)


    def get_all(self, force_download=False):
        """ Retrieve the metadata for all items in this list from the server,
        as Item objects

        :rtype: List
        :returns: a List of the corresponding Item objects
        :type force_download: Boolean
        :param force_download: True to download from the server
            regardless of the cache's contents

        :raises: APIError if the API request is not successful


        """
        cl = self.client
        return [cl.get_item(item, force_download) for item in self.item_urls]


    def item_url(self, item_index):
        """ Return the URL of the specified item

        :type item_index: int
        :param item_index: the index of the item URL

        :rtype: String
        :returns: the URL of the item


        """
        return self.item_urls[item_index]


    def __getitem__(self, key):
        """ Return the URL of the specified item

        :type key: int
        :param key: the index of the item URL

        :rtype: String
        :returns: the URL of the item


        """
        try:
            return self.item_urls[key]
        except (IndexError, ValueError) as e:
            raise KeyError(e.message)


    def urls(self):
        """ Return a list of all item URLs for this ItemGroup

        :rtype: List
        :returns: List of item URLs


        """
        return self.item_urls


    def get_item(self, item_index, force_download=False):
        """ Retrieve the metadata for a specific item in this ItemGroup

        :type item_index: int
        :param item_index: the index of the item
        :type force_download: Boolean
        :param force_download: True to download from the server
            regardless of the cache's contents

        :rtype: Item
        :returns: the metadata, as an Item object

        :raises: APIError if the API request is not successful


        """
        return self.client.get_item(self.item_urls[item_index], force_download)


    def add_to_item_list_by_name(self, name):
        """ Add the items in this ItemGroup to the specified Item List on
        the server, creating the item list if it does not already exist

        :type name: String
        :param name: the name of the Item List

        :rtype: String
        :returns: the URL of the Item List

        :raises: APIError if the API request is not successful


        """
        return self.client.add_to_item_list_by_name(self.item_urls, name)


    def add_to_item_list(self, item_list_url):
        """ Add the items in this ItemGroup to the specified Item List on
        the server, creating the item list if it does not already exist

        :type item_list_url: String or ItemList
        :param item_list_url: the URL of the Item List,
            or an ItemList object

        :rtype: String
        :returns: the URL of the Item List

        :raises: APIError if the API request is not successful


        """
        return self.client.add_to_item_list(self.item_urls, item_list_url)

class ItemList(ItemGroup):
    """ Represents a Alveo Item List residing on the server

        Extends ItemGroup with additional Item List-specific functionality


    """
    def __init__(self, item_urls, client, url, name):
        """ Construct a new ItemList

        :type item_urls: List or ItemGroup
        :param item_urls: a List of the item URLs in this Item List,
            or an ItemGroup object
        :type client: Client
        :param client: the API client to use for API operations
        :type url: String
        :param url: the URL of this Item List
        :type name: String
        :param name: the name of this Item List

        :rtype: ItemList
        :returns: the new ItemList


        """
        super(ItemList, self).__init__(list(item_urls), client) #augh
        self.list_url = url
        self.list_name = name

    def __str__(self):
        """ Return the URL corresponding to this ItemList

        :rtype: String
        :returns: the URL


        """
        return self.url()


    def name(self):
        """ Return the name of this Item List

        :rtype: String
        :returns: the name of this Item List


        """
        return self.list_name


    def url(self):
        """ Return the URL corresponding to this ItemList

        :rtype: String
        :returns: the URL


        """
        return self.list_url


    def refresh(self):
        """ Update this ItemList by re-downloading it from the server

        :rtype: ItemList
        :returns: this ItemList, after the refresh

        :raises: APIError if the API request is not successful


        """
        refreshed = self.client.get_item_list(self.url())
        self.item_urls = refreshed.urls()
        self.list_name = refreshed.name()
        return self


    def append(self, items):
        """ Add some items to this ItemList and save the changes to the server

        :param items: the items to add, either as a List of Item objects, an
            ItemList, a List of item URLs as Strings, a single item URL as a
            String, or a single Item object

        :rtype: String
        :returns: the server success message

        :raises: APIError if the API request is not successful


        """
        resp = self.client.add_to_item_list(items, self.url())
        self.refresh()
        return resp

    def __eq__(self, other):
        """ Return true if another ItemList has all identical fields

        :type other: ItemList
        :param other: the other ItemList to compare to.

        :rtype: Boolean
        :returns: True if the ItemLists are identical, otherwise False


        """
        return (self.url() == other.url() and
                self.name() == other.name() and
                super(ItemList, self).__eq__(other))


    def __ne__(self, other):
        """ Return true if another ItemList does not have all identical fields

        :type other: ItemList
        :param other: the other ItemList to compare to.

        :rtype: Boolean
        :returns: False if the ItemLists are identical, otherwise True


        """
        return not self.__eq__(other)

class Item(object):
    """ Represents a single Alveo item """

    def __init__(self, metadata, client):
        """ Create a new Item object

        :type metadata: Dict
        :param metadata: the metadata for this Item
        :type client: Client
        :param client: the API client to use for API operations

        :rtype: Item
        :returns: the new Item


        """
        self.item_url = metadata['alveo:catalog_url']
        self.item_metadata = metadata
        self.client = client


    def metadata(self):
        """ Return the metadata for this Item

        :rtype: Dict
        :returns: the metadata for this Item


        """
        return self.item_metadata


    def url(self):
        """ Return the URL for this Item

        :rtype: String
        :returns: the URL for this Item


        """
        return self.item_url


    def get_documents(self):
        """ Return the metadata for each of the documents corresponding
        to this Item, each as a Document object

        :rtype: List
        :returns: a list of Document objects corresponding to this
            Item's documents
        """
        return[Document(d, self.client) for d in self.metadata()['alveo:documents']]


    def get_document(self, index=0):
        """ Return the metadata for the specified document, as a
        Document object

        :type index: int
        :param index: the index of the document

        :rtype: Document
        :returns: the metadata for the specified document


        """
        try:
            return Document(self.metadata()['alveo:documents'][index], self.client)
        except IndexError:
            raise ValueError('No document exists for this item with index: '
                             + str(index))


    def get_primary_text(self, force_download=False):
        """ Retrieve the primary text for this item from the server

        :type force_download: Boolean
        :param force_download: True to download from the server
            regardless of the cache's contents

        :rtype: String
        :returns: the primary text

        :raises: APIError if the API request is not successful


        """
        return self.client.get_primary_text(self.url(), force_download)


    def get_annotations(self, atype=None, label=None):
        """ Retrieve the annotations for this item from the server

        :type atype: String
        :param atype: return only results with a matching Type field
        :type label: String
        :param label: return only results with a matching Label field

        :rtype: String
        :returns: the annotations as a JSON string

        :raises: APIError if the API request is not successful


        """
        return self.client.get_item_annotations(self.url(), atype, label)


    def get_annotation_types(self):
        """ Retrieve the annotation types for this item from the server

        :rtype: List
        :returns: a List specifying the annotation types

        :raises: APIError if the request was not successful


        """
        return self.client.get_annotation_types(self.url())


    def add_annotations(self, annotations):
        """Add annotations to an item

        :type annotation: String
        :param annotations: the annotations, a list of dictionaries

        :rtype: String
        :returns: the server success response

        :raises: APIError if the API request is not successful


        """
        return self.client.add_annotations(self.url(), annotations)


    def __str__(self):
        """ Return the URL of this Item

        :rtype: String
        :returns: the URL of this Item


        """
        return self.url()


    def __eq__(self, other):
        """ Return true if and only if this Item is identical to another

        :type other: Item
        :param other: the other Item

        :rtype: Boolean
        :returns: True if both Items have all identical fields, otherwise False


        """
        return (self.url() == other.url() and
                self.metadata() == other.metadata() and
                self.client == other.client)


    def __ne__(self, other):
        """ Return true if and only if this Item is not identical to another

        :type other: Item
        :param other: the other Item

        :rtype: Boolean
        :returns: False if both Items have all identical fields, otherwise True


        """
        return not self.__eq__(other)


    def add_to_item_list(self, item_list_url):
        """ Add this item to the specified Item List on the server

        :type item_list_url: String or ItemList
        :param item_list_url: the URL of the Item list,
            or an ItemList object

        :rtype: String
        :returns: the URL of the Item List

        :raises: APIError if the API request is not successful


        """
        return self.client.add_to_item_list([self.url()], item_list_url)


    def add_to_item_list_by_name(self, name):
        """ Add this item to the specified Item List on the server

        :type name: String
        :param name: the name of the Item list

        :rtype: String
        :returns: the URL of the Item List

        :raises: APIError if the API request is not successful


        """
        return self.client.add_to_item_list_by_name([self.url()], name)

class Document(object):
    """ Represents a single Alveo document """

    def __init__(self, metadata, client):
        """ Create a new Document

        :type metadata: Dict
        :param metadata: the metadata for this Document
        :type client: Client
        :param client: the API client to use for API operations

        :rtype: Document
        :returns: the new Document


        """
        self.doc_url = metadata['alveo:url']
        self.doc_metadata = metadata
        self.client = client


    def metadata(self):
        """ Return the metadata for this Document

        :rtype: Dict
        :returns: the metadata for this Document


        """
        return self.doc_metadata


    def url(self):
        """ Return the URL for this Document

        :rtype: String
        :returns: the URL for this Document


        """
        return self.doc_url


    def __str__(self):
        """ Return the URL of this Document

        :rtype: String
        :returns: the URL of this Document


        """
        return self.url()


    def __eq__(self, other):
        """ Return true if and only if this Document is identical to another

        :type other: Document
        :param other: the other Document

        :rtype: Boolean
        :returns: True if both Documents have all identical fields, otherwise False


        """
        return (self.url() == other.url() and
                self.metadata() == other.metadata() and
                self.client == other.client)


    def __ne__(self, other):
        """ Return true if and only if this Document is not identical to another

        :type other: Document
        :param other: the other Document

        :rtype: Boolean
        :returns: False if both Documents have all identical fields, otherwise True


        """
        return not self.__eq__(other)


    def get_content(self, force_download=False):
        """ Retrieve the content for this Document from the server

        :type force_download: Boolean
        :param force_download: True to download from the server
            regardless of the cache's contents

        :rtype: String
        :returns: the content data

        :raises: APIError if the API request is not successful


        """
        return self.client.get_document(self.url(), force_download)


    def get_filename(self):
        """ Get the original filename for this document

        :rtype: String
        :returns: the filename


        """
        return unquote(self.url().rsplit('/',1)[1])


    def download_content(self, dir_path='', filename=None,
                         force_download=False):
        """ Download the content for this document to a file

        :type dir_path: String
        :param dir_path: the path to which to write the data
        :type filename: String
        :param filename: filename to write to (if None, defaults to the document's
            name, as specified by its metadata
        :type force_download: Boolean
        :param force_download: True to download from the server
            regardless of the cache's contents

        :rtype: String
        :returns: the path to the downloaded file

        :raises: APIError if the API request is not successful


        """
        if filename is None:
            filename = self.get_filename()
        path = os.path.join(dir_path, filename)
        data = self.client.get_document(self.url(), force_download)
        with open(path, 'wb') as f:
            f.write(data)
        return path
