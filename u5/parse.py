# coding: UTF-8
import logging
import re
import lxml.html
import requests
import pdftableextract as pte
import contextlib
import rdflib
import subprocess
import io
import os
import sys
import hashlib
import glob
import csv
import threading
from urllib.parse import urlparse
from .html_table import Table

tasks = []
def task(code):
	def proc(func):
		def wrap(**kwargs):
			try:
				gen = func()
				if gen is None:
					return iter([])
				
				res = list(gen)
				if not res:
					logging.warn("code %s emits nothing" % code)
				return iter(res)
			except:
				logging.error("code %s" % code, exc_info=True)
		tasks.append(wrap)
		return wrap
	return proc

def meta_write(filename, g):
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

class Fs(str):
	@property
	def path(self):
		pc = urlparse(self)
		if len(pc.path) < 2: # "" or "/"
			pc.path = "/index.html"
		
		if pc.query:
			return pc.netloc + pc.path + "@" + pc.query
		
		return pc.netloc + pc.path
	
	@property
	def local(self):
		return "docs/" + self.path
	
	@property
	def remote(self):
		return "https://hkwi.github.com/U5/" + self.path

NS1 = rdflib.Namespace("https://hkwi.github.io/U5/scheme#")

def fetch(url, meta_filename="docs/meta.ttl", save=True):
	'''
	@return data, Fs(obj)
	'''
	fs = Fs(url)
	with meta(meta_filename) as g:
		lm = g.value(rdflib.URIRef(url), NS1["last-modified"])
		
		fp = None
		if save and os.path.exists(fs.local) and lm:
			fp = requests.get(url, headers={"If-Modified-Since":lm})
			if fp.status_code == 304: # xxx: not modified
				return open(fs.local, "rb"), fs
		
		if fp is None:
			fp = requests.get(url)
		
		if not fp.ok:
			logging.error("wget failed: %s" % url)
			return None, None
		
		logging.info("downloading %s" % url)
		if save:
			os.makedirs(os.path.dirname(fs.local), exist_ok=True)
			with open(fs.local, "wb") as w:
				for data in fp:
					w.write(data)
			
			g.set((rdflib.URIRef(url), NS1["mirror"], rdflib.URIRef(fs.remote)))
			lm = fp.headers.get("last-modified")
			if lm:
				g.set((rdflib.URIRef(url), NS1["last-modified"], rdflib.Literal(lm)))
		
		return io.BytesIO(fp.content), fs

def _get(url, save=False):
	fp, fs = fetch(url, save=save)
	# using binary data insted of text to hook lxml.html beautifulsoup cleaner
	r = lxml.html.parse(fp, base_url=url).getroot()
	r.make_links_absolute()
	return r

def get(url):
	return _get(url, save=False)

def wget(url):
	return _get(url, save=True)

class Css(object):
	def __init__(self, pattern):
		self.pattern = pattern
	
	def _get(self, url, save=False):
		'''
		fetch the url and select over the document
		'''
		return _get(url, save=save).cssselect(self.pattern)
	
	def get(self, url):
		return self._get(url, save=False)
	
	def wget(self, url):
		return self._get(url, save=True)

def pdftable(url, meta_filename="docs/meta.ttl"):
	'''
	@return generator
	yields a table (list of list)
	'''
	_, fs = fetch(url, meta_filename=meta_filename)
	if not fs or not os.path.exists(fs.local):
		return []
	
	d = hashlib.md5()
	d.update(open(fs.local, "rb").read())
	h = d.hexdigest()
	with meta(meta_filename) as g:
		h2 = g.value(rdflib.URIRef(fs), NS1["md5"])
		if not h2 or h != h2.value:
			for f in glob.glob(re.sub(r".pdf", "_*.csv", fs.local)):
				os.remove(f)
			
			out = subprocess.check_output(("pdfinfo", fs.local)).decode(sys.stdout.encoding)
			pages = None
			for l in io.StringIO(out):
				m = re.match(r"^Pages:\s*(\d+)", l)
				if m:
					pages = int(m.group(1))
			assert pages
			for i in range(pages):
				p = i+1
				try:
					cells = pte.process_page(fs.local, str(p), whitespace="raw")
				except:
					print(fs, p, i)
					raise
					
				out = re.sub(r".pdf", "_%d.csv" % i, fs.local)
				try:
					pte.output(cells, i, table_csv_filename=out)
				except:
					logging.error(fs.local, exc_info=True)
					raise
			
			g.set((rdflib.URIRef(fs), NS1["md5"], rdflib.Literal(h)))
		
		for f in glob.glob(re.sub(r".pdf", "_*.csv", fs.local)):
			yield list(csv.reader(open(f)))

def tbtable(tb):
	def txt(obj):
		if obj is None:
			return ""
		return obj.text_content()
	return Table(tb).matrix(txt)
