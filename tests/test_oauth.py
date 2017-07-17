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
class OAuthTest(unittest.TestCase):

    def test_create_client_oauth(self, m):
        """Create a client using OAuth credentials"""

        redirect_url = API_URL+'/oauth_redirect/'
        oauth_url = API_URL+'/oauth/authorize'

        m.get(redirect_url, json={})

        oauth_info = {
            'client_id': 'foobar',
            'client_secret': 'secret client',
            'redirect_url': redirect_url,
        }
        client = pyalveo.Client(api_url=API_URL,
                                oauth=oauth_info,
                                configfile="missing.config",
                                verifySSL=False)

        # we can't capture the request that OAuth makes but we can
        # check the settings that result from it
        self.assertTrue(client.oauth.auth_url.startswith(oauth_url))
        self.assertEqual(client.oauth.redirect_url, redirect_url)

        # now try the callback method, need to manufacture a response to
        # pass in
        #resp = None
        #result = client.oauth.on_callback(resp)
        #self.assertTrue(result)

if __name__ == "__main__" :
    unittest.main(verbosity=5)
