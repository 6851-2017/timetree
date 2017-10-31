========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - |
        | |codecov|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|

.. |docs| image:: https://readthedocs.org/projects/timetree/badge/?style=flat
    :target: https://readthedocs.org/projects/timetree
    :alt: Documentation Status

.. |codecov| image:: https://codecov.io/github/6851-2017/timetree/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/6851-2017/timetree

.. |version| image:: https://img.shields.io/pypi/v/timetree.svg
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/timetree

.. |commits-since| image:: https://img.shields.io/github/commits-since/6851-2017/timetree/v0.1.0.svg
    :alt: Commits since latest release
    :target: https://github.com/6851-2017/timetree/compare/v0.1.0...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/timetree.svg
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/timetree

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/timetree.svg
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/timetree

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/timetree.svg
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/timetree


.. end-badges

General transformation to make python objects persistent

* Free software: MIT license

Installation
============

::

    pip install timetree

Documentation
=============

https://timetree.readthedocs.io/

Development
===========

To run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
