import unittest
import pyalveo
import os
import sqlite3

class Test(unittest.TestCase):
    
    def test_create_client(self):
        """ Test that the clients can be created with or without alveo.config file 
        and correct database is created """

        alveo_config_path = os.path.join(os.path.expanduser('~'), 'alveo.config')
        cache_db_path = os.path.join(os.path.expanduser('~'), 'alveo_cache', 'cache.db')
        
        # Test when alveo.config is present
        if os.path.exists(alveo_config_path):
            client = pyalveo.Client()
            self.assertEqual(type(client), pyalveo.Client)  
            self.assertTrue(os.path.exists(cache_db_path))

            # Test all the tables in the dtabase
            conn = sqlite3.connect(cache_db_path)
            cursor = conn.cursor()
            sql = "SELECT * from sqlite_master WHERE type = 'table'"
            cursor.execute(sql)
            result = cursor.fetchall()
            
            self.assertEqual(4, len(result), "there should be 4 tables in the database")
            self.assertEqual(result[0][1], 'items', "first table should be items")
            self.assertEqual(result[1][1], 'documents', "second table should be documents")
            self.assertEqual(result[2][1], 'primary_texts', "third table should be primary_texts")
            self.assertEqual(result[3][1], 'meta', "fourth table should be meta")
            conn.close()

        else:
            # Teset when alveo.config is absent
            with self.assertRaises(IOError) as cm:
                client = pyalveo.Client()
            
            self.assertEqual(
                "Could not find file ~/alveo.config. Please download your configuration file from http://pyalveo.org.au/ OR try to create a client by specifying your api key",
                str(cm.exception)
            )

        # Test with correct api key
        
        client = pyalveo.Client(cache="cache.db", use_cache=True, update_cache=True)
        self.assertEqual(type(client), pyalveo.Client)

        self.assertTrue(os.path.exists(cache_db_path))
        
    

        # Test with wrong api key
        with self.assertRaises(pyalveo.APIError) as cm:
                client = pyalveo.Client(api_key="wrongapikey123", cache="cache.db", use_cache=True, update_cache=True)
            
        self.assertEqual(
            "HTTP 401\nUnauthorized\nClient could not be created. Check your api key",
            str(cm.exception)
        )       
    

    def test_identical_clients(self):
        """ Test that multiple clients can be created with default configuration or specific configuration
        and check if they are identical or not """

        first_client = pyalveo.Client()
        second_client = pyalveo.Client()

        self.assertTrue(first_client.__eq__(second_client))
        self.assertTrue(second_client.__eq__(first_client))
        

        first_client = pyalveo.Client(cache="cache.db", use_cache=True, update_cache=True)
        second_client = pyalveo.Client(cache="cache.db", use_cache=True, update_cache=True)

        # Two clients created with same api key and same arguments must be same
        self.assertTrue(first_client.__eq__(second_client))     
        self.assertTrue(second_client.__eq__(first_client))

        # Two clients with same api key but diffent database configuration must be different
        third_client = pyalveo.Client(cache="cache.db", use_cache=False, update_cache=False)
        self.assertTrue(first_client.__ne__(third_client))
        self.assertTrue(second_client.__ne__(third_client))
        
        # Client without any arguments should be equal to client with all the default arguments
        first_client = pyalveo.Client()
        second_client = first_client = pyalveo.Client(cache="cache.db", use_cache=True, update_cache=True)
        self.assertTrue(first_client.__eq__(second_client))


    def test_item_download(self):
        """Test access to individual items"""
        client = pyalveo.Client()
        item_url = client.api_url + 'catalog/ace/A01a'
        item  = client.get_item(item_url)

        self.assertEqual(item_url, item.url())

        meta = item.metadata()
            
        self.assertEqual(meta['alveo:primary_text_url'], client.api_url + u'catalog/ace/A01a/primary_text.json')


    def test_item_lists(self):
        """ Test that the item list can be created, item can be added to the item list, 
        item list can be renamed and deleted """

        client = pyalveo.Client()
        base_url = client.api_url
        new_item_url_1 = [base_url + 'catalog/ace/A01a']
        self.assertEqual(client.add_to_item_list_by_name(new_item_url_1, 'my_list'), '1 items added to new item list my_list')

        my_list = client.get_item_list_by_name('my_list')
        self.assertEqual(my_list.name(), 'my_list')
        
        new_item_url_2 = [base_url + 'catalog/ace/A01b']
        self.assertEqual(client.add_to_item_list(new_item_url_2, my_list.url()), '1 items added to existing item list ' + my_list.name())

        
        my_list = my_list.refresh()
        item = client.get_item(new_item_url_2[0])
        self.assertTrue(item in my_list)

        # Test Rename List
        client.rename_item_list(my_list, 'brand new list')
        my_list = my_list.refresh()
        self.assertEqual(my_list.name(), 'brand new list')

        # Deleting an Item List
        self.assertEqual(client.delete_item_list(my_list), None)







if __name__ == "__main__" :
    unittest.main(verbosity=5)

