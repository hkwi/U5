import itertools
from .parse import tasks
from . import task28

for url in itertools.chain(*[t() for t in tasks]):
	if isinstance(url, str):
		print(url)
