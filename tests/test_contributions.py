import unittest
import pyalveo
import requests_mock
import json

CONTEXT = { "ausnc": "http://ns.ausnc.org.au/schemas/ausnc_md_model/",
            "corpus": "http://ns.ausnc.org.au/corpora/",
            "dc": "http://purl.org/dc/terms/",
            "dcterms": "http://purl.org/dc/terms/",
            "foaf": "http://xmlns.com/foaf/0.1/",
            "hcsvlab": "http://hcsvlab.org/vocabulary/"
         }

API_URL = "http://example.alveo.froob"
API_KEY = "fakekeyvalue"


@requests_mock.Mocker()
class ContributionsTest(unittest.TestCase):

    def test_create_contribution(self, m):
        """Test that we can create a new contribution"""

        m.get(API_URL + "/item_lists.json",json={'success': 'yes'})
        client = pyalveo.Client(api_url=API_URL, api_key=API_KEY)

        cname = 'testcontrib'

        m.post(client.oauth.api_url + "/contrib/",
               json={'description': 'This is contribution description',
                     'documents': [{'name': 'testfile.txt',
                                    'url': 'https://staging.alveo.edu.au/catalog/demotext/2006-05-28-19/document/testfile.txt'}],
                     'id': '29',
                     'metadata': {'abstract': '"This is contribution abstract"',
                                  'collection': 'https://staging.alveo.edu.au/catalog/demotext',
                                  'created': '2018-12-06T05:46:11Z',
                                  'creator': 'Data Owner',
                                  'title': 'HelloWorld'},
                     'name': 'HelloWorld',
                     'url': 'https://staging.alveo.edu.au/contrib/29'}
               )

        meta = {
            "contribution_name": "HelloWorld",
            "contribution_collection": "demotext",
            "contribution_text": "This is contribution description",
            "contribution_abstract": "This is contribution abstract"
        }

        result = client.create_contribution(meta)

        # validate the request we made
        req = m.last_request
        self.assertEqual(req.method, 'POST')
        # check that the right things were in the request
        self.assertIn('contribution_collection', req.json())
        self.assertIn('contribution_name', req.json())
        self.assertDictEqual(meta, req.json())

    def test_get_contribution(self, m):
        """Get details of a contribution"""

        m.get(API_URL + "/item_lists.json",json={'success': 'yes'})
        client = pyalveo.Client(api_url=API_URL, api_key=API_KEY)

        cname = '29'

        contrib_url = client.oauth.api_url + "/contrib/" + cname
        m.get(contrib_url,
               json={'description': 'This is contribution description',
                     'documents': [{'name': 'testfile.txt',
                                    'url': 'https://staging.alveo.edu.au/catalog/demotext/2006-05-28-19/document/testfile.txt'}],
                     'metadata': {'abstract': '"This is contribution abstract"',
                                  'collection': 'https://staging.alveo.edu.au/catalog/demotext',
                                  'created': '2018-12-06T05:46:11Z',
                                  'creator': 'Data Owner',
                                  'title': 'HelloWorld'},
                     'name': 'HelloWorld',
                     'url': contrib_url}
               )

        result = client.get_contribution(contrib_url)

        req = m.last_request
        self.assertEqual(req.method, "GET")
        self.assertEqual(result['id'], cname)
        self.assertEqual(result['description'], 'This is contribution description')






def test_add_document_to_contrib(self, m):
        """Test adding documents to a contribution"""

        m.get(API_URL + "/item_lists.json",json={'success': 'yes'})
        client = pyalveo.Client(api_url=API_URL, api_key=API_KEY)
        collection_name = "testcollection1"
        itemname = "item1"
        docname = "doc1.txt"
        content = "Hello World!\n"

        item_uri = API_URL + "/catalog/%s/%s" % (collection_name, itemname)

        m.post(item_uri, json={"success":"Added the document %s to item %s in collection %s" % (docname, itemname, collection_name)})

        docmeta = {
                   "dcterms:title": "Sample Document",
                   "dcterms:type": "Text"
                  }

        document_uri = client.add_document(item_uri, docname, docmeta, content=content, contrib_id=1)

        req = m.last_request
        payload = req.json()
        self.assertEqual(payload['document_content'], content)
        self.assertIn('metadata', payload)
        md = payload['metadata']
        self.assertIn('dcterms:title', md)
        self.assertEqual(md['dcterms:title'], docmeta['dcterms:title'])
        self.assertEqual(md['@type'], "foaf:Document")
        self.assertEqual(md['dcterms:identifier'], docname)
        # in addition to the above info for add_document we
        # should have the contribution id in the payload JSON
        self.assertIn('contribution_id', payload)


if __name__ == "__main__" :
    unittest.main(verbosity=5)
