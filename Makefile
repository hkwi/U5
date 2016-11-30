SHELL := /bin/bash

all:
	wget -P docs -N -x -i <(python3 -m u5.__main__)


