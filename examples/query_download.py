"""Example script to search metadata for data from one
Austalk speaker and download all of their digit data.

To run this script you need to install the pyalveo library
which is available at (https://pypi.python.org/pypi/pyalveo/0.4) for
installation with the normal Python package tools (pip install pyalveo).

You also need to download your API key (alveo.config) from the Alveo web application
(click on your email address at the top right) and save it in your home directory:

Linux or Unix: /home/<user>
Mac: /Users/<user>
Windows: C:\Users\<user>

The script should then find this file and access Alveo on your behalf.



 """

import os
import sys
import pyalveo

speakerid = "1_1308"
component = "words"  # will find words-1, words-2 and words-3
component = "digits"

# directory to write downloaded data into
outputdir = "data"

if __name__=='__main__':

    client = pyalveo.Client(use_cache=False)

    items = client.search_metadata("collection_name:austalk AND speaker:%s AND componentName:%s" % (speakerid, component))

    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    print "Query found ", len(items), "items"

    client = pyalveo.Client(use_cache=False)
    items = client.get_item_list(item_list_url)
    for itemurl in items:
        item = client.get_item(itemurl)
        meta = item.metadata()
        speakerid = meta['alveo:metadata']['olac:speaker']

        # write out to a subdirectory based on the speaker identifier
        subdir = os.path.join(outputdir, speakerid)
        if not os.path.exists(subdir):
            os.makedirs(subdir)

        for doc in item.get_documents():
            filename = doc.get_filename()

            if filename.endswith('speaker16.wav') or filename.endswith('.TextGrid'):
                doc.download_content(dir_path=subdir)
