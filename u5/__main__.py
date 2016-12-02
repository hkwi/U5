import itertools
from .util import tasks, res
from . import task28

for url in itertools.chain(*[t() for t in tasks]):
	if isinstance(url, res):
		for tb in url.tables():
			print(set([len(t) for t in tb]), len(tb))
	else:
		print("!!!", url)
