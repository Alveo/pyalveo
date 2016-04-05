import unittest
import pyalveo
import os
import uuid
import httpretty
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



class CreateTest(unittest.TestCase):

    def setUp(self):

        httpretty.enable()
        httpretty.HTTPretty.allow_net_connect = False
        # mock result for /item_lists.json is needed to create client
        httpretty.register_uri(httpretty.GET,
                               API_URL + "/item_lists.json",
                               body=json.dumps({'success': 'yes'}),
                               content_type='application/json'
                               )



    def test_create_collection(self):
        """Test that we can create a new collection"""

        client = pyalveo.Client(api_url=API_URL, api_key=API_KEY)

        cname = 'testcollection1'
        curl = client.api_url + "/catalog/" + cname

        httpretty.register_uri(httpretty.POST,
                               client.api_url + "/catalog",
                               body='{"success":"New collection \'%s\' (%s) created"}' % (cname, curl),
                               status=200,
                               content_type='application/json'
                               )

        meta = { "@context": CONTEXT,
                 "@type": "dcmitype:Collection",
                 "dc:creator": "Data Owner",
                 "dc:rights": "All rights reserved to Data Owner",
                 "dc:subject": "English Language",
                 "dc:title": "Test Collection" }

        result = client.create_collection('testcollection1', meta)

        self.assertIn("testcollection1", result)
        self.assertIn("created", result)

        # validate the request we made
        req = httpretty.last_request()
        self.assertEqual(req.method, 'POST')
        self.assertIn('name', req.parsed_body)
        self.assertIn('collection_metadata', req.parsed_body)
        self.assertDictEqual(meta, req.parsed_body['collection_metadata'])

        # TODO: test creating collection that already exists
        # TODO: test other error conditions - no name, no metadata, bad json

    def test_add_items(self):
        """Test that we can add new items to a collection"""

        client = pyalveo.Client(api_url=API_URL, api_key=API_KEY)
        collection_name = "testcollection1"
        collection_uri = API_URL + "catalog/" + collection_name
        itemname = str(uuid.uuid4())

        httpretty.register_uri(httpretty.POST,
                               collection_uri,
                               body='{"success": ["%s"]}' % (itemname,),
                               status=200,
                               content_type='application/json'
                               )

        meta = {
                'dc:title': 'Test Item',
                'dc:creator': 'A. Programmer'
                }

        item_uri = client.add_item(collection_uri, itemname, meta)

        self.assertIn(itemname, item_uri)
        req = httpretty.last_request()
        self.assertEqual(req.method, 'POST')
        self.assertEqual(req.headers['Content-Type'], 'application/json')
        self.assertEqual(req.headers['X-API-KEY'], API_KEY)
        self.assertIn('items', req.parsed_body)

        # now delete it
        httpretty.register_uri(httpretty.DELETE,
                               item_uri,
                               body='{"success": ["%s"]}' % (itemname,),
                               status=200,
                               content_type='application/json'
                               )

        client.delete_item(item_uri)

        # add a document

        docname = "document2.txt"

        httpretty.register_uri(httpretty.POST,
                               item_uri,
                               body='{"success":"Added the document %s to item %s in collection %s"}' % (docname, itemname, collection_name),
                               status=200,
                               content_type='application/json'
                               )

        docmeta = {
                   "dcterms:title": "Sample Document",
                   "dcterms:type": "Text"
                  }

        document_uri = client.add_document(item_uri, docname, docmeta, content="Hello World!")

        req = httpretty.last_request()
        self.assertIn('document_content', req.parsed_body)
        self.assertIn('metadata', req.parsed_body)
        self.assertIn('dcterms:title', req.parsed_body['metadata'])

        # delete the document
        httpretty.register_uri(httpretty.DELETE,
                               document_uri,
                               body='{"success":"Deleted the document %s from item %s in collection %s"}' % (docname, itemname, collection_name),
                               status=200,
                               content_type='application/json'
                               )

        client.delete_item(document_uri)


if __name__ == "__main__" :
    unittest.main(verbosity=5)
