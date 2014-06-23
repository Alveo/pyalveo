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
			    "Could not find file ~/alveo.config. Please download your configuration file from http://hcsvlab.org.au/ OR try to create a client by specifying your api key",
			    str(cm.exception)
			)

		# Test with correct api key
		"""
		print "Enter your api key: "
		my_api_key = raw_input()
		client = hcsvlab.Client(api_key=my_api_key, api_url="https://ic2-hcsvlab-staging1-vm.intersect.org.au/", cache="cache.db", use_cache=True, update_cache=True)
		self.assertEqual(type(client), hcsvlab.Client)

		self.assertTrue(os.path.exists(cache_db_path))
		
		"""

		# Test with wrong api key
		with self.assertRaises(hcsvlab.APIError) as cm:
				client = hcsvlab.Client(api_key="wrongapikey123", api_url="https://ic2-hcsvlab-staging1-vm.intersect.org.au/", cache="cache.db", use_cache=True, update_cache=True)
			
		self.assertEqual(
		    "HTTP 401\nUnauthorized\nClient could not be created. Check your api key",
		    str(cm.exception)
		)		
	

	def identical_clients(self):
		first_client = hcsvlab.Client()
		second_client = hcsvlab.Client()

		self.assertTrue(first_client.__eq__(second_client))
		self.assertTrue(second_client.__eq__(first_client))
		
		print "Enter your api key: "
		my_api_key = raw_input()
		first_client = hcsvlab.Client(api_key=my_api_key, api_url="https://ic2-hcsvlab-staging1-vm.intersect.org.au/", cache="cache.db", use_cache=True, update_cache=True)
		second_client = hcsvlab.Client(api_key=my_api_key, api_url="https://ic2-hcsvlab-staging1-vm.intersect.org.au/", cache="cache.db", use_cache=True, update_cache=True)

		# Two clients created with same api key and same arguments must be same
		self.assertTrue(first_client.__eq__(second_client))		
		self.assertTrue(second_client.__eq__(first_client))

		# Two clients with same api key but diffent database configuration must be different
		third_client = hcsvlab.Client(api_key=my_api_key, api_url="https://ic2-hcsvlab-staging1-vm.intersect.org.au/", cache="cache.db", use_cache=False, update_cache=False)
		self.assertTrue(first_client.__ne__(third_client))
		self.assertTrue(second_client.__ne__(third_client))
		
		# Client without any arguments should be equal to client with all the default arguments
		first_client = hcsvlab.Client()
		second_client = first_client = hcsvlab.Client(api_key=my_api_key, api_url="https://ic2-hcsvlab-staging1-vm.intersect.org.au/", cache="cache.db", use_cache=True, update_cache=True)
		self.assertTrue(first_client.__eq__(second_client))


	def test_item_lists(self):
		client = hcsvlab.Client()
		new_item_url = ['https://ic2-hcsvlab-staging1-vm.intersect.org.au/catalog/ace/A01a']
		my_list = client.get_item_list_by_name('my new list')
		# Make sure to clear the item list from the web before running this
		# ToDO : clear the item list from api
		self.assertEqual(client.add_to_item_list_by_name(new_item_url, 'my new list'), '1 items added to existing item list my new list')






if __name__ == "__main__" :
	unittest.main(verbosity=5)

