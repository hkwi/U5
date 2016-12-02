import re
import rdflib
import itertools
from .util import tasks, res, NS1
from . import task28

g = rdflib.Graph()
for obj in itertools.chain(*[t() for t in tasks]):
	if isinstance(obj, res):
		assert obj.env.get("code"), obj.env
		
		for tb in obj.tables():
			if len(tb) < 2:
				continue
			if len(set([len(t) for t in tb])) > 1:
				warnings.warn("table alignment broken in %s" % obj.url)
			
			def scan(word):
				for i,row in enumerate(tb):
					for j,cell in enumerate(row):
						if word in re.sub(r"[\s　]*", "", cell):
							return (i,j)
			
			pkeys = []
			for k in ("園名", "名称", "施設名"):
				idx = scan(k)
				if idx:
					pkeys.append(idx)
			
			keys = []
			for k in ("住所", "所在", "電話", "定員", "位置"):
				idx = scan(k)
				if idx:
					keys.append(idx)
			
			ki = set([i[0] for i in pkeys+keys])
			kj = set([i[1] for i in pkeys+keys])
			
			def triples(table, idx_row):
				idx = None
				for i,row in enumerate(table):
					if i==idx_row:
						idx = row
						continue
					
					if idx:
						name = re.sub(r"[\s　]*", "", "".join([row[k[1]] for k in pkeys]))
						if name:
							code = obj.env.get("code")
							b = rdflib.BNode(code+name)
							g.add((b, NS1["ref"], rdflib.URIRef(obj.url)))
							g.add((b, NS1["code"], rdflib.Literal(code)))
							for k,v in zip(idx, row):
								field = re.sub(r"[\s　]*", "", k)
								value = v.strip()
								fixup = obj.env.get("fixup")
								if fixup:
									value = fixup(value)
								
								if field and value:
									g.add((b, NS1[field], rdflib.Literal(value)))
			
			if len(ki)==1 and len(kj) > 1:
				triples(tb, ki.pop())
			elif len(ki) > 1 and len(kj)==1:
				us = [[]]*len(tb[0])
				for i,row in enumerate(tb):
					for j,cell in enumerate(row):
						us[j].append(cell)
				
				triples(us, kj.pop())
			else:
				print(obj.url)
	else:
		print("!!!", url)

with open("docs/all.ttl", "wb") as w:
	g.serialize(destination=w, format="turtle")
