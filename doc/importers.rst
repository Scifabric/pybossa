
.. _importers:

Importer interface
==================

Task importers are currently located in view/importer.py; each gets
a class, which should inherit from _BulkTaskImport and provide
the following public interface:

* importer_id
* tasks()
* variants

importer_id is the name of the importer; any of the supported importers:
'csv', 'gdocs' and 'epicollect'

tasks() should generate a list of tasks

variants, a class method, should list all the variants of this importer;
this mechanism is used for Google Docs

In addition, a class named BulkTaskImportManager is provided, which should be
the only class to handle imports exported by this module. It acts as an
abstraction layer between the importers and the users of them (the views).
It exposes the following public methods:

* create_importer
* variants

create_importer takes as an argument the importer_id and returns an instance
of the required importer class

variants returns a list with all the variants for every importer defined in the
package
