PyHCSvLab
=========

A Python library for interfacing with the HCSvLab API

Version
----

0.1a

Introduction
-----------

PyHCSVlab comprises the hcsvlab module and its dependencies, which provides object-oriented access to the HCSVlab API, with the following features:

- An Client class with full API coverage
- API-aware classes representing HCSvLab Items, Item Lists, and documents, with sensibly overloaded operators
- Seamless (but configurable) local caching of item metadata, document content data and primary texts using SQLite3
- Comprehensive epydoc documentation

Dependencies
--------------

The hcsvlab module requires the following:

- PyYAML 3.10
- dateutil 2.0

Both of these are included in this repository.

Classes
----

Below are short summaries of each class included in the hcsvlab module. For complete documentation, see documentation/index.html

**Client**

Implements all HCSvLab API methods. Generally, you will want to construct a Client using the <code>default_config_file()</code> method, or with the <code>with_config_file()</code> method (see below for information on the format of the configuration file), but you can also specify the configuration manually:

```py
client = hcsvlab.Client.default_config_file()
client = hcsvlab.Client.with_config_file('my_config.yaml')
client = hcsvlab.Client('MYAPIKEY', hcsvlab.Cache('cache.db'), 'http://ic2-hcsvlab-staging2-vm.intersect.org.au')
```

**ItemGroup**

Represents an ordered list of HCSvLab items. Essentially behaves like a List of item URLs. Get an individual item as an Item object with <code>get_item()</code>. Supports addition (union), subtraction (relative complement), and intersection, equality-checking, iteration, length inspection, indexing, and membership checking:

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
[i.get_document() for i in (ig1 - ig2).get_all()]
client.download_items([i in (ig1 + ig2)], 'items.zip')
```

**ItemList**

Extends ItemGroup to represent an Item List appearing on the HCSvLab server, with additional Item List-specifc metadata and functionality. Primarily, the <code>refresh()</code> and <code>append()</code> methods:

```py
il = client.get_item_list_by_name('foobar')
il.append(ig2) #works because ig2.__iter__() lists the item URLS
il.refresh() 
#il should now reflect the new items, both locally and on the server
```

**Item**

Represents a single HCSvLab item. Essentially behaves like a String containing the item's URL, but with additional functionality. Access the item's metadata as a dictionary with <code>metadata()</code>, and its documents as Document objects with <code>get_document()</code>.

```py
item = ig1.get_item(2)
if item == ig2.get_item(2): 
    print(item.metadata()['austalk:prompt'])

#works because item.__str__ produces the item's url
#and il.__str__ produces the Item List's url
if item in ig2: item.add_to_item_list(il)

#or, equivalently:
if item.url() in ig2: il.append(item)



```

**Document**

Represents a single HCSvLab document. Mostly you probably want to use <code>get_content</code> to get the content data, or <code>download_content</code> to download it to a file.

```py
doc = item.get_document()
doc.download_content('~/downloads') #uses original filename, or:
doc.download_content('~/downloads', 'filename.wav')

#this produces the actual data
data = doc.get_content()
```

**Cache**

Implements caching of item metadata, document content data, and item primary texts. Metadata and primary texts are stored in an SQLite3 database, and data files are stored in the filesystem (the database keeps track of the paths, which are UUIDs, because the orginal filenames are not guaranteed to be unique). 

When you construct a Cache instance, you can specify a maximum age (in seconds), and the <code>has_</code> methods will ignore files older than that, so any Client using that Cache will not 'see' those older records, and will instead download that information from the server if it is requested (and update the cache's record at that point)

You can turn off reading from or writing to the cache entirely for a given Client using the Client's <code>use_cache</code> and <code>update_cache</code> options. Furthermore, all methods of Client, ItemGroup, ItemList, Item, and Document objects which would normally read data from the cache can be forced to download the information from the server instead using the <code>force_download</code> option.

**APIError**

Exception thrown whenever an API access is unsuccessful.