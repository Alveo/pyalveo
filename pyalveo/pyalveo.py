import os
from oauthlib.oauth2.rfc6749.errors import TokenExpiredError

try:
    from urllib.parse import urlencode, unquote
except ImportError:
    from urllib import urlencode, unquote

import requests
from requests_oauthlib import OAuth2Session
import json

from .cache import Cache
from .objects import ItemGroup, ItemList, Item, Document


class APIError(Exception):
    """ Raised when an API operation fails for some reason """
    def __init__(self, http_status_code=None, response=None, msg=''):
        self.http_status_code = http_status_code
        self.response = response
        self.msg = msg

        Exception.__init__(self, str(self))

    def __str__(self):
        ret = 'Error: '
        if self.http_status_code:
            ret += "HTTP " + str(self.http_status_code) + "\n"
        if self.response:
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
          'dcterms': 'http://purl.org/dc/terms/',
          'dc': 'http://purl.org/dc/elements/1.1/',
          'foaf': 'http://xmlns.com/foaf/0.1/',
          'hcsvlab': 'http://alveo.edu.au/vocabulary/',
          'austalk': "http://ns.austalk.edu.au/",
          'olac': "http://www.language-archives.org/OLAC/1.1/",
          'rdf': "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
          'schema': "http://schema.org/",
          'xsd': "http://www.w3.org/2001/XMLSchema#",
          }

#This is here to prevent continuous attempts at getting
#the api key once it is fully phased out
#set to false to not bother trying to get it
API_KEY_DEFAULT = True

