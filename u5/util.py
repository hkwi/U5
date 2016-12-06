import io
import sys
import re
import csv
import glob
import hashlib
import functools
import os.path
import collections
import contextlib
import logging
import subprocess
import threading
import rdflib
import lxml.html
import requests
import pdftableextract as pte
from .html_table import Table
from urllib.parse import urlparse

import janome.tokenizer
tk = janome.tokenizer.Tokenizer()

env_stack = [dict(
	meta="docs/meta.ttl",
	local="docs/",
	remote="https://hkwi.github.com/U5/",
)]

class env(object):
	def __init__(self, **kwargs):
		self.kv = kwargs
	
	def __enter__(self):
		env_stack.append(self.kv)
	
	def __exit__(self, etype, evalue, tb):
		env_stack.pop()
	
	def __call__(self, genfunc):
		# generator function decorator
		def wrap(*args, **kwargs):
			with self:
				# XXX: don't do like this. We need a generator to pause the processing.
				# return genfunc(*args, **kwargs)
				gen = genfunc(*args, **kwargs)
				if gen:
					for u in gen:
						yield u
		return wrap
	
	@classmethod
	def all(self):
		ret = dict()
		for ctx in env_stack:
			ret.update(ctx)
		return ret
	
	@classmethod
	def get(self, key, default=None):
		return self.all().get(key, default)

L = threading.Lock()
def meta_write(filename, g):
	with L:
		with open(filename, "wb") as w:
			g.serialize(destination=w, format="turtle")

@contextlib.contextmanager
def meta(filename):
	g = rdflib.Graph()
	if os.path.exists(filename):
		g.load(filename, format="turtle")
	yield g
	th = threading.Thread(target=meta_write, args=(filename, g))
	th.start()
	th.join()

tasks = []
def task(f):
	tasks.append(f)
	return f

NS1 = rdflib.Namespace("https://hkwi.github.io/U5/scheme#")

