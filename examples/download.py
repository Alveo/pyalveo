"""Example script to download files from an item list,
 for example, to download one audio file and the TextGrid
 annotations for data from the Austalk corpus

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
import pyalveo

# this is a shared item list with a sample of Austalk files that
# contain TextGrid annotations, change this URL to your own item
# list to download different data
itemlist_url = "https://app.alveo.edu.au/item_lists/484"

# directory to write downloaded data into
outputdir = "data"

if __name__=='__main__':

    client = pyalveo.Client(use_cache=False)

    itemlist = client.get_item_list(itemlist_url)

    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    print "Item list name: ", itemlist.name()
    for itemurl in itemlist:
        item = client.get_item(itemurl)
        meta = item.metadata()
        speakerid = meta['alveo:metadata']['olac:speaker']
        print "Item:", meta['alveo:metadata']['dc:identifier']

        # write out to a subdirectory based on the speaker identifier
        subdir = os.path.join(outputdir, speakerid)
        if not os.path.exists(subdir):
            os.makedirs(subdir)


        for doc in item.get_documents():
            filename = doc.get_filename()

            if filename.endswith('speaker16.wav') or filename.endswith('.TextGrid'):
                print '\t', filename
                doc.download_content(dir_path=subdir)
