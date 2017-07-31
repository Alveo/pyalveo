import pyalveo
import pprint

# we need an alveo.config file, get one from the staging server to run these as tests
client = pyalveo.Client(configfile='examples/alveo.config', verifySSL=True)



collection_name = "testcollection"
collection_uri = client.api_url + "catalog/" + collection_name

print "collection_uri[%s]" %(collection_uri)

# add some speakers
speakers = {}
speakerids = ['jane', 'louise', 'mary']
for spkr in speakerids:
    meta = {
        'dcterms:identifier': spkr,
        'foaf:gender': 'female',
        'foaf:age': 21,
    }
    spkr_url = client.add_speaker(collection_name, meta)
    speakers[spkr] = spkr_url
    print(spkr, spkr_url)

for spkr in speakerids:
    info = client.get_speaker(speakers[spkr])
    print(spkr)
    pprint.pprint(info)

print("SPEAKERS", client.get_speakers(collection_name))

# run a sparql query - should pick up the speakers
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

for spkr in speakerids:
    res = client.delete_speaker(speakers[spkr])
    print(res)

print("SPEAKERS", client.get_speakers(collection_name))
