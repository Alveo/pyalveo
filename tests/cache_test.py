import unittest
import pyalveo
import os
import sqlite3
import shutil

class CacheTest(unittest.TestCase):

    def test_create_cache(self):
        """ Test that we can make a chache and all the right things happen"""

        file_dir = 'tmp'
        cache_db_path = os.path.join(file_dir, 'alveo_cache.db')

        self.addCleanup(shutil.rmtree, file_dir, True)

        cache = pyalveo.Cache(file_dir)
        self.assertEqual(type(cache), pyalveo.Cache)
        self.assertTrue(os.path.exists(cache_db_path))

        # Test all the tables in the database
        conn = sqlite3.connect(cache_db_path)
        cursor = conn.cursor()
        sql = "SELECT * from sqlite_master WHERE type = 'table'"
        cursor.execute(sql)
        result = cursor.fetchall()

        self.assertEqual(3, len(result), "there should be 4 tables in the database")
        self.assertEqual(result[0][1], 'items', "first table should be items")
        self.assertEqual(result[1][1], 'documents', "second table should be documents")
        self.assertEqual(result[2][1], 'primary_texts', "third table should be primary_texts")
        conn.close()

    def test_add_item(self):
        """Test adding an item to the cache and retrieving it"""

        item_url = 'http://foo.org/one/two/three.jpg'
        item_meta = "{'one': 'two'}"

        file_dir = 'tmp'
        cache_db_path = os.path.join(file_dir, 'alveo_cache.db')
        self.addCleanup(shutil.rmtree, file_dir, True)

        cache = pyalveo.Cache(file_dir)

        cache.add_item(item_url, item_meta)

        self.assertTrue(cache.has_item(item_url))
        self.assertEqual(item_meta, cache.get_item(item_url))

    def test_to_from_json(self):
        """ Test packing the cache into a json form then reloading it. """
        
        file_dir = 'tmp'
        expected_json = '{"max_age": 0, "cache_dir": "tmp"}'
        cache = pyalveo.Cache(file_dir)
        
        json_string = cache.to_json()
        
        #Test json comes out as expected
        self.assertEqual(json_string, expected_json)
        
        cache2 = pyalveo.Cache.from_json(json_string)
        
        #Test generated json creates an identical object
        self.assertEqual(cache, cache2)
        
        starting_json = '{"max_age": 500, "cache_dir": "tmp"}'
        
        cache = pyalveo.Cache(file_dir,max_age=500)
        
        cache2 = pyalveo.Cache.from_json(starting_json)
        
        #test manually created json creates an identical cache to one properly setup
        self.assertEqual(cache, cache2)
        

    def test_add_primary_text(self):
        """Test adding a primary text to the cache and retrieving it"""

        item_url = 'http://foo.org/one/two/three.jpg'
        item_text = "one two buckly my shoe"

        file_dir = 'tmp'
        cache_db_path = os.path.join(file_dir, 'alveo_cache.db')
        self.addCleanup(shutil.rmtree, file_dir, True)

        cache = pyalveo.Cache(file_dir)

        cache.add_primary_text(item_url, item_text)

        self.assertTrue(cache.has_primary_text(item_url))
        self.assertEqual(item_text, cache.get_primary_text(item_url))


    def test_add_document(self):
        """Test adding a document to the cache and retrieving it"""

        item_url = 'http://foo.org/one/two/three.jpg'
        item_data = "this is the text of a sample document".encode()

        file_dir = 'tmp'
        cache_db_path = os.path.join(file_dir, 'alveo_cache.db')
        self.addCleanup(shutil.rmtree, file_dir, True)

        cache = pyalveo.Cache(file_dir)

        cache.add_document(item_url, item_data)

        self.assertTrue(cache.has_document(item_url))
        self.assertEqual(item_data, cache.get_document(item_url))

    # TODO: test max_age expiry of cache contents





if __name__ == "__main__" :
    unittest.main(verbosity=5)