class OAuth2(object):
    """ An OAuth2 Manager class for the retrieval and storage of
        all relevant URI's, tokens and client login data.  """

    def __init__(self, api_url, api_key=None, oauth=None, verifySSL=True):
        """ Construct the OAuth requests module along with support for using
            an API Key if Allowed.

        :type api_url: String
        :param api_url: the base URL for the API server used
        :type oauth: Dictionary
        :param oauth dictionary of configuation settings for oauth containing keys
            client_id, client_secret and redirect_url, default None means to use
            api_key instead
        :type api_key: :class:String
        :param api_key: the API key to use, if set, we use this rather than trying OAuth
        :type verifySSL: Boolean
        :param verifySSL True to enforce checking of SSL certificates, False
            to disable checking (eg. for staging/testing servers)

        :rtype: OAuth2
        :returns: the new OAuth2 client that can be used to make API requests
        """

        # Application specific parameters
        self.api_url = api_url
        self.verifySSL = verifySSL
        self.api_key = api_key

        if oauth is not None:
            self.client_id = oauth['client_id']
            self.client_secret = oauth['client_secret']
            self.redirect_url = oauth['redirect_url']
        else:
            self.client_id = None
            self.client_secret = None
            self.redirect_url = None

        if self.client_id is None or self.client_secret is None or self.redirect_url is None:
            # There better be an API Key and I'm allowed to use it or I'll cry
            if not (self.api_key):
                raise APIError(http_status_code="0", response="Local Error", msg="Client could not be created. Check your api key")

        # API Urls derived from the main URL
        self.auth_base_url = self.api_url+'/oauth/authorize'
        self.token_url = self.api_url+'/oauth/token' #grant_type = authorization_code
        self.revoke_url = self.api_url+'/oauth/revoke'
        self.validate_url = self.api_url+'/oauth/token/info'
        self.refresh_url = self.api_url+'/oauth/token' #grant_type = refresh_token

        self.token = None
        self.auto_refresh = False
        self.state = None
        self.auth_url = None

        if not self.verifySSL:
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

        # trigger authorisation if we are to use oauth
        if not self.api_key:
            self.get_authorisation_url()

    def __eq__(self, other):
        """ Return true if another OAuth2 has all identical fields

        :type other: $1
        :param other: the other OAuth2 to compare to.

        :rtype: Boolean
        :returns: True if the OAuth2s are identical, otherwise False


        """
        if not isinstance(other, OAuth2):
            return False
        d1 = dict(self.__dict__)
        d1.pop('state',None)
        d1.pop('auth_url',None)
        d2 = dict(other.__dict__)
        d2.pop('state',None)
        d2.pop('auth_url',None)
        return (d1 == d2)

    def __ne__(self, other):
        """ Return true if another Client does not have all identical fields

        :type other: Client
        :param other: the other Client to compare to.

        :rtype: Boolean
        :returns: False if the Clients are identical, otherwise True


        """
        return not self.__eq__(other)

    def to_dict(self):
        """
            Returns a dict of all of it's necessary components.
            Not the same as the __dict__ method
        """
        data = dict()
        data['api_url'] = self.api_url
        data['api_key'] = self.api_key
        data['verifySSL'] = self.verifySSL
        data['client_id'] = self.client_id
        data['client_secret'] = self.client_secret
        data['redirect_url'] = self.redirect_url
        data['token'] = self.token
        data['state'] = self.state
        data['auth_url'] = self.auth_url
        return data

    def to_json(self):
        """
            Returns a json string containing all relevant data to recreate this pyalveo.OAuth2.
        """
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(json_data):
        """
            Returns a pyalveo.OAuth2 given a json string built from the oauth.to_json() method.
        """
        #If we have a string, then decode it, otherwise assume it's already decoded
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
        oauth_dict = {
                      'client_id':data.get('client_id',None),
                      'client_secret':data.get('client_secret',None),
                      'redirect_url':data.get('redirect_url',None),
                      }
        oauth = OAuth2(api_url=data.get('api_url',None), api_key=data.get('api_key',None),oauth=oauth_dict, verifySSL=data.get('verifySSL',True))
        oauth.token = data.get('token',None)
        oauth.state = data.get('state',None)
        oauth.auth_url = data.get('auth_url',None)
        return oauth

    def get_authorisation_url(self, reset=False):
        """ Initialises the OAuth2 Process by asking the auth server for a login URL.
            Once called, the user can login by being redirected to the url returned by
            this function.
            If there is an error during authorisation, None is returned."""

        if reset:
            self.auth_url = None
        if not self.auth_url:
            try:
                oauth = OAuth2Session(self.client_id,redirect_uri=self.redirect_url)
                print("OA", oauth)
                self.auth_url,self.state = oauth.authorization_url(self.auth_base_url)
                print("OA", self.auth_url, self.state)
            except Exception:
                #print("Unexpected error:", sys.exc_info()[0])
                #print("Could not get Authorisation Url!")
                return None

        return self.auth_url

    def on_callback(self,auth_resp):
        """ Must be called once the authorisation server has responded after
            redirecting to the url provided by 'get_authorisation_url' and completing
            the login there.
            Returns True if a token was successfully retrieved, False otherwise."""
        global API_KEY_DEFAULT
        try:
            oauth = OAuth2Session(self.client_id,state=self.state,redirect_uri=self.redirect_url)
            self.token = oauth.fetch_token(self.token_url,
                                           authorization_response=auth_resp,
                                           client_secret=self.client_secret,
                                           verify=self.verifySSL)
            if not self.api_key and API_KEY_DEFAULT:
                self.get_api_key()
                if not self.api_key:
                    API_KEY_DEFAULT = False
        except Exception:
            #print("Unexpected error:", sys.exc_info()[0])
            #print("Could not fetch token from OAuth Callback!")
            return False
        return True

    def validate(self):
        """  Confirms the current token is still valid.
        Returns True if it is valid, False otherwise. """

        try:
            resp = self.request().get(self.validate_url, verify=self.verifySSL).json()
        except TokenExpiredError:
            return False
        except AttributeError:
            return False

        if 'error' in resp:
            return False
        return True

    def refresh_token(self):
        """  Refreshes access token using refresh token. Returns true if successful, false otherwise. """

        try:
            if self.token:
                self.token = self.request().refresh_token(self.refresh_url, self.token['refresh_token'])
                return True
        except Exception as e:
            # TODO: what might go wrong here - handle this error properly
            #print("Unexpected error:\t\t", str(e))
            #traceback.print_exc()
            pass
        return False

    def revoke_access(self):
        """  Requests that the currently used token becomes invalid. Call this should a user logout. """
        if self.token is None:
            return True
        #Don't try to revoke if token is invalid anyway, will cause an error response anyway.
        if self.validate():
            data = {}
            data['token'] = self.token['access_token']
            self.request().post(self.revoke_url, data=data, json=None,verify=self.verifySSL)
        return True

    def get_user_data(self):
        try:
            response = self.get(self.api_url+"/account/get_details")

            if response.status_code != requests.codes.ok: #@UndefinedVariable
                return None

            return response.json()
        except Exception:
            return None

    def get_api_key(self):
        if self.token is None:
            return False
        try:
            oauth = OAuth2Session(self.client_id,
                                  token=self.token,
                                  redirect_uri=self.redirect_url,
                                  state=self.state)

            response = oauth.get(self.api_url+"/account_api_key",verify=self.verifySSL)

            if response.status_code != requests.codes.ok: #@UndefinedVariable
                return False

            self.api_key = response.json()['apiKey']

            return True
        except Exception:
            return False

    def request(self):
        """ Returns an OAuth2 Session to be used to make requests.
        Returns None if a token hasn't yet been received."""

        headers = {'Accept': 'application/json'}

        #Use API Key if possible
        if self.api_key:
            headers['X-API-KEY'] = self.api_key
            return requests,headers
        else:
            # Try to use OAuth
            if self.token:
                return OAuth2Session(self.client_id, token=self.token),headers
            else:
                raise APIError("No API key and no OAuth session available")

    def get(self, url, **kwargs):
        request,headers = self.request()
        headers.update(kwargs.get('headers',{}))
        if not url.startswith(self.api_url):
            url = self.api_url + url
        return request.get(url, headers=headers, verify=self.verifySSL, **kwargs)

    def post(self, url, **kwargs):
        request,headers = self.request()
        if not url.startswith(self.api_url):
            url = self.api_url + url
        afile = kwargs.pop('file',None)
        if afile is not None:
            #A file was given to us, so we should update headers
            #with what is provided, if not default to: multipart/form-data
            #headers.update(kwargs.get('headers',{'Content-Type':'multipart/form-data'}))
            with open(afile,'rb') as fd:
                response = request.post(url, headers=headers, files={'file':fd}, verify=self.verifySSL, **kwargs)
        else:
            #If there is data but no file then set content type to json
            if kwargs.get('data',None):
                headers['Content-Type'] = 'application/json'
            headers.update(kwargs.get('headers',{}))
            response = request.post(url, headers=headers, verify=self.verifySSL, **kwargs)
        return response

    def put(self, url, **kwargs):
        request,headers = self.request()
        headers['Content-Type'] = 'application/json'
        headers.update(kwargs.get('headers',{}))
        if not url.startswith(self.api_url):
            url = self.api_url + url
        return request.put(url, headers=headers, verify=self.verifySSL, **kwargs)

    def delete(self, url, **kwargs):
        request,headers = self.request()
        headers.update(kwargs.get('headers',{}))
        if not url.startswith(self.api_url):
            url = self.api_url + url
        return request.delete(url, headers=headers, verify=self.verifySSL, **kwargs)


