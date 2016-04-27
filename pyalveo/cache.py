import os
import sqlite3
import datetime
import uuid
import warnings

import dateutil.parser
import dateutil.tz



class Cache(object):
    """ Handles caching for Alveo API Client objects """

    def __init__(self, cache_dir, max_age=0):
        """ Create a new Cache object

        :type cache_dir: String
        @para cache_dir: directory to store cache database and large files
        :type max_age: int
        :param max_age: cache entries older than this many seconds will be
        ignored by the has_item, has_document and has_primary_text methods

        :rtype: Cache
        :returns: the new Cache


        """
        self.max_age = max_age
        self.cache_dir = os.path.expanduser(cache_dir)
        self.database = os.path.join(self.cache_dir, 'alveo_cache.db')
        self.file_dir = os.path.join(self.cache_dir, 'files')

        # create file_dir using makedirs which will also make cache_dir if needed
        if not os.path.exists(self.file_dir):
            os.makedirs(self.file_dir)
        elif not os.path.isdir(self.cache_dir):
            raise Exception("file_dir exists and is not a directory")

        if not os.path.isfile(self.database):

            self.create_cache_database()

        self.conn = sqlite3.connect(self.database)
        self.conn.text_factory = str

    def create_cache_database(self):
        """ Create a new SQLite3 database for use with Cache objects


        :raises: IOError if there is a problem creating the database file

        """

        conn = sqlite3.connect(self.database)
        conn.text_factory = str

        c = conn.cursor()
        c.execute("""CREATE TABLE items
                     (url text, metadata text, datetime text)""")
        c.execute("""CREATE TABLE documents
                     (url text, path text, datetime text)""")
        c.execute("""CREATE TABLE primary_texts
                     (item_url text, primary_text text, datetime text)""")
        conn.commit()
        conn.close()



    def __eq__(self, other):
        """ Return True if this cache has identical fields to another

        :type other: Cache
        :param other: the other Cache

        :rtype: Boolean
        :returns: True if the caches are identical, oterwise False


        """
        return(self.max_age == other.max_age and
               self.database == other.database)



    def __ne__(self, other):
        """ Return False if this cache has all identical fields to another

        :type other: Cache
        :param other: the other Cache

        :rtype: Boolean
        :returns: False if the caches are identical, oterwise True


        """
        return not self.__eq__(other)


    def __del__(self):
        """ Close the database connection """
        self.conn.close()


    def __exists_row_not_too_old(self, row):
        """ Check if the given row exists and is not too old """
        if row is None:
            return False
        record_time = dateutil.parser.parse(row[2])
        now = datetime.datetime.now(dateutil.tz.gettz())
        age = (record_time - now).total_seconds()
        if age > self.max_age:
            return False

        return True

    @staticmethod
    def __now_iso_8601():
        """ Get the current local time as an ISO 8601 string """
        return datetime.datetime.now(dateutil.tz.gettz()).isoformat()


    def has_item(self, item_url):
        """ Check if the metadata for the given item is present in
        the cache

        If the max_age attribute of this Cache is set to a nonzero value,
        entries older than the value of max_age in seconds will be ignored

        :type item_url: String or Item
        :param item_url: the URL of the item, or an Item object

        :rtype: Boolean
        :returns: True if the item is present, False otherwise


        """
        c = self.conn.cursor()
        c.execute("SELECT * FROM items WHERE url=?", (str(item_url),))
        row = c.fetchone()
        c.close()
        return self.__exists_row_not_too_old(row)


    def has_document(self, doc_url):
        """ Check if the content of the given document is present
        in the cache

        If the max_age attribute of this Cache is set to a nonzero value,
        entries older than the value of max_age in seconds will be ignored

        :type doc_url: String or Document
        :param doc_url: the URL of the document, or a Document object

        :rtype: Boolean
        :returns: True if the data is present, False otherwise


        """
        c = self.conn.cursor()
        c.execute("SELECT * FROM documents WHERE url=?", (str(doc_url),))
        row = c.fetchone()
        c.close()
        return self.__exists_row_not_too_old(row)


    def has_primary_text(self, item_url):
        """ Check if the primary text corresponding to the
        given item is present in the cache

        If the max_age attribute of this Cache is set to a nonzero value,
        entries older than the value of max_age in seconds will be ignored

        :type item_url: String or Item
        :param item_url: the URL of the item, or an Item object

        :rtype: Boolean
        :returns: True if the primary text is present, False otherwise


        """
        c = self.conn.cursor()
        c.execute("SELECT * FROM primary_texts WHERE item_url=?",
                      (str(item_url),))
        row = c.fetchone()
        c.close()
        return self.__exists_row_not_too_old(row)


    def get_item(self, item_url):
        """ Retrieve the metadata for the given item from the cache.

        :type item_url: String or Item
        :param item_url: the URL of the item, or an Item object

        :rtype: String
        :returns: the item metadata, as a JSON string

        :raises: ValueError if the item is not in the cache


        """
        c = self.conn.cursor()
        c.execute("SELECT * FROM items WHERE url=?", (str(item_url),))
        row = c.fetchone()
        c.close()
        if row is None:
            raise ValueError("Item not present in cache")
        return row[1]


    def get_document(self, doc_url):
        """ Retrieve the content for the given document from the cache.

        :type doc_url: String or Document
        :param doc_url: the URL of the document, or a Document object

        :rtype: String
        :returns: the document data

        :raises: ValueError if the item is not in the cache


        """
        c = self.conn.cursor()
        c.execute("SELECT * FROM documents WHERE url=?", (str(doc_url),))
        row = c.fetchone()
        c.close()
        if row is None:
            raise ValueError("Item not present in cache")
        file_path = row[1]
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except IOError as e:
            raise IOError("Error reading file " + file_path +
                          " to retrieve document " + doc_url +
                          ": " + e.message)


    def get_primary_text(self, item_url):
        """ Retrieve the primary text for the given item from the cache.

        :type item_url: String or Item
        :param item_url: the URL of the item, or an Item object

        :rtype: String
        :returns: the primary text

        :raises: ValueError if the primary text is not in the cache


        """
        c = self.conn.cursor()
        c.execute("SELECT * FROM primary_texts WHERE item_url=?",
                      (str(item_url),))
        row = c.fetchone()
        c.close()
        if row is None:
            raise ValueError("Item not present in cache")
        return row[1]


    def add_item(self, item_url, item_metadata):
        """ Add the given item to the cache database, updating
        the existing metadata if the item is already present

        :type item_url: String or Item
        :param item_url: the URL of the item, or an Item object
        :type item_metadata: String
        :param item_metadata: the item's metadata, as a JSON string


        """
        c = self.conn.cursor()
        c.execute("DELETE FROM items WHERE url=?", (str(item_url),))
        self.conn.commit()
        c.execute("INSERT INTO items VALUES (?, ?, ?)",
                  (str(item_url), item_metadata, self.__now_iso_8601()))
        self.conn.commit()
        c.close()


    def __generate_filepath(self):
        """ Generate a unique (absolute) file path within the file_dir directory

        :rtype: String
        :returns: a unique file path


        """
        file_path = os.path.join(self.file_dir, str(uuid.uuid4()))
        if os.path.exists(file_path):
            warnings.warn("something has almost certainly gone wrong")
            return self.__generate_filepath()
        return file_path


    def add_document(self, doc_url, data):
        """ Add the given document to the cache, updating
        the existing content data if the document is already present

        :type doc_url: String or Document
        :param doc_url: the URL of the document, or a Document object
        :type data: String
        :param data: the document's content data


        """
        file_path = self.__generate_filepath()
        with open(file_path, 'wb') as f:
            f.write(data)

        c = self.conn.cursor()
        c.execute("SELECT * FROM documents WHERE url=?", (str(doc_url),))
        for row in c.fetchall():
            old_file_path = row[1]
            if os.path.isfile(old_file_path):
                os.unlink(old_file_path)
        c.execute("DELETE FROM documents WHERE url=?", (str(doc_url),))
        self.conn.commit()
        c.execute("INSERT INTO documents VALUES (?, ?, ?)",
                  (str(doc_url), file_path, self.__now_iso_8601()))
        self.conn.commit()
        c.close()

    def add_primary_text(self, item_url, primary_text):
        """ Add the given primary text to the cache database, updating
        the existing record if the primary text is already present

        :type item_url: String or Item
        :param item_url: the URL of the corresponding item, or an Item object
        :type primary_text: String
        :param primary_text: the item's primary text


        """
        c = self.conn.cursor()
        c.execute("DELETE FROM primary_texts WHERE item_url=?",
                      (str(item_url),))
        self.conn.commit()
        c.execute("INSERT INTO primary_texts VALUES (?, ?, ?)",
                  (str(item_url), primary_text, self.__now_iso_8601()))
        self.conn.commit()
        c.close()
