PyHCSvLab
=========

A Python library for interfacing with the HCSvLab API

Version
----

0.1

Introduction
-----------

PyHCSVlab comprises the ``hcsvlab`` module and its dependencies, which provides object-oriented access to the HCSVlab API, with the following features:

- A Client class with full API coverage
- API-aware classes representing HCSvLab items, Item Lists, and documents, with sensibly overloaded operators
- Seamless (but configurable) local caching of item metadata, document content data and primary texts using SQLite3
- Comprehensive epydoc documentation

Documentation
-------------
This file provides only an introduction to this module. Full documentation can be found at ./documentation/index.html

Dependencies
--------------

The ``hcsvlab`` module requires the following:

- PyYAML 3.10
- dateutil 2.0

Both of these are included in this repository.

Classes
----

Below are short summaries of each class included in the ``hcsvlab`` module. For complete documentation, see documentation/index.html

**Client**

Implements all HCSvLab API methods. Generally, you will want to construct a Client using the ``default_config()`` method, or with the ``with_config_file()`` method (see below for information on the format of the configuration file), but you can also specify the configuration manually:

```py
client = hcsvlab.Client.default_config()
client = hcsvlab.Client.with_config_file('my_config.yaml')
client = hcsvlab.Client('MYAPIKEY', hcsvlab.Cache('cache.db'), 'http://ic2-hcsvlab-staging2-vm.intersect.org.au')
```

**ItemGroup**

Represents an ordered list of HCSvLab items. Essentially behaves like a List of item URLs, but with additional functionality. Get an individual item as an Item object with ``get_item()``. Supports addition (union), subtraction (relative complement), and intersection, equality-checking, iteration, length inspection, indexing, and membership checking:

```py
ig1 = client.search_metadata('componentName:digits AND prompt:nine')
ig2 = client.search_metadata('componentName:digits AND prompt:seven')

#these are all valid:
item = ig1.get_item(1)
union = ig1 + ig2
sub = ig1 - ig2
inter = ig1.intersection(ig2)
if ig1 == ig2: print('False')
item_url = ig1[1]
len(ig1)
if item in ig1: print('True')

#so you can do things like:
docs = [i.get_document() for i in (ig1 - ig2).get_all()]
client.download_items(ig1 + ig2, 'items.zip')
```

**ItemList**

Extends (inherits from) ItemGroup to represent an Item List appearing on the HCSvLab server, with additional Item List-specifc metadata and functionality. Primarily, the ``refresh()`` and ``append()`` methods:

```py
il = client.get_item_list_by_name('foobar')
il.append(ig2)
#il should now reflect the new items, both locally and on the server

#if we add items using another method, the list needs to be refreshed manuallly before it will be updated:
cl.add_to_item_list([ig1[200]], il)
il.refresh() 
```

**Item**

Represents a single HCSvLab item. Essentially behaves like a String containing the item's URL, but with additional functionality. Access the item's metadata as a dictionary with ``metadata()``, and its documents as Document objects with ``get_document()``.

```py
item = ig1.get_item(2)
if item == ig2.get_item(2): 
    print(item.metadata()['metadata']['austalk:prompt'])

if item in ig2: item.add_to_item_list(il)

#or, equivalently:
if item.url() in ig2: il.append(item)



```

**Document**

Represents a single HCSvLab document. Mostly you probably want to use ``get_content`` to get the content data, or ``download_content`` to download it to a file.

```py
doc = item.get_document()
doc.download_content('/home/me/downloads') #uses original filename, or:
doc.download_content('/home/me/downloads', 'filename.wav')

#this produces the actual data
data = doc.get_content()
```

**Cache**

Implements caching of item metadata, document content data, and item primary texts. Metadata and primary texts are stored in an SQLite3 database, and data files are stored in the filesystem (the database keeps track of the paths, which are UUIDs, because the orginal filenames are not guaranteed to be unique). 

When you construct a Cache instance, you can specify a maximum age (in seconds), and the ``has_`` methods will ignore files older than that, so any Client using that Cache will not 'see' those older records, and will instead download that information from the server if it is requested (and update the cache's record at that point)

You can turn off reading from or writing to the cache entirely for a given Client using the Client's ``use_cache`` and ``update_cache`` options. Furthermore, all methods of Client, ItemGroup, ItemList, Item, and Document objects which would normally read data from the cache can be forced to download the information from the server instead using the ``force_download`` option.

**APIError**

Exception thrown whenever an API access is unsuccessful.

Configuration
----
``Client.with_config_file()`` reads a YAML file specifying (as key-value pairs) the options that would normally be passed to ``Cache()`` and ``Client()``. A default configuration file, ``config.yaml``, is provided, though an API key needs to be filled in before use (this is the file that is passed to ``Client.with_config_file()`` when ``Client.default_config()`` is called).

To generate a new (empty) cache database, call ``hcsvlab.create_cache_database(path, file_dir)``. The database file will be created at ``path``, and data files will be stored in ``file_dir``, which will be created if it does not already exist.


Metadata Search Query Syntax
----
The Client method ``metadata_search()`` takes a query string (based on the Apache Solr query syntax) which is passed to the server. The documentation for the query syntax is currently being compiled, but in the meantime, the following is known to work:

- A bare alphanumeric string (e.g. ``digits``) will match all items with that string anywhere in their metadata
- Individual metadata fields can be searched with ``field_name:value``, but the ``field_name`` is not the name used in the item metadata, but a corresponding identifier obtained from [this lookup table](http://ic2-hcsvlab-staging2-vm.intersect.org.au/catalog/searchable_fields)
- The latter type can be combined with a Boolean AND, for example ``componentName:digits AND prompt:nine AND created:Sep``
