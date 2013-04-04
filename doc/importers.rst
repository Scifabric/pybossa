
.. _importers:

Importer interface
==================

Task importers are currently located in view/importer.py; each gets
a class, which should inherit from BulkTaskImportForm and provide
the following values:

* variants
* tasks()
* form_detector
* form_id
* template_id
