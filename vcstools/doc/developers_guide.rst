Developer's Guide
=================

Bug reports and feature requests
--------------------------------

- `Submit a bug report <https://code.ros.org/trac/ros/newticket?component=vcstools&type=defect&&vcstools>`_
- `Submit a feature request <https://code.ros.org/trac/ros/newticket?component=vcstools&type=enhancement&vcstools>`_

Testing
-------

Setup

::

    pip install nose
    pip install mock


rospkg uses `Python nose <http://readthedocs.org/docs/nose/en/latest/>`_ 
for testing, which is a fairly simple and straightfoward test
framework.  You just have to write a function start with the name
``test`` and use normal ``assert`` statements for your tests.

rospkg also uses `mock <http://www.voidspace.org.uk/python/mock/>`_ to
create mocks for testing.

You can run the tests, including coverage, as follows:

::

    cd vcstools
    make test


Documentation
-------------

Sphinx is used to provide API documentation for vcstools.  The documents
are stored in the ``doc`` subdirectory.

