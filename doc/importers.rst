
.. _importers:

Importer interface
==================

Task importers are currently located in view/importer.py; each gets
a class, which should inherit from BulkTaskImportForm and provide
the following public interface:

* importer_id
* tasks()
* variants

importer_id is the name of the importer; any of the supported importers:
'csv', 'gdocs' and 'epicollect'

tasks() should generate a list of tasks

variants, a class method, should list all the variants of this importer;
this mechanism is used for Google Docs
