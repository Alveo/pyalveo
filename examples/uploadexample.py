import pyalveo
import time
import tempfile
import os

# we need an alveo.config file, get one from the staging server to run these as tests
client = pyalveo.Client(configfile='examples/alveo.config')
collection_uri = client.api_url + "catalog/testcollection"

# delete any existing items
for itemuri in client.get_items(collection_uri):
    print("DELETE ITEM:", itemuri)
    try:
        client.delete_item(itemuri)
    except pyalveo.APIError:
        pass

text = """
Mrs Campbell was very much frightened and ill for three weeks afterwords but fortunately for me I had not the sense to be frightened. Indeed Mrs Campbell was so much frightened that she told me she had miscarried her twintyeth child but gude forgie  me I think she hardly sticks to the truth in family concerns she makes them all very young and for Mrs McLeod who has three children and is just about to have the fourth she is only twenty one or two and the young ladies three straping queens are from eighteen to fifteen but the youngest may pass for eighteen and the oldest for twinty six. Well we lost sight of St Jago and then we were becalmed for weeks together and but for harpooning sharks and shooting whales I dont know what the gentlemen would have done with themselves and the ladies generally were disputing which of their lords or brothers or lords to be (for there were some matches made up on the way) that had the merit of sending the poor shooten fishes to their long homes - And then, but this is rather a serious story, a young man of the name of Nicholson, a servant of Mrs Campbell, went to sleep in the jolly boat and was struck by the sun.  He died on the ninth day afterwards and was buried on the day after his death. I never never will forget the sound of the deep and hollow plunge when the body was consined  to its fathomless bed of rest. It was a calm day and every wave was as still as death till the mornin after his funeral when all at once there was a breeze got up and in twelve hours we were a hundred miles from poor Nicholson.
"""
starttime = time.time()

docmeta = {
              "dcterms:extent": len(text),
              "dcterms:title": "The Title",
              "dcterms:type": "Text"
            }


for i in range(3):

    itemstart = time.time()

    itemname = "yitem-%d" % i
    meta = {
            'dc:title': 'Test Item %d' % i,
            'dc:creator': 'A. Programmer'
            }
    item_uri = client.add_item(collection_uri, itemname, meta)
    print("ITEM: ", item_uri)
    # create a temporary file to upload
    with tempfile.NamedTemporaryFile() as fd:
        fd.write(b"Hello World")
        fd.flush()
        doc_uri = client.add_document(item_uri, os.path.basename(fd.name), docmeta, file=fd.name)
    print("DOC:", doc_uri)

print("Overall: ", time.time()-starttime)
