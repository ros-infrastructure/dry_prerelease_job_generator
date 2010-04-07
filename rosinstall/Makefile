all:
	mkdir -p src/rosinstall
	svn export --force $(shell rospack find roslib2)/src/roslib2 src/rosinstall


clean_dist:
	-rm -f MANIFEST
	-rm -rf dist

distro: all clean_dist
	python setup.py sdist

clean: clean_dist
	rm -rf src/rosinstall
	svn up src/rosinstall

install: distro
	sudo checkinstall python setup.py install