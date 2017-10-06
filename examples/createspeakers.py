from __future__ import print_function

import pyalveo
import pprint


# we need an alveo.config file, get one from the staging server to run these as tests
client = pyalveo.Client(configfile='examples/alveo.config', verifySSL=True)

# this relies on an existing collection being available
collection_name = "testcollection"
collection_uri = client.api_url + "catalog/" + collection_name

print("collection_uri[%s]" %(collection_uri))

# add some speakers
speakers = {}
speakerids = ['jane', 'louise', 'mary']
for spkr in speakerids:
    meta = {
        'dcterms:identifier': spkr,
        'foaf:gender': 'female',
        'foaf:age': 21,
        'austalk:something': 12
    }
    spkr_url = client.add_speaker(collection_name, meta)
    speakers[spkr] = spkr_url
    print(spkr, spkr_url)

for spkr in speakerids:
    info = client.get_speaker(speakers[spkr])
    print(spkr)
    pprint.pprint(info)

print("SPEAKERS", client.get_speakers(collection_name))

# now try to get the speaker info via the SPARQL interface
# tests whether the correct RDF has been inserted by the system

qq = """
PREFIX dcterms:<http://purl.org/dc/terms/>
PREFIX foaf:<http://xmlns.com/foaf/0.1/>
select ?spkr ?p ?v where
{
  ?spkr a foaf:Person .
  ?spkr ?p ?v .
}"""

res = client.sparql_query(collection_name, qq)
for b in res['results']['bindings']:
    print("SPKR", b['spkr']['value'], b['p']['value'], b['v']['value'])

# remove all of the speakers
for spkr in speakerids:
    res = client.delete_speaker(speakers[spkr])
    print(res)

# check that they are gone
if not client.get_speakers(collection_name):
    print("SPEAKERS are gone!!")
else:
    print("Speakers were not deleted:", client.get_speakers(collection_name))
