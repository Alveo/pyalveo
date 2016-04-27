import pyalveo
import time

# we need an alveo.config file, get one from the staging server to run these as tests
client = pyalveo.Client(configfile='examples/alveo-pc.config', verifySSL=False)
collection_uri = client.api_url + "catalog/sctestcollection1"

# delete any existing items
#for itemuri in client.get_items(collection_uri):
#    print("ITEM:", itemuri)
#    try:
#        client.delete_item(itemuri)
#    except:
#        pass

text = """
Mrs Campbell was very much frightened and ill for three weeks afterwords but fortunately for me I had not the sense to be frightened. Indeed Mrs Campbell was so much frightened that she told me she had miscarried her twintyeth child but gude forgie  me I think she hardly sticks to the truth in family concerns she makes them all very young and for Mrs McLeod who has three children and is just about to have the fourth she is only twenty one or two and the young ladies three straping queens are from eighteen to fifteen but the youngest may pass for eighteen and the oldest for twinty six. Well we lost sight of St Jago and then we were becalmed for weeks together and but for harpooning sharks and shooting whales I dont know what the gentlemen would have done with themselves and the ladies generally were disputing which of their lords or brothers or lords to be (for there were some matches made up on the way) that had the merit of sending the poor shooten fishes to their long homes - And then, but this is rather a serious story, a young man of the name of Nicholson, a servant of Mrs Campbell, went to sleep in the jolly boat and was struck by the sun.  He died on the ninth day afterwards and was buried on the day after his death. I never never will forget the sound of the deep and hollow plunge when the body was consined  to its fathomless bed of rest. It was a calm day and every wave was as still as death till the mornin after his funeral when all at once there was a breeze got up and in twelve hours we were a hundred miles from poor Nicholson.
"""
starttime = time.time()

docmeta = {  "@id": "document1",
              "@type": "foaf:Document",
              "dcterms:extent": len(text),
              "dcterms:identifier": "document1.txt",

              "dcterms:title": "document1#Text",
              "dcterms:type": "Text"
            }


for i in range(10):

    itemstart = time.time()

    itemname = "newitem%d" % i
    meta = {
            'dc:title': 'Test Item %d' % i,
            'dc:creator': 'A. Programmer'
            }
    item = client.add_item(collection_uri, itemname, meta)

    docstart = time.time()

    # add a document
    docmeta = {
               "dcterms:title": "Sample Document",
               "dcterms:type": "Text"
              }

    client.add_document(item, "document%d.txt" % i, docmeta, content=text)

    done = time.time()

    print "ITEM: ", itemname, done-itemstart, done-docstart, done-starttime

print "Overall: ", time.time()-starttime
