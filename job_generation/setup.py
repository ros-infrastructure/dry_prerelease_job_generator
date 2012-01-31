from setuptools import setup

setup(name='ros-job_generation',
      version= '0.1.0',
      install_requires=['python-jenkins', 'rospkg', 'rosdep'],
      packages=['job_generation'],
      package_dir = {'':'src'},
      scripts = ['scripts/create_distro.py',
                 'scripts/generate_deb_cleanup.py',
                 'scripts/generate_debbuild.py',
                 'scripts/generate_devel.py',
                 'scripts/generate_gazebo.py',
                 'scripts/generate_postrelease.py',
                 'scripts/generate_prerelease.py',
                 'scripts/generate_rosinstall.py',
                 'scripts/generate_unreleased.py',
                 'scripts/run_auto_stack_devel.py',
                 'scripts/run_auto_stack_prerelease.py',
                 'scripts/run_auto_stack_prerelease_devel.py',
                 'scripts/run_auto_stack_postrelease.py',
                 'scripts/run_auto_stack_unreleased.py',
                 'scripts/ros-src',
                 'scripts/ros-tar',
                 ],
      author = "Wim Meeussen", 
      author_email = "wim@willowgarage.com",
      url = "http://www.ros.org/wiki/job_generation",
      download_url = "http://pr.willowgarage.com/downloads/job_generation/", 
      keywords = ["ROS"],
      classifiers = [
        "Programming Language :: Python", 
        "License :: OSI Approved :: BSD License" ],
      description = "build farm job generation for dry jobs", 
      long_description = """\
build farm job generation for dry jobs
""",
      license = "BSD"
      )
