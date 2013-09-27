.PHONY: all setup clean_dist distro clean install upload

NAME=ros-groovy-job-generation
VERSION=`python setup.py -V`

all:
	echo "noop for debbuild"

clean_dist:
	-rm -f MANIFEST
	-rm -rf dist
	-rm -rf deb_dist

distro: clean_dist
	python setup.py sdist

push: distro
	python setup.py sdist register upload
	scp dist/${NAME}-${VERSION}.tar.gz ros@ftp-osl.osuosl.org:/home/ros/data/download.ros.org/downloads/ros-groovy-job-generation

clean: clean_dist
	echo "clean"

install: distro
	sudo checkinstall python setup.py install

