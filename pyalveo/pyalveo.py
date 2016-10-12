import os


try:
    from urllib.parse import urlencode, unquote
except ImportError:
    from urllib import urlencode, unquote

import requests
import json

from .cache import Cache

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


CONFIG_DEFAULT = {'max_age': 0,
                  'use_cache': "true",
                  'update_cache': "true",
                  'cache_dir': '~/alveo_cache',
                  'alveo_config': '~/alveo.config',
              }

CONTEXT ={'ausnc': 'http://ns.ausnc.org.au/schemas/ausnc_md_model/',
          'corpus': 'http://ns.ausnc.org.au/corpora/',
          'dc': 'http://purl.org/dc/terms/',
          'dcterms': 'http://purl.org/dc/terms/',
          'foaf': 'http://xmlns.com/foaf/0.1/',
          'hcsvlab': 'http://alveo.edu.au/vocabulary/',
          'austalk': "http://ns.austalk.edu.au/",
          'olac': "http://www.language-archives.org/OLAC/1.1/",
          'rdf': "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
          'schema': "http://schema.org/",
          'xsd': "http://www.w3.org/2001/XMLSchema#",
          }


class Client(object):
    """ Client object used to manipulate Alveo objects and interface
    with the API


    """
    def __init__(self, api_key=None, api_url=None, cache=None,
                 use_cache=None, cache_dir=None, update_cache=None, configfile=None,
                 verifySSL=True):
        """ Construct a new Client with the specified parameters.
        Unspecified parameters will be derived from the users ~/alveo.config
        file if present.

        :type api_key: :class:String
        :param api_key: the API key to use
        :type cache: :class:Cache
        :param cache: the Cache to use
        :type api_url: String
        :param api_url: the base URL for the API server used
        :type use_cache: Boolean
        :param use_cache: True to fetch available data from the
            cache database, False to always fetch data from the server
        :type update_cache: Boolean
        :param update_cache: True to update the cache database with
            downloaded data, False to never write to the cache
        :type verifySSL: Boolean
        :param verifySSL True to enforce checking of SSL certificates, False
            to disable checking (eg. for staging/testing servers)

        :rtype: Client
        :returns: the new Client
        """

        config = self._read_config(configfile)

        if api_key!=None:
            self.api_key = api_key
        else:
            self.api_key = config['apiKey']

        if api_url!=None:
            self.api_url = api_url
        else:
            self.api_url = config['base_url']

        if use_cache!=None:
            self.use_cache = use_cache
        else:
            self.use_cache = config['use_cache'] == "true"

        if cache_dir!=None:
            self.cache_dir = cache_dir
        else:
            self.cache_dir = config['cache_dir']

        if update_cache!=None:
            self.update_cache = update_cache
        else:
            self.update_cache = config['update_cache'] == "true"

        self.verifySSL = verifySSL

        # grab the default context
        self.context = CONTEXT


        # configure a cache if we want to read or write to it
        if self.use_cache or self.update_cache:
            if cache == None:
                if 'max_age' in config:
                    self.cache = Cache(self.cache_dir, config['max_age'])
                else:
                    self.cache = Cache(self.cache_dir)
            else:
                self.cache = cache
        else:
            self.cache = None

        # Create a client successfully only when the api key is correct
        # Otherwise raise an Error
        try:
            self.get_item_lists()
        except APIError:
            raise APIError(http_status_code="401", response="Unauthorized", msg="Client could not be created. Check your api key")


    @staticmethod
    def _read_config(configfile=None):

        config = CONFIG_DEFAULT

        if configfile==None:
            alveo_config = os.path.expanduser(CONFIG_DEFAULT['alveo_config'])
        else:
            alveo_config = configfile

        alveo_config = os.path.expandvars(alveo_config)

        if  os.path.exists(alveo_config):
            with open(alveo_config) as h:
                config.update(json.load(h))

        config['cache_dir'] = os.path.expandvars(os.path.expanduser(config['cache_dir']))

        return config



    def __eq__(self, other):
        """ Return true if another Client has all identical fields

        :type other: $1
        :param other: the other Client to compare to.

        :rtype: Boolean
        :returns: True if the Clients are identical, otherwise False


        """
        return (self.api_key == other.api_key and
                self.cache == other.cache and
                self.use_cache == other.use_cache and
                self.update_cache == other.update_cache)

    def __ne__(self, other):
        """ Return true if another Client does not have all identical fields

        :type other: Client
        :param other: the other Client to compare to.

        :rtype: Boolean
        :returns: False if the Clients are identical, otherwise True


        """
        return not self.__eq__(other)


    def api_request(self, url, data=None, method='GET', raw=False, file=None):
        """ Perform an API request to the given URL, optionally
        including the specified data

        :type url: String
        :param url: the URL to which to make the request
        :type data: String
        :param data: the data to send with the request, if any
        :type method: String
        :param method: the HTTP request method
        :type raw: Boolean
        :para raw: if True, return the raw response, otherwise treat as JSON and return the parsed response
        :type file: String
        :param file: (Optional) full path to file to be uploaded in a POST request


        :returns: the response from the server either as a raw response or a Python dictionary
        generated by parsing the JSON response

        :raises: APIError if the API request is not successful


        """
        headers = {'X-API-KEY': self.api_key, 'Accept': 'application/json'}
        if data is not None and file is None:
            headers['Content-Type'] = 'application/json'

        if method is 'GET':
            response = requests.get(url, headers=headers, verify=self.verifySSL)
        elif method is 'POST':
            if file is not None:
                response = requests.post(url, headers=headers, data=data, files={'file':open(file,'rb')}, verify=self.verifySSL)
            else:
                response = requests.post(url, headers=headers, data=data, verify=self.verifySSL)
        elif method is 'PUT':
            response = requests.put(url, headers=headers, data=data, verify=self.verifySSL)
        elif method is 'DELETE':
            response = requests.delete(url, headers=headers, verify=self.verifySSL)

        if response.status_code != requests.codes.ok:
            raise APIError(response.status_code, '', "Error accessing API (url: %s, method: %s)\nData: %s\nMessage: %s" % (url, method, data, response.text))

        if raw:
            return response.content
        else:
            return response.json()


    def add_context(self, prefix, url):
        """ Add a new entry to the context that will be used
        when uploading new metadata records.

        :type prefix: String
        :para prefix: the namespace prefix (eg. dc)

        :type url: String
        :para url: the url to associate with the prefix

        """

        self.context[prefix] = url


    def get_api_version(self):
        """ Retrieve the API version from the server

        :rtype: String
        :returns: the API version string returned by the server

        :raises: APIError if the API request is not successful


        """
        resp = self.api_request(self.api_url + '/version')
        return resp['API version']


    def get_annotation_context(self):
        """ Retrieve the JSON-LD annotation context from the server

        :rtype: Dict
        :returns: the annotation context

        :raises: APIError if the API request is not successful


        """
        return self.api_request(self.api_url + '/schema/json-ld')


    def get_collections(self):
        """Retrieve a list of the collection URLs for all collections
        hosted on the server.

        :rtype: List
        :returns: a List of tuples of (name, url) for each collection
        """
        result = self.api_request(self.api_url + '/catalog')

        # get the collection name from the url
        return [(os.path.split(x)[1], x) for x in result['collections']]


    def get_item_lists(self):
        """ Retrieve metadata about each of the Item Lists associated
        with this Client's API key

        Returns a List of Dicts, each containing metadata regarding
        an Item List, with the following key-value pairs:

            - name: the name of the Item List
            - url: the URL of the Item List
            - num_items: the number of items in the Item List

        :rtype: List
        :returns: a List of Dicts, each containing metadata regarding
            an Item List

        :raises: APIError if the API request is not successful


        """
        return self.api_request(self.api_url + '/item_lists.json')


    def get_item(self, item_url, force_download=False):
        """ Retrieve the item metadata from the server, as an Item object

        :type item_url: String or Item
        :param item_url: URL of the item, or an Item object

        :rtype: Item
        :returns: the corresponding metadata, as an Item object
        :type force_download: Boolean
        :param force_download: True to download from the server
            regardless of the cache's contents

        :raises: APIError if the API request is not successful


        """
        item_url = str(item_url)

        if (self.use_cache and
                not force_download and
                self.cache.has_item(item_url)):
            item_json = self.cache.get_item(item_url)
        else:
            item_json = self.api_request(item_url, raw=True)
            if self.update_cache:
                self.cache.add_item(item_url, item_json)

        return Item(json.loads(item_json.decode('utf-8')), self)


    def get_document(self, doc_url, force_download=False):
        """ Retrieve the data for the given document from the server

        :type doc_url: String or Document
        :param doc_url: the URL of the document, or a Document object
        :type force_download: Boolean
        :param force_download: True to download from the server
            regardless of the cache's contents

        :rtype: String
        :returns: the document data

        :raises: APIError if the API request is not successful


        """
        doc_url = str(doc_url)
        if (self.use_cache and
                not force_download and
                self.cache.has_document(doc_url)):
            doc_data = self.cache.get_document(doc_url)
        else:
            doc_data = self.api_request(doc_url, raw=True)
            if self.update_cache:
                self.cache.add_document(doc_url, doc_data)

        return doc_data


    def get_primary_text(self, item_url, force_download=False):
        """ Retrieve the primary text for an item from the server

        :type item_url: String or Item
        :param item_url: URL of the item, or an Item object
        :type force_download: Boolean
        :param force_download: True to download from the server
            regardless of the cache's contents

        :rtype: String
        :returns: the item's primary text if it has one, otherwise None

        :raises: APIError if the request was not successful


        """
        item_url = str(item_url)
        metadata = self.get_item(item_url).metadata()

        try:
            primary_text_url = metadata['alveo:primary_text_url']
        except KeyError:
            return None

        if primary_text_url == 'No primary text found':
            return None

        if (self.use_cache and
                not force_download and
                self.cache.has_primary_text(item_url)):
            primary_text = self.cache.get_primary_text(item_url)
        else:
            primary_text = self.api_request(primary_text_url, raw=True)
            if self.update_cache:
                self.cache.add_primary_text(item_url, primary_text)

        return primary_text


    def get_item_annotations(self, item_url, annotation_type=None, label=None):
        """ Retrieve the annotations for an item from the server

        :type item_url: String or Item
        :param item_url: URL of the item, or an Item object
        :type annotation_type: String
        :param annotation_type: return only results with a matching Type field
        :type label: String
        :param label: return only results with a matching Label field

        :rtype: String
        :returns: the annotations as a dictionary, if the item has
            annotations, otherwise None
        The annotation dictionary has keys:
          commonProperties - properties common to all annotations
          @context - the url of the JSON-LD annotation context definition
          alveo:annotations - a list of annotations, each is a dictionary


        :raises: APIError if the request was not successful


        """
        # get the annotation URL from the item metadata, if not present then there are no annotations
        item_url = str(item_url)
        metadata = self.get_item(item_url).metadata()

        try:
            annotation_url = metadata['alveo:annotations_url']
        except KeyError:
            return None


        req_url = annotation_url
        if annotation_type is not None:
            req_url += '?'
            req_url += urlencode((('type', annotation_type),))
        if label is not None:
            if annotation_type is None:
                req_url += '?'
            else:
                req_url += '&'
            req_url += urlencode((('label',label),))
        try:
            return self.api_request(req_url)
        except KeyError:
            return None


    def get_annotation_types(self, item_url):
        """ Retrieve the annotation types for the given item from the server

        :type item_url: String or Item
        :param item_url: URL of the item, or an Item object

        :rtype: List
        :returns: a List specifying the annotation types

        :raises: APIError if the request was not successful


        """
        req_url = item_url + "/annotations/types"
        resp = self.api_request(req_url)
        return resp['annotation_types']


    def add_annotations(self, item_url, annotations):
        """Add annotations to the given item

        :type item_url: String or Item
        :param item_url: the URL of the item corresponding to the annotation,
            or an Item object
        :type annotation: list
        :param annotations: the annotations as a list of dictionaries, each with keys '@type', 'label', 'start', 'end' and 'type'

        :rtype: String
        :returns: the server's success message, if successful

        :raises: APIError if the upload was not successful
        :raises: Exception if the annotations are malformed (missing a required key)
        """
        adict = {'@context': "https://alveo-staging1.intersect.org.au/schema/json-ld"}

        for ann in annotations:
            # verify that we have the required properties
            for key in ('@type', 'label', 'start', 'end', 'type'):
                if not key in ann.keys():
                    raise Exception("required key '%s' not present in annotation" % key)
        adict['@graph'] = annotations

        resp = self.api_request(str(item_url) + '/annotations', method='POST', data=json.dumps(adict))
        return self.__check_success(resp)


    def get_collection_info(self, collection_url):
        """ Retrieve information about the specified Collection from the server

        :type collection_url: String
        :param collection_url: the URL of the collection

        :rtype: Dict
        :returns: a Dict containing information about the Collection

        :raises: APIError if the request was not successful


        """
        return self.api_request(collection_url)


    def create_collection(self, name, metadata):
        """ Create a new collection with the given name
        and attach the metadata.

        :param name: the collection name, suitable for use in a URL (no spaces)
        :type name: String
        :param metadata: a dictionary of metadata values to associate with the new collection
        :type metadata: Dict

        :rtype: String
        :returns: a message confirming creation of the collection

        :raises: APIError if the request was not successful

        """

        payload = {
                    'collection_metadata': metadata,
                    'name': name
                   }

        response = self.api_request(self.api_url + '/catalog', method='POST', data=json.dumps(payload))

        return self.__check_success(response)


    def modify_collection_metadata(self, collection_uri, metadata, replace=None):
        """Modify the metadata for the given collection.

        :param collection_uri: The URI that references the collection
        :type collection_uri: String

        :param metadata: a dictionary of metadata values to add/modify
        :type metadata: Dict

        :rtype: String
        :returns: a message confirming that the metadata is modified

        :raises: APIError if the request was not successful
        """

        payload = {
                    'collection_metadata': metadata,
                    'name': name
                   }

        if not replace is None:
            payload['replace'] = replace

        response = self.api_request(collection_uri, method='PUT', data=json.dumps(payload))

        return self.__check_success(response)

    def get_items(self, collection_uri):
        """Return all items in this collection.

        :param collection_uri: The URI that references the collection
        :type collection_uri: String

        :rtype: List
        :returns: a list of the URIs of the items in this collection

        """

        cname = os.path.split(collection_uri)[1]
        return self.search_metadata("collection_name:%s" % cname)

    def add_text_item(self, collection_uri, name, metadata, text, title=None):
        """Add a new item to a collection containing a single
        text document.

        The full text of the text document is specified as the text
        argument and will be stored with the same name as the
        item and a .txt extension.

        This is a shorthand for the more general add_item method.

        :param collection_uri: The URI that references the collection
        :type collection_uri: String

        :param name: The item name, suitable for use in a URI (no spaces)
        :type name: String

        :param metadata: a dictionary of metadata values describing the item
        :type metadata: Dict

        :param text: the full text of the document associated with this item
        :type text: String


        :param title: document title, defaults to the item name
        :type title: String

        :rtype String
        :returns: the URI of the created item

        :raises: APIError if the request was not successful

        """

        docname = name + ".txt"
        if title is None:
            title = name

        metadata['dcterms:identifier'] = name
        metadata['@type'] = 'ausnc:AusNCObject'
        metadata['hcsvlab:display_document'] = {'@id': docname}
        metadata['hcsvlab:indexable_document'] = {'@id': docname}
        metadata['ausnc:document'] =  [{ '@id': 'document1.txt',
                                         '@type': 'foaf:Document',
                                         'dcterms:extent': len(text),
                                         'dcterms:identifier': docname,
                                         'dcterms:title': title,
                                         'dcterms:type': 'Text'}]

        meta = {'items': [{'metadata': { '@context': self.context,
                                         '@graph': [metadata]
                                        },
                            'documents': [{'content': text, 'identifier': docname}]
                          }]
                }

        response = self.api_request(collection_uri, method='POST', data=json.dumps(meta))

        # this will raise an exception if the request fails
        self.__check_success(response)

        item_uri = collection_uri + "/" + response['success'][0]

        return item_uri


    def add_item(self, collection_uri, name, metadata, documents=None):
        """Add a new item to a collection

        :param collection_uri: The URI that references the collection
        :type collection_uri: String

        :param name: The item name, suitable for use in a URI (no spaces)
        :type name: String

        :param metadata: a dictionary of metadata values describing the item
        :type metadata: Dict

        :param documents: a list of metadata dictionaries, one per document
        :type documents: List of Dict

        :rtype String
        :returns: the URI of the created item

        :raises: APIError if the request was not successful

        """

        metadata['dcterms:identifier'] = name
        metadata['@type'] = 'ausnc:AusNCObject'

        meta = {'items': [{'metadata': { '@context': self.context,
                                         '@graph': [metadata]
                                        }
                          }]
                }

        response = self.api_request(collection_uri, method='POST', data=json.dumps(meta))

        # this will raise an exception if the request fails
        self.__check_success(response)

        item_uri = collection_uri + "/" + response['success'][0]

        return item_uri


    def modify_item(self, item_uri, metadata):
        """Modify the metadata on an item

        """

        md = json.dumps({'metadata': metadata})

        response = self.api_request(item_uri, method='PUT', data=md)
        return self.__check_success(response)


    def delete_item(self, item_uri):
        """Delete an item from a collection

        :param item_uri: the URI that references the item
        :type item_uri: String

        :rtype: String
        :returns: a message confirming that the metadata is modified

        :raises: APIError if the request was not successful
        """

        response = self.api_request(item_uri, method='DELETE')
        return self.__check_success(response)


    def add_document(self, item_uri, name, metadata, content=None, docurl=None, file=None, displaydoc=False):
        """Add a document to an existing item

        :param item_uri: the URI that references the item
        :type item_uri: String

        :param name: The document name
        :type name: String

        :param metadata: a dictionary of metadata values describing the document
        :type metadata: Dict

        :param content: optional content of the document
        :type content: byte array

        :param docurl: optional url referencing the document
        :type docurl: String

        :param file: optional full path to file to be uploaded
        :type file: String

        :param displaydoc: if True, make this the display document for the item
        :type displaydoc: Boolean

        :rtype: String
        :returns: The URL of the newly created document
        """

        if file is not None:
            docid = os.path.basename(file)
        else:
            docid = name

        docmeta = {"metadata": {"@context": self.context,
                                "@type": "foaf:Document",
                                "dcterms:identifier": docid,
                                }
                  }
        # add in metadata we are passed
        docmeta["metadata"].update(metadata)

        if content is not None:
            docmeta['document_content'] = content
        elif docurl is not None:
            docmeta["metadata"]["dcterms:source"] = { "@id": docurl }
        elif file is not None:
            # we only pass the metadata part of the dictionary
            docmeta = docmeta['metadata']
        else:
            raise Exception("One of content, docurl or file must be specified in add_document")

        if file is not None:
            result = self.api_request(item_uri, method='POST', data={'metadata': json.dumps(docmeta)}, file=file)
        else:
            result = self.api_request(item_uri, method='POST', data=json.dumps(docmeta))

        self.__check_success(result)

        if displaydoc:
            itemmeta = {"http://alveo.edu.org/vocabulary/display_document": docid}

            self.modify_item(item_uri, itemmeta)

        doc_uri = item_uri + "/document/" + name
        return doc_uri

    def delete_document(self, doc_uri):
        """Delete a document from an item

        :param doc_uri: the URI that references the document
        :type doc_uri: String

        :rtype: String
        :returns: a message confirming that the document was deleted

        :raises: APIError if the request was not successful
        """

        result = self.api_request(doc_uri, method='DELETE')
        return self.__check_success(result)

    @staticmethod
    def __check_success(resp):
        """ Check a JSON server response to see if it was successful

        :type resp: Dictionary (parsed JSON from response)
        :param resp_json: the response string

        :rtype: String
        :returns: the success message, if it exists

        :raises: APIError if the success message is not present


        """

        if "success" not in resp.keys():
            try:
                raise APIError('200', 'Operation Failed', resp["error"])
            except KeyError:
                raise APIError('200', 'Operation Failed', str(resp))
        return resp["success"]


    def download_items(self, items, file_path, file_format='zip'):
        """ Retrieve a file from the server containing the metadata
        and documents for the speficied items

        :type items: List or ItemGroup
        :param items: List of the the URLs of the items to download,
            or an ItemGroup object
        :type file_path: String
        :param file_path: the path to which to save the file
        :type file_format: String
        :param file_format: the file format to request from the server: specify
            either 'zip' or 'warc'

        :rtype: String
        :returns: the file path

        :raises: APIError if the API request is not successful


        """
        download_url = self.api_url + '/catalog/download_items'
        download_url += '?' + urlencode((('format', file_format),))
        item_data = {'items': list(items)}

        data = self.api_request(download_url, method='POST', data=json.dumps(item_data), raw=True)

        with open(file_path, 'w') as f:
            f.write(data)

        return file_path


    def search_metadata(self, query):
        """ Submit a search query to the server and retrieve the results

        :type query: String
        :param query: the search query

        :rtype: ItemGroup
        :returns: the search results

        :raises: APIError if the API request is not successful


        """
        query_url = (self.api_url +
                     '/catalog/search?' +
                     urlencode((('metadata', query),)))

        resp = self.api_request(query_url)
        return ItemGroup(resp['items'], self)


    def get_item_list(self, item_list_url):
        """ Retrieve an item list from the server as an ItemList object

        :type item_list_url: String or ItemList
        :param item_list_url: URL of the item list to retrieve, or an
            ItemList object

        :rtype: ItemList
        :returns: The ItemList

        :raises: APIError if the request was not successful


        """
        resp = self.api_request(str(item_list_url))
        return ItemList(resp['items'], self, str(item_list_url), resp['name'])


    def get_item_list_by_name(self, item_list_name, category='own'):
        """ Retrieve an item list from the server as an ItemList object

        :type item_list_name: String
        :param item_list_name: name of the item list to retrieve
        :type category: String
        :param category: the category of lists to fetch. At the time of
            writing, supported values are "own" and "shared"

        :rtype: ItemList
        :returns: The ItemList

        :raises: APIError if the request was not successful


        """
        resp = self.api_request(self.api_url + '/item_lists')
        for item_list in resp[category]:
            if item_list['name'] == item_list_name:
                return self.get_item_list(item_list['item_list_url'])
        raise ValueError('List does not exist: ' + item_list_name)


    def add_to_item_list(self, item_urls, item_list_url):
        """ Instruct the server to add the given items to the specified
        Item List

        :type item_urls: List or ItemGroup
        :param item_urls: List of URLs for the items to add,
            or an ItemGroup object
        :type item_list_url: String or ItemList
        :param item_list_url: the URL of the list to which to add the items,
            or an ItemList object

        :rtype: String
        :returns: the server success message, if successful

        :raises: APIError if the request was not successful


        """
        item_list_url = str(item_list_url)
        name = self.get_item_list(item_list_url).name()
        return self.add_to_item_list_by_name(item_urls, name)


    def add_to_item_list_by_name(self, item_urls, item_list_name):
        """ Instruct the server to add the given items to the specified
        Item List (which will be created if it does not already exist)

        :type item_urls: List or ItemGroup
        :param item_urls: List of URLs for the items to add,
            or an ItemGroup object
        :type item_list_name: String
        :param item_list_name: name of the item list to retrieve

        :rtype: String
        :returns: the server success message, if successful

        :raises: APIError if the request was not successful


        """
        url_name = urlencode((('name', item_list_name),))
        request_url = self.api_url + '/item_lists?' + url_name

        data = json.dumps({'items': list(item_urls)})
        resp = self.api_request(request_url,  method='POST', data=data)
        return self.__check_success(resp)


    def rename_item_list(self, item_list_url, new_name):
        """ Rename an Item List on the server

        :type item_list_url: String or ItemList
        :param item_list_url: the URL of the list to which to add the items,
            or an ItemList object
        :type new_name: String
        :param new_name: the new name to give the Item List

        :rtype: ItemList
        :returns: the item list, if successful

        :raises: APIError if the request was not successful


        """
        data = json.dumps({'name': new_name})
        resp = self.api_request(str(item_list_url), data, method="PUT")

        try:
            return ItemList(resp['items'], self, item_list_url, resp['name'])
        except KeyError:
            try:
                raise APIError('200', 'Rename operation failed', resp['error'])
            except KeyError:
                raise APIError('200', 'Rename operation failed', resp)


    def delete_item_list(self, item_list_url):
        """ Delete an Item List on the server

        :type item_list_url: String or ItemList
        :param item_list_url: the URL of the list to which to add the items,
            or an ItemList object

        :rtype: Boolean
        :returns: True if the item list was deleted

        :raises: APIError if the request was not successful
        """

        try:
            resp = self.api_request(str(item_list_url), method="DELETE")

            # all good if it says success
            if 'success' in resp:
                return True
            else:
                raise APIError('200', 'Operation Failed', 'Delete operation failed')
        except APIError as e:
            if e.http_status_code == 302:
                return True
            else:
                raise e


    def sparql_query(self, collection_name, query):
        """ Submit a sparql query to the server to search metadata
        and annotations.

        :type collection_name: String
        :param collection_name: the name of the collection to search
        :type query: String
        :param query: the sparql query

        :rtype: Dict
        :returns: the query result from the server as a Python dictionary
        following the format of the SPARQL JSON result format documented
        at http://www.w3.org/TR/rdf-sparql-json-res/

        :raises: APIError if the request was not successful


        """
        request_url = self.api_url + 'sparql/' + collection_name + '?'
        request_url += urlencode((('query', query),))

        return self.api_request(request_url)




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
