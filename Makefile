SHELL := /bin/bash

all: cert/lgpki.pem
	python3 -m u5

cert/lgpki.pem:
	cd cert && bash lgpki.sh
