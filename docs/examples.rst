Examples
========

This page contains some example scripts written using the API.

Download Austalk Data
---------------------

This script downloads files from the Austalk collection based on an item list. It could
be adapted to work with any collection.  It reads the metadata for the item list
and iterates over the items it contains. For each item it downloads files
ending in `speaker16.wav` and `TextGrid`.    Files are stored in directories
named for the speaker identifier for the item.

Note that in creating the client the cache is disabled to prevent versions of
downloaded files being cached.

.. code-block:: python

    from __future__ import print_function
    import os
    import pyalveo

    item_list_name = 'over-50-hvd'

    # directory to write downloaded data into
    outputdir = "data"

    client = pyalveo.Client(use_cache=False)

    itemlist = client.get_item_list_by_name(item_list_name)

    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    for itemurl in itemlist:
        item = client.get_item(itemurl)
        meta = item.metadata()

        speakerurl = meta['alveo:metadata']['olac:speaker']
        speaker_meta = client.get_speaker(speakerurl)
        speakerid = speaker_meta['dcterms:identifier']

        # write out to a subdirectory based on the speaker identifier
        subdir = os.path.join(outputdir, speakerid)
        if not os.path.exists(subdir):
            os.makedirs(subdir)

        for doc in item.get_documents():
            filename = doc.get_filename()

            if filename.endswith('speaker16.wav') or filename.endswith('.TextGrid'):
                print(filename)
                doc.download_content(dir_path=subdir)






