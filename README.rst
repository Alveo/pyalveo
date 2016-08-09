PyAlveo
=======

.. image:: https://badge.fury.io/py/pyalveo.svg
    :target: https://badge.fury.io/py/pyalveo
.. image:: https://travis-ci.org/Alveo/pyalveo.svg?branch=master
    :target: https://travis-ci.org/Alveo/pyalveo
.. image:: https://readthedocs.org/projects/pyalveo/badge/
    :target: https://pyalveo.readthedocs.io/

A Python library for interfacing with the Alveo API.

`Alveo <http://alveo.edu.au>`_ is a Virtual Laboratory platform to support
research on Human Communication. It
stores large collections of audio, video and textual data representing language use
and provides an API to search and retrieve data and metadata.  This Python library
is one way that Alveo integrates tools for processing data to support repeatable
research.

Introduction
------------

PyAlveo comprises the ``pyalveo`` module and its dependencies, which
provides object-oriented access to the Alveo API, with the following
features:

-  A Client class with full API coverage
-  API-aware classes representing Alveo items, Item Lists, and
   documents, with sensibly overloaded operators
-  Seamless (but configurable) local caching of item metadata and document
   content
-  Comprehensive epydoc documentation
