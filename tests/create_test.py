import unittest
import pyalveo
import os
import uuid
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
class CreateTest(unittest.TestCase):

    def test_create_collection(self, m):
        """Test that we can create a new collection"""

        m.get(API_URL + "/item_lists.json",json={'success': 'yes'})
        client = pyalveo.Client(api_url=API_URL, api_key=API_KEY)

        cname = 'testcollection1'
        curl = client.api_url + "/catalog/" + cname

        m.post(client.api_url + "/catalog",
               json={"success":"New collection \'%s\' (%s) created" % (cname, curl)})

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
        req = m.last_request
        self.assertEqual(req.method, 'POST')
        self.assertIn('name', req.json())
        self.assertIn('collection_metadata', req.json())
        self.assertDictEqual(meta, req.json()['collection_metadata'])

        # TODO: test creating collection that already exists
        # TODO: test other error conditions - no name, no metadata, bad json

    def test_add_items(self, m):
        """Test that we can add new items to a collection"""

        m.get(API_URL + "/item_lists.json",json={'success': 'yes'})
        client = pyalveo.Client(api_url=API_URL, api_key=API_KEY)
        collection_name = "testcollection1"
        collection_uri = API_URL + "/catalog/" + collection_name
        itemname = str(uuid.uuid4())

        m.post(collection_uri, json={"success": itemname})

        meta = {
                'dc:title': 'Test Item',
                'dc:creator': 'A. Programmer'
                }

        item_uri = client.add_item(collection_uri, itemname, meta)

        self.assertIn(itemname, item_uri)
        req = m.last_request
        self.assertEqual(req.method, 'POST')
        self.assertEqual(req.headers['Content-Type'], 'application/json')
        self.assertEqual(req.headers['X-API-KEY'], API_KEY)
        self.assertIn('items', req.json())

        # add a document

        docname = "document2.txt"

        m.post(item_uri, json={"success":"Added the document %s to item %s in collection %s" % (docname, itemname, collection_name)})

        docmeta = {
                   "dcterms:title": "Sample Document",
                   "dcterms:type": "Text"
                  }

        document_uri = client.add_document(item_uri, docname, docmeta, content="Hello World!")

        req = m.last_request
        self.assertIn('document_content', req.json())
        self.assertIn('metadata', req.json())
        self.assertIn('dcterms:title', req.json()['metadata'])

        # delete the document
        m.delete(document_uri, json={"success":"Deleted the document %s from item %s in collection %s" % (docname, itemname, collection_name)})
        client.delete_document(document_uri)

        req = m.last_request
        self.assertEqual(req.method, 'DELETE')


        # now delete the item
        m.delete(item_uri, json={"success": itemname})
        client.delete_item(item_uri)

        req = m.last_request
        self.assertEqual(req.method, 'DELETE')





    def test_add_annotations(self, m):
        """Test that we can add new annotations for an item"""

        m.get(API_URL + "/item_lists.json",json={'success': 'yes'})
        client = pyalveo.Client(api_url=API_URL, api_key=API_KEY)

        # create an item
        m.post(collection_uri, json={"success": [itemname]})
        meta = {
                'dc:title': 'Test Item',
                'dc:creator': 'A. Programmer'
                }

        item_uri = client.add_item(collection_uri, itemname, meta)

        anns = [{
                    "@type": "dada:TextAnnotation",
                    "type": "pageno",
                    "label": "hello",
                    "start": 421,
                    "end": 425
                },
                {
                    "@type": "dada:TextAnnotation",
                    "type": "pageno",
                    "label": "world",
                    "start": 2524,
                    "end": 2529
                }
               ]

        # now add some annotations
        m.post(item_uri + "/annotations", json={'success': 'yes'})
        client.upload_annotation(item_uri, annotations)




if __name__ == "__main__" :
    unittest.main(verbosity=5)
