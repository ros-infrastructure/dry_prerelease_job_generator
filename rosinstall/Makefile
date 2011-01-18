.PHONY: all setup clean_dist distro clean install dsc source_deb upload

all:
	echo "noop for debbuild"

setup:
	mkdir -p src/rosinstall/vcs
	svn export --force $(shell rospack find vcstools)/src/vcstools src/rosinstall/vcs


clean_dist:
	-rm -f MANIFEST
	-rm -rf dist
	-rm -rf deb_dist

distro: setup clean_dist
	python setup.py sdist

clean: clean_dist
	rm -rf src/rosinstall/vcs

install: distro
	sudo checkinstall python setup.py install


dsc: distro
	python setup.py --command-packages=stdeb.command sdist_dsc

source_deb: dsc
	# need to convert unstable to each distro and repeat
	cd deb_dist/rosin* && dpkg-buildpackage -sa -S -k84C5CECD

upload: source_deb
	cd deb_dist && dput ppa:tully.foote/tully-test-ppa ../rosinstall_0.5.12-3_source.changes 
