import unittest
import pyalveo
import os
import shutil
import requests_mock
import json
import tempfile

API_URL = "https://app.alveo.edu.au"
API_KEY = "fakekeyvalue"


@requests_mock.Mocker()
class ClientTest(unittest.TestCase):

    def test_create_client(self, m):
        """ Test that the clients can be created with or without alveo.config file
        and correct database is created """

        m.get(API_URL + "/item_lists.json",
              json={'failure': 'Client could not be created. Check your api key'},
              status_code=401)
        # Test with wrong api key
        with self.assertRaises(pyalveo.APIError) as cm:
            client = pyalveo.Client(api_url=API_URL, api_key=API_KEY)
            client.get_item_lists()

        self.assertTrue(
            "Client could not be created. Check your api key" in str(cm.exception)
        )

        m.get(API_URL + "/item_lists.json",json={'success': 'yes'})
        alveo_config_path = os.path.expanduser('~/alveo.config')
        cache_db_path = 'tmp'

        if False:
            # how to mock these?
            # Test when alveo.config is present
            if os.path.exists(alveo_config_path):
                client = pyalveo.Client()
                self.assertEqual(type(client), pyalveo.Client)

            else:
                # Test when alveo.config is absent
                with self.assertRaises(IOError) as cm:
                    client = pyalveo.Client()

                self.assertEqual(
                    "Could not find file ~/alveo.config. Please download your configuration file from http://pyalveo.org.au/ OR try to create a client by specifying your api key",
                    str(cm.exception)
                )

            # Test with correct api key
            client = pyalveo.Client()
            self.assertEqual(type(client), pyalveo.Client)


    def test_to_from_json(self,m):
        """ Test packing the oath object into a json form then reloading it. """

        api_url = 'https://example.org'
        api_key = 'thisisrandomtext'
        verifySSL = False
        cache_dir = 'tmp'
        oauth_dict = {
                      'client_id':'morerandomtext',
                      'client_secret':'secretrandomtext',
                      'redirect_url':'https://anotherfake.com'
                      }
        expected_json = '{"use_cache": false, "api_url": "https://example.org", "cache": {"max_age": 0, "cache_dir": "tmp"}, "cache_dir": "tmp", "update_cache": true, "oauth": {"client_id": "morerandomtext", "state": "cgLXfsICCMsuTeY6HWkzsqMPyxTA8K", "token": null, "auth_url": "https://example.org/oauth/authorize?response_type=code&client_id=morerandomtext&redirect_uri=https%3A%2F%2Fanotherfake.com&state=cgLXfsICCMsuTeY6HWkzsqMPyxTA8K", "redirect_url": "https://anotherfake.com", "client_secret": "secretrandomtext", "api_key": "secretkey", "verifySSL": false, "api_url": "https://example.org"}, "api_key": "secretkey"}'
        client = pyalveo.Client(api_url=api_url,oauth=oauth_dict,verifySSL=verifySSL,use_cache=False,cache_dir=cache_dir, configfile="tests/alveo.config")
        json_string = client.to_json()
        #Test json comes out as expected
        #A state will be generated which should be different always
        #So we need to load the json into a dict, remove the state key then check equality
        json_dict = json.loads(json_string)
        expected_dict = json.loads(expected_json)
        json_dict['oauth'].pop('state',None)
        expected_dict['oauth'].pop('state',None)
        #Do the same with auth url as it's a string that contains the state
        json_dict['oauth'].pop('auth_url',None)
        expected_dict['oauth'].pop('auth_url',None)
        #Do the same with cache dir as that also can't be predicted
        json_dict['cache'].pop('cache_dir',None)
        expected_dict['cache'].pop('cache_dir',None)
        json_dict.pop('cache_dir',None)
        expected_dict.pop('cache_dir',None)

        self.assertEqual(json_dict, expected_dict)

        client2 = pyalveo.Client.from_json(json_string)

        #Test generated json creates an identical object
        #These should have identical states however
        self.assertEqual(client, client2)

        starting_json = '{"use_cache": true, "api_url": "https://example.org", "cache": {"max_age": 0, "cache_dir": "tmp"}, "cache_dir": "tmp", "update_cache": true, "oauth": {"client_id": null, "state": null, "token": null, "auth_url": null, "redirect_url": null, "client_secret": null, "api_key": "thisisrandomtext", "verifySSL": false, "api_url": "https://example.org"}, "api_key": "thisisrandomtext"}'

        client = pyalveo.Client(api_url=api_url,api_key=api_key,verifySSL=verifySSL,use_cache=True,cache_dir=cache_dir)

        client2 = pyalveo.Client.from_json(starting_json)

        #test manually created json creates an identical cache to one properly setup
        self.assertEqual(client, client2)

    def test_client_context(self, m):
        """add_context extends the context that is used by the  client"""

        m.get(API_URL + "/item_lists.json",json={'success': 'yes'})
        client = pyalveo.Client(api_url=API_URL, api_key=API_KEY)

        client.add_context('test', 'http://test.org/')

        self.assertIn('test', client.context)
        self.assertEqual('http://test.org/', client.context['test'])


    def test_client_cache(self, m):
        """Test that we can create a client with a cache enabled and that it caches things"""

        cache_dir = "tmp"


        m.get(API_URL + "/item_lists.json",json={'success': 'yes'})
        client = pyalveo.Client(api_url=API_URL, api_key=API_KEY, use_cache=True, cache_dir=cache_dir)

        item_url = client.oauth.api_url + "/catalog/cooee/1-190"
        item_meta = ""

        self.addCleanup(shutil.rmtree, cache_dir, True)

        self.assertEqual(type(client.cache), pyalveo.Cache)


        with open('tests/responses/1-190.json', 'rb') as rh:
            m.get(item_url, body=rh)
            item = client.get_item(item_url)

        self.assertEqual(type(item), pyalveo.Item)

        # look in the cache for this item metadata

        self.assertTrue(client.cache.has_item(item_url))

        meta = client.cache.get_item(item_url)

        # check a few things about the metadata json
        self.assertIn("@context", meta.decode('utf-8'))
        self.assertIn(item_url, meta.decode('utf-8'))


        # get a document
        with open('tests/responses/1-190-plain.txt', 'rb') as rh:
            m.get(item_url + "/document/1-190-plain.txt", body=rh)
            doc = item.get_document(0)

            self.assertEqual(type(doc), pyalveo.Document)

            doc_content = doc.get_content()
            self.assertEqual(doc_content[:20].decode(), "Sydney, New South Wa")

        # there should be a cached file somewhere under cache_dir
        ldir = os.listdir(os.path.join(cache_dir, "files"))
        self.assertEqual(1, len(ldir))
        # the content of the file should be the same as our doc_content
        with open(os.path.join(cache_dir, "files", ldir[0]), 'rb') as h:
            self.assertEqual(h.read(), doc_content)

        # now trigger a cache hit
        doc_content_cache = doc.get_content()
        self.assertEqual(doc_content, doc_content_cache)



    def test_client_no_cache(self, m):
        """Test that we can create and use a client without a cache enabled"""

        m.get(API_URL + "/item_lists.json",json={'success': 'yes'})
        client = pyalveo.Client(api_url=API_URL, api_key=API_KEY, use_cache=False)

        item_url = client.oauth.api_url + "/catalog/cooee/1-190"
        item_meta = ""

        with open('tests/responses/1-190.json', 'rb') as rh:
            m.get(item_url, body=rh)
            item = client.get_item(item_url)

        self.assertEqual(type(item), pyalveo.Item)

        # get a document
        with open('tests/responses/1-190-plain.txt', 'rb') as rh:
            m.get(item_url + "/document/1-190-plain.txt", body=rh)
            doc = item.get_document(0)

            self.assertEqual(type(doc), pyalveo.Document)

            doc_content = doc.get_content()
            self.assertEqual(doc_content[:20].decode(), "Sydney, New South Wa")


    def test_identical_clients(self, m):
        """ Test that multiple clients can be created with default configuration or specific configuration
        and check if they are identical or not """

        m.get(API_URL + "/item_lists.json",json={'success': 'yes'})
        first_client = pyalveo.Client(api_url=API_URL, api_key=API_KEY, use_cache=False)
        second_client = pyalveo.Client(api_url=API_URL, api_key=API_KEY, use_cache=False)

        self.assertTrue(first_client.__eq__(second_client))
        self.assertTrue(second_client.__eq__(first_client))


        first_client = pyalveo.Client(api_url=API_URL, api_key=API_KEY, cache="cache.db", use_cache=True, update_cache=True)
        second_client = pyalveo.Client(api_url=API_URL, api_key=API_KEY, cache="cache.db", use_cache=True, update_cache=True)

        # Two clients created with same api key and same arguments must be same
        self.assertTrue(first_client.__eq__(second_client))
        self.assertTrue(second_client.__eq__(first_client))

        # Two clients with same api key but diffent database configuration must be different
        third_client = pyalveo.Client(api_url=API_URL, api_key=API_KEY, cache="cache.db", use_cache=False, update_cache=False)
        self.assertTrue(first_client.__ne__(third_client))
        self.assertTrue(second_client.__ne__(third_client))

        # Client without any arguments should be equal to client with all the default arguments
        first_client = pyalveo.Client(api_url=API_URL, api_key=API_KEY, use_cache=False)
        second_client = first_client = pyalveo.Client(api_url=API_URL, api_key=API_KEY, cache="cache.db", use_cache=True, update_cache=True)
        self.assertTrue(first_client.__eq__(second_client))


    def test_item_download(self, m):
        """Test access to individual items"""

        m.get(API_URL + "/item_lists.json",json={'success': 'yes'})
        client = pyalveo.Client(api_url=API_URL, api_key=API_KEY, use_cache=True)
        item_url = client.oauth.api_url + '/catalog/cooee/1-190'

        with open('tests/responses/1-190.json', 'rb') as rh:
            m.get(item_url, body=rh)
            item = client.get_item(item_url)

        self.assertEqual(item_url, item.url())

        meta = item.metadata()

        self.assertEqual(meta['alveo:primary_text_url'], client.oauth.api_url + u'/catalog/cooee/1-190/primary_text.json')

        # now try it with the cache, should not make a request
        item2 = client.get_item(item_url)
        self.assertEqual(item_url, item2.url())
        self.assertEqual(item.metadata(), item2.metadata())


    def test_download_document(self, m):
        """Download a document"""

        m.get(API_URL + "/item_lists.json",json={'success': 'yes'})
        client = pyalveo.Client(api_url=API_URL, api_key=API_KEY, use_cache=False)

        # temp directory for output
        output_dir = tempfile.mkdtemp()
        outname = "downloaded_sample.wav"

        document_url = client.oauth.api_url + '/catalog/cooee/1-190/document/sample.wav'

        meta = {'alveo:url': document_url}
        document = pyalveo.Document(meta, client)

        with open('tests/responses/sample.wav', 'rb') as rh:
            m.get(document_url, body=rh)
            document.download_content(output_dir, outname, force_download=True)

        self.assertTrue(os.path.exists(os.path.join(output_dir, outname)))

    def test_item_lists(self, m):
        """ Test that the item list can be created, item can be added to the item list,
        item list can be renamed and deleted """

        m.get(API_URL + "/item_lists.json",json={'success': 'yes'})
        client = pyalveo.Client(api_url=API_URL, api_key=API_KEY, use_cache=False)
        base_url = client.oauth.api_url
        item_list_name = 'pyalveo_test_item_list'

        msg = '1 items added to new item list ' + item_list_name
        m.post(API_URL + '/item_lists',json={'success': msg})
        new_item_url_1 = [base_url + '/catalog/ace/A01a']
        self.assertEqual(client.add_to_item_list_by_name(new_item_url_1, item_list_name), msg)

        with open('tests/responses/item-lists.json', 'rb') as fd:
            m.get(API_URL + '/item_lists', content=fd.read())

        with open('tests/responses/item-list-831.json') as fd:
            ilist_831 = json.loads(fd.read())

        m.get(API_URL + '/item_lists/831', json=ilist_831)
        my_list = client.get_item_list_by_name(item_list_name)
        self.assertEqual(my_list.name(), item_list_name)

        msg = '1 items added to existing item list ' + item_list_name
        m.post(API_URL + '/item_lists',json={'success': msg})
        new_item_url_2 = [base_url + 'catalog/ace/A01b']
        self.assertEqual(client.add_to_item_list(new_item_url_2, my_list.url()), '1 items added to existing item list ' + my_list.name())

        # Test Rename List
        ilist_831['name'] = 'brand new list'
        m.put(API_URL + '/item_lists/831', json=ilist_831)
        client.rename_item_list(my_list, 'brand new list')

        # Deleting an Item List
        m.delete(API_URL + '/item_lists/831', json={'success': 'item list deleted'})
        self.assertEqual(client.delete_item_list(my_list), True)

        # deleting an Item List that isn't there raises an exception
        m.delete(API_URL + '/item_lists/831', status_code=404)
        self.assertRaises(pyalveo.APIError, client.delete_item_list, my_list)

    def test_get_annotations(self, m):

        m.get(API_URL + "/item_lists.json",json={'success': 'yes'})
        client = pyalveo.Client(api_url=API_URL, api_key=API_KEY, use_cache=False)

        item_url = client.oauth.api_url + "/catalog/ace/A01b"
        with open('tests/responses/A01b.json', 'rb') as fd:
            m.get(item_url, content=fd.read())
        item = client.get_item(item_url)

        # get annotations for this item of type 'speaker'
        ann_url = item_url + '/annotations.json'
        with open('tests/responses/A01b-annotations.json', 'rb') as fd:
            m.get(ann_url, content=fd.read())
        anns = item.get_annotations(atype=u'http://ns.ausnc.org.au/schemas/annotation/ice/speaker')
        self.assertListEqual(sorted(anns.keys()), [u'@context', u'alveo:annotations', u'commonProperties'])

        ann = anns['alveo:annotations'][0]
        self.assertEqual(sorted(ann.keys()), [u'@id', u'@type',  u'end',  u'start', u'type'])

    def test_sparql_query(self, m):
        """Can we run a simple SPARQL query"""

        m.get(API_URL + "/item_lists.json",json={'success': 'yes'})
        client = pyalveo.Client(api_url=API_URL, api_key=API_KEY, use_cache=False)

        query = """select * where { ?a ?b ?c } LIMIT 10"""

        m.get(API_URL + "/sparql/mitcheldelbridge", json={'results': {'bindings': [1,2,3,4,5,6,7,8,9,0]}})
        result = client.sparql_query('mitcheldelbridge', query)

        self.assertIn('results', result)
        self.assertIn('bindings', result['results'])
        self.assertEqual(len(result['results']['bindings']), 10)




if __name__ == "__main__" :
    unittest.main(verbosity=5)
