import re
import rdflib
import itertools
from .util import tasks, res, NS1
from . import task28

g = rdflib.Graph()
NS1=rdflib.Namespace("https://hkwi.github.io/U5/scheme#")
g.bind("ns1", NS1)
g.bind("ns2", NS1["0"])
g.bind("ns3", NS1["1"])
g.bind("ns4", NS1["3"])
g.bind("ns5", NS1["4"])
g.bind("ns6", NS1["5"])
g.bind("ns7", NS1["１"])
g.bind("ns8", NS1["４"])
g.bind("ns9", NS1["５"])
g.bind("ns10", NS1["所在地・"])
g.bind("ns11", NS1["利用年齢1号2号・3"])
g.bind("ns12", NS1["園（所）"])
g.bind("ns13", NS1["保育標準時間（保育短時間）"])
g.bind("ns14", NS1["病児・"])

for obj in itertools.chain(*[t() for t in tasks]):
	emit = False
	if isinstance(obj, res):
		for t in obj.triples():
			emit = True
			g.add(t)
	
	if not emit:
		print(obj.url)

with open("docs/all.ttl", "wb") as w:
	g.serialize(destination=w, format="turtle")
