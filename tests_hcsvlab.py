import unittest
import hcsvlab
import os

class Test(unittest.TestCase):
	
	def test_create_client(self):
		alveo_config_path = os.path.join(os.path.expanduser('~'), 'alveo.config')
		cache_db_path = os.path.join(os.path.expanduser('~'), 'alveo_cache', 'cache.db')
		
		# Test when alveo.config is present
		if os.path.exists(alveo_config_path):
			client = hcsvlab.Client()
			self.assertEqual(type(client), hcsvlab.Client)	
			self.assertTrue(os.path.exists(cache_db_path))

		else:
			# Teset when alveo.config is absent
			with self.assertRaises(IOError) as cm:
				client = hcsvlab.Client()
			
			self.assertEqual(
			    "Could not find file ~/alveo.config. Please download your configuration file from http://hcsvlab.org.au/",
			    str(cm.exception)
			)

		# Test with correct api key
		print "Enter your api key: "
		my_api_key = raw_input()
		client = hcsvlab.Client(api_key=my_api_key, api_url="https://ic2-hcsvlab-staging1-vm.intersect.org.au/", cache="cache.db", use_cache=True, update_cache=True)
		self.assertEqual(type(client), hcsvlab.Client)

		self.assertTrue(os.path.exists(cache_db_path))
		
		# Test with wrong api key
		with self.assertRaises(hcsvlab.APIError) as cm:
				client = hcsvlab.Client(api_key="wrongapikey123", api_url="https://ic2-hcsvlab-staging1-vm.intersect.org.au/", cache="cache.db", use_cache=True, update_cache=True)
			
		self.assertEqual(
		    "HTTP 401\nUnauthorized\nClient could not be created. Check your api key",
		    str(cm.exception)
		)		
		
	



		




if __name__ == "__main__" :
	unittest.main(verbosity=5)

