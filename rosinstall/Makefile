all:
	echo "noop for debbuild"

setup:
	mkdir -p src/rosinstall/vcs
	svn export --force $(shell rospack find vcstools)/src/vcstools src/rosinstall/vcs


clean_dist:
	-rm -f MANIFEST
	-rm -rf dist

distro: setup clean_dist
	python setup.py sdist

clean: clean_dist
	rm -rf src/rosinstall
	svn up src/rosinstall

install: distro
	sudo checkinstall python setup.py install