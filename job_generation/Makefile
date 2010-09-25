all:
	mkdir -p export/ros-prerelease
	svn export --force $(shell rospack find job_generation)/src/job_generation/jobs_common.py export/ros-prerelease/ros_prerelease_jobs_common.py
	svn export --force $(shell rospack find job_generation)/src/job_generation/generate_prerelease.py export/ros-prerelease/ros-prerelease.py
	svn export --force $(shell rospack find hudson)/src/hudson.py export/ros-prerelease/ros_prerelease_hudson.py


clean_dist:
	-rm -f MANIFEST
	-rm -rf dist

distro: all clean_dist
	cd export/ros-prerelease && python setup.py sdist

clean: clean_dist
	rm -rf export/ros-prerelease

install: distro
	cd export/ros-prerelease && sudo checkinstall python setup.py install