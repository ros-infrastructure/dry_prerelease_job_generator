include $(shell rospack find mk)/cmake.mk



clean_dist:
	-rm -f MANIFEST
	-rm -rf dist

distro: 
	mkdir -p pypi/src/hudson
	cp src/hudson.py pypi/src/hudson/__init__.py
	cd pypi && python setup.py sdist

install: distro
	cd pypi && sudo checkinstall python setup.py install