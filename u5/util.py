import io
import sys
import re
import csv
import glob
import hashlib
import functools
import os.path
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
	
	def __call__(self, func):
		# function decorator
		def wrap(*args, **kwargs):
			with self:
				return func(*args, **kwargs)
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
		
		return functools.reduce(lambda x,y:x+y, [n.cssselect("a") for n in r.cssselect(css)])
