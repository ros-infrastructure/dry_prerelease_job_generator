from setuptools import setup

setup(name='ros-groovy-job-generation',
      version= '0.2.9',
      install_requires=['python-jenkins', 'rospkg', 'rosdep'],
      packages=['job_generation_groovy'],
      package_dir = {'':'src'},
      scripts = ['scripts/generate_groovy_devel.py',
                 'scripts/generate_groovy_prerelease.py',
                 ],
      author = "Wim Meeussen",
      author_email = "wim@hidof.com",
      url = "http://wiki.ros.org/job_generation",
      download_url = "http://dowload.ros.org/downloads/ros-groovy-job-generation",
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