class Client(object):
    """ Client object used to manipulate Alveo objects and interface
    with the API
    """
    def __init__(self, api_key=None, cache=None, api_url=None,
                 use_cache=True, update_cache=True, cache_dir=None,
                 verifySSL=True,
                 oauth=None, configfile=None):

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
        :type oauth: Dictionary
        :param oauth dictionary of configuation settings for oauth containing keys
            client_id, client_secret and redirect_url, default None means to use
            api_key instead
        :type configfile: String
        :param configfile File name to read configuration from, default ~/alveo.config

        :rtype: Client
        :returns: the new Client
        """

        config = self._read_config(configfile)
        # api_key, api_url args override config settings
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = config.get('apiKey', None)

        if api_url:
            self.api_url = api_url
        else:
            self.api_url = config.get('base_url', None)

        #pyAlveo Cache Settings
        if use_cache is not None:
            self.use_cache = use_cache
        else:
            self.use_cache = config.get('use_cache', None)

        if cache_dir:
            self.cache_dir = cache_dir
        else:
            self.cache_dir = config.get('cache_dir', None)

        self.update_cache = update_cache

        # grab the default context
        self.context = config.get('context', CONTEXT)

        # configure a cache if we want to read or write to it
        if self.use_cache or self.update_cache:
            if cache is None or isinstance(cache, str):
                if 'max_age' in config:
                    self.cache = Cache(self.cache_dir, config['max_age'])
                else:
                    self.cache = Cache(self.cache_dir)
            else:
                self.cache = cache
        else:
            self.cache = None

        self.oauth = OAuth2(api_url=self.api_url,
                            oauth=oauth,
                            api_key=self.api_key,
                            verifySSL=verifySSL)

    def to_json(self):
        """
            Returns a json string containing all relevant data to recreate this pyalveo.Client.
        """
        data = dict(self.__dict__)
        data.pop('context',None)
        data['oauth'] = self.oauth.to_dict()
        data['cache'] = self.cache.to_dict()
        return json.dumps(data)

    @staticmethod
    def from_json(json_data):
        """
            Returns a pyalveo.Client given a json string built from the client.to_json() method.
        """
        #If we have a string, then decode it, otherwise assume it's already decoded
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
        oauth_dict = {
                      'client_id':data.get('oauth',{}).get('client_id',None),
                      'client_secret':data.get('oauth',{}).get('client_secret',None),
                      'redirect_url':data.get('oauth',{}).get('redirect_url',None),
                      }
        client = Client(api_key=data.get('api_key',None),
                        api_url=data.get('api_url',None),
                        oauth=oauth_dict,
                        use_cache=data.get('use_cache',None),
                        cache_dir=data.get('cache_dir',None),
                        update_cache=data.get('update_cache',None),
                        verifySSL=data.get('oauth',{}).get('verifySSL',None)
                        )
        client.cache = Cache.from_json(data.get('cache',None))
        client.oauth = OAuth2.from_json(data.get('oauth',None))
        return client

    @staticmethod
    def _read_config(configfile=None):

        # copy the default configuration so we don't update it
        config = CONFIG_DEFAULT.copy()

        if configfile is None:
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
        if not isinstance(other, Client):
            return False
        d1 = dict(self.__dict__)
        d1oauth = d1['oauth']
        d1.pop('oauth',None)
        d1cache = d1['cache']
        d1.pop('cache',None)

        d2 = dict(other.__dict__)
        d2oauth = d2['oauth']
        d2.pop('oauth',None)
        d2cache = d2['cache']
        d2.pop('cache',None)
        return (d1 == d2 and d1oauth == d2oauth and d1cache == d2cache)

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

        if method is 'GET':
            response = self.oauth.get(url)
        elif method is 'POST':
            if file is not None:
                response = self.oauth.post(url, data=data, file=file)
            else:
                response = self.oauth.post(url, data=data)
        elif method is 'PUT':
            response = self.oauth.put(url, data=data)
        elif method is 'DELETE':
            response = self.oauth.delete(url)
        else:
            raise APIError("Unknown request method: %s" % (method,))

        # check for error responses
        if response.status_code >= 400:
            raise APIError(response.status_code,
                           '',
                           "Error accessing API (url: %s, method: %s)\nData: %s\nMessage: %s" % (url, method, data, response.text))

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
        resp = self.api_request('/version')
        return resp['API version']

    def get_annotation_context(self):
        """ Retrieve the JSON-LD annotation context from the server

        :rtype: Dict
        :returns: the annotation context

        :raises: APIError if the API request is not successful


        """
        return self.api_request('/schema/json-ld')

    def get_collections(self):
        """Retrieve a list of the collection URLs for all collections
        hosted on the server.

        :rtype: List
        :returns: a List of tuples of (name, url) for each collection
        """
        result = self.api_request('/catalog')

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
        return self.api_request('/item_lists.json')

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
                if key not in ann.keys():
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

        response = self.api_request('/catalog', method='POST', data=json.dumps(payload))

        return self.__check_success(response)

    def modify_collection_metadata(self, collection_uri, metadata, replace=None, name=''):
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

        if replace is not None:
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

    def add_item(self, collection_uri, name, metadata):
        """Add a new item to a collection

        :param collection_uri: The URI that references the collection
        :type collection_uri: String

        :param name: The item name, suitable for use in a URI (no spaces)
        :type name: String

        :param metadata: a dictionary of metadata values describing the item
        :type metadata: Dict

        :rtype String
        :returns: the URI of the created item

        :raises: APIError if the request was not successful

        """

        metadata['dcterms:identifier'] = name
        metadata['dc:identifier'] = name  # for backward compatability in Alveo SOLR store until bug fix
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
        :param resp: the response string

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
        download_url = '/catalog/download_items'
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
        query_url = ('/catalog/search?' +
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
        resp = self.api_request('/item_lists')
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
        request_url = '/item_lists?' + url_name

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


    def get_speakers(self, collection_name):
        """Get a list of speaker URLs for this collection

        :type collection_name: String
        :param collection_name: the name of the collection to search

        :rtype: List
        :returns: a list of URLs for the speakers associated with
            the given collection

        """

        speakers_url = "/speakers/"+collection_name
        resp = self.api_request(speakers_url)
        if 'speakers' in resp:
            return resp['speakers']
        else:
            return []

    def get_speaker(self, speaker_url):
        """Given a speaker URL, return a dictionary containing
        the speaker metadata.

        :type speaker_url: String
        :param speaker_url: the URL identifier of the speaker

        :rtype: Dict
        :returns: a dictionary containing the metadata fields describing
            this speaker
        """

        return self.api_request(speaker_url)

    def add_speaker(self, collection_name, metadata):
        """Add a new speaker to this collection.

        :type collection_name: String
        :param collection_name: the name of the collection to search
        :type metadata: Dict
        :param metadata: dictionary of metadata properties and values
          for this speaker. Must include 'dcterms:identifier' a unique
          identifier for the speaker.

        :rtype: String
        :returns: the URL of the newly created speaker, or None if there was an
            error
        """

        if 'dcterms:identifier' not in metadata:
            raise APIError(msg="No identifier in speaker metadata")

        if '@context' not in metadata:
            metadata['@context'] = CONTEXT

        speakers_url = "/speakers/"+collection_name+"/"
        resp = self.api_request(speakers_url, data=json.dumps(metadata), method="POST")

        if 'success' in resp:
            return resp['success']['URI']
        else:
            return None

    def delete_speaker(self, speaker_uri):
        """Delete an speaker from a collection

        :param speaker_uri: the URI that references the speaker
        :type speaker_uri: String

        :rtype: Boolean
        :returns: True if the speaker was deleted

        :raises: APIError if the request was not successful
        """

        response = self.api_request(speaker_uri, method='DELETE')
        return self.__check_success(response)

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
        request_url = '/sparql/' + collection_name + '?'
        request_url += urlencode((('query', query),))

        return self.api_request(request_url)
