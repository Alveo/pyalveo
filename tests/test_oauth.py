import unittest
import pyalveo
from pyalveo.pyalveo import OAuth2
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

    def test_to_from_json(self,m):
        """ Test packing the oath object into a json form then reloading it. """
        
        api_url = 'https://fake.com'
        api_key = 'thisisrandomtext'
        verifySSL = False
        oauth_dict = {
                      'client_id':'morerandomtext',
                      'client_secret':'secretrandomtext',
                      'redirect_url':'https://anotherfake.com'
                      }
        expected_json = '{"client_id": "morerandomtext", "state": "Yg4HRoIwCGspnYRQY65jCoPlbIHaiy", "token": null, "auth_url": "https://fake.com/oauth/authorize?response_type=code&client_id=morerandomtext&redirect_uri=https%3A%2F%2Fanotherfake.com&state=Yg4HRoIwCGspnYRQY65jCoPlbIHaiy", "redirect_url": "https://anotherfake.com", "client_secret": "secretrandomtext", "api_key": null, "verifySSL": false, "api_url": "https://fake.com"}'
        oauth = OAuth2(api_url,oauth=oauth_dict,verifySSL=verifySSL)
        json_string = oauth.to_json()
        
        #Test json comes out as expected
        #A state will be generated which should be different always
        #So we need to load the json into a dict, remove the state key then check equality
        json_dict = json.loads(json_string)
        expected_dict = json.loads(expected_json)
        json_dict.pop('state',None)
        expected_dict.pop('state',None)
        #Do the same with auth url as it's a string that contains the state
        json_dict.pop('auth_url',None)
        expected_dict.pop('auth_url',None)
        self.assertEqual(json_dict, expected_dict)
        
        oauth2 = OAuth2.from_json(json_string)
        
        #Test generated json creates an identical object
        #These should have identical states however
        self.assertEqual(oauth, oauth2)
        
        starting_json = '{"client_id": null, "state": null, "token": null, "auth_url": null, "redirect_url": null, "client_secret": null, "api_key": "thisisrandomtext", "verifySSL": false, "api_url": "https://fake.com"}'
        
        oauth = OAuth2(api_url,api_key=api_key,verifySSL=verifySSL)
        
        oauth2 = OAuth2.from_json(starting_json)
        
        #test manually created json creates an identical cache to one properly setup
        self.assertEqual(oauth, oauth2)

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
