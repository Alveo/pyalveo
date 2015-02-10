PyAlveo
=======

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
-  Seamless (but configurable) local caching of item metadata, document
   content data and primary texts using SQLite3
-  Comprehensive epydoc documentation