class res(object):
	file = None
	content = None
	
	def __init__(self, url):
		self.url = url
		self.env = env.all()
	
	def __str__(self):
		return self.url
	
	def _prepare(self):
		url = self.url
		save = env.get("save", False)
		with meta(env.get("meta")) as g:
			params = {}
			
			verify = env.get("verify")
			if verify:
				params["verify"] = verify
			
			lm = g.value(rdflib.URIRef(url), NS1["last-modified"])
			if save and os.path.exists(self.local) and lm:
				params["headers"] = {"If-Modified-Since":lm}
			
			req = requests.get(url, **params)
			
			if req.status_code == 304: # xxx: not modified
				self.file = self.local
				return
			elif not req.ok:
				logging.error("wget failed: %s" % url)
				self.file = None
				return
			
			logging.info("downloading %s" % url)
			if save:
				os.makedirs(os.path.dirname(self.local), exist_ok=True)
				with open(self.local, "wb") as w:
					for data in req:
						w.write(data)
				
				g.set((rdflib.URIRef(url), NS1["mirror"], rdflib.URIRef(self.remote)))
				lm = req.headers.get("last-modified")
				if lm:
					g.set((rdflib.URIRef(url), NS1["last-modified"], rdflib.Literal(lm)))
				
				self.file = self.local
			else:
				self.content = req.content
	
	def open(self):
		if self.content is None and self.file is None:
			try:
				self._prepare()
			except requests.exceptions.SSLError:
				with env(verify="cert/lgpki.pem"):
					self._prepare()
		
		if self.content:
			return io.BytesIO(self.content)
		elif self.file:
			return open(self.local, "rb")
	
	@property
	def is_pdf(self):
		fp = self.open()
		if fp:
			with contextlib.closing(fp):
				return fp.read(5) == b"%PDF-"
	
	@property
	def root(self):
		fp = self.open()
		if fp:
			with contextlib.closing(fp):
				r = lxml.html.parse(fp, base_url=self.url).getroot()
				r.make_links_absolute()
				return r
	
	def tables(self):
		with env(save=True):
			if self.is_pdf:
				d = hashlib.md5()
				d.update(self.open().read())
				h = d.hexdigest()
				
				with meta(env.get("meta")) as g:
					h2 = g.value(rdflib.URIRef(self.url), NS1["md5"])
					if not h2 or h != h2.value:
						for f in glob.glob(re.sub(r".pdf", "_*.csv", self.local)):
							os.remove(f)
						
						out = subprocess.check_output(("pdfinfo", self.local)).decode(sys.stdout.encoding)
						pages = None
						for l in io.StringIO(out):
							m = re.match(r"^Pages:\s*(\d+)", l)
							if m:
								pages = int(m.group(1))
						assert pages
						for i in range(pages):
							p = i+1
							try:
								cells = pte.process_page(self.local, str(p), whitespace="raw")
							except:
								print(self.local, p, i)
								raise
								
							out = re.sub(r".pdf", "_%d.csv" % i, self.local)
							try:
								pte.output(cells, i, table_csv_filename=out)
							except:
								logging.error(self.local, exc_info=True)
								raise
						
						g.set((rdflib.URIRef(self.url), NS1["md5"], rdflib.Literal(h)))
					
					for f in glob.glob(re.sub(r".pdf", "_*.csv", self.local)):
						yield list(csv.reader(open(f)))
			else:
				def txt(obj):
					if obj is None:
						return ""
					return obj.text_content()
				
				root = self.root
				if root is None:
					return iter([])
				
				css = self.env.get("css", None)
				if css is None:
					for tb in root.cssselect("table"):
						yield Table(tb).matrix(txt)
				else:
					for main in root.cssselect(css):
						for tb in main.cssselect("table"):
							yield Table(tb).matrix(txt)
	
	def triples(self):
		assert self.env.get("code"), self.env
		
		for tb in self.tables():
			if len(tb) < 2:
				continue
			if len(set([len(t) for t in tb])) > 1:
				logging.warn("table alignment broken in %s" % self.url)
			
			def scan(word):
				for i,row in enumerate(tb):
					for j,cell in enumerate(row):
						if "。" in cell:
							continue # 文は見出しではない
						
						if isinstance(word, str):
							if word == re.sub(r"[\s　]*", "", cell):
								return (i,j) # 完全一致
							
							tks = tk.tokenize(re.sub(r"[\s　]*", "", cell))
							for t in tks:
								if word == t.surface:
									return (i,j)
						elif isinstance(word, tuple):
							tks = tk.tokenize(re.sub(r"[\s　]*", "", cell))
							sq = [t.surface for t in tks]
							if len(sq) > word:
								for i in range(len(sq)-len(word)):
									if sq[i:i+len(word)] == word:
										return (i,j)
			
			pkeys = []
			for k in ("名", "施設名", "園名", "名称", "施設名", "設置名"):
				idx = scan(k)
				if idx:
					pkeys.append(idx)
			
			keys = []
			for k in ("住所", "所在", "電話", "定員", "位置"):
				idx = scan(k)
				if idx:
					keys.append(idx)
			
			def triples(table, idx_row):
				idx = None
				for i,row in enumerate(table):
					if i==idx_row:
						idx = row
						continue
					
					if idx:
						name = re.sub(r"[\s　]*", "", "".join([row[k[1]] for k in pkeys]))
						if name:
							code = self.env.get("code")
							b = rdflib.BNode(code+name)
							yield b, NS1["ref"], rdflib.URIRef(self.url)
							yield b, NS1["code"], rdflib.Literal(code)
							for k,v in zip(idx, row):
								field = re.sub(r"[\s　]*", "", k)
								value = v.strip()
								fixup = self.env.get("fixup")
								if fixup:
									value = fixup(value)
								
								if field and value:
									yield b, NS1[field], rdflib.Literal(value)
			
			# print(pkeys, keys, self.url)
			ki = set([i[0] for i in pkeys+keys])
			kj = set([i[1] for i in pkeys+keys])
			
			def maybe_index(ks):
				if len(set(ks))==1:
					return True
				
				c = collections.Counter()
				for k in ks:
					c[k] += 1
				com = c.most_common()
				if len(com)>1 and com[0][1] > 1 and not [True for n in com[1:] if n[1]!=1]:
					return True
			
			if maybe_index([i[0] for i in pkeys+keys])==1 and len(kj) > 1:
				for t in triples(tb, ki.pop()):
					yield t
			elif len(ki) > 1 and len(kj)==1:
				us = [[]]*len(tb[0])
				for i,row in enumerate(tb):
					for j,cell in enumerate(row):
						us[j].append(cell)
				
				for t in triples(us, kj.pop()):
					yield t
	
	@property
	def path(self):
		pc = urlparse(self.url)
		path = pc.path
		if path=="":
			path = "/"
		if path.endswith("/"):
			path += "index.html"
		
		if pc.query:
			return pc.netloc + path + "@" + pc.query
		
		return pc.netloc + path
	
	@property
	def local(self):
		return env.get("local") + self.path
	
	@property
	def remote(self):
		return env.get("remote") + self.path

def links(url):
	fp = res(url).open()
	with contextlib.closing(fp):
		r = lxml.html.parse(fp, base_url=url).getroot()
		r.make_links_absolute()
		css = env.get("css", None)
		if css is None:
			return r.cssselect("a")
		
		ret = []
		for n in r.cssselect(css):
			for a in n.cssselect("a"):
				ret.append(a)
		
		return ret

def remove_line_separator(s):
	return s.replace("\n","").replace("\r","")
