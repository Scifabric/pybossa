
.. _importers:

Importer interface
==================

Task importers are currently located in importers.py; each gets
a class, which should inherit from _BulkTaskImport and provide
the following public interface:

* importer_id
* tasks()

importer_id is the name of the importer; any of the supported importers:
'csv', 'gdocs', 'epicollect', 'flickr' and 'dropbox'.

tasks() should generate a list of tasks

These classes are intended for private use within the importers.py module. New
ones can be created here to handle different kind of importing mechanisms.
The module exposes the public class Importer, which will be the one resposible
for actually do the job of importing tasks, by using their public methods:

* create_tasks
* count_tasks_to_import
* get_all_importer_names
* get_autoimporter_names

create_importer takes as arguments task_repo, project_id, importer_id, and
**form_data. task_repo is a TaskRepository object that will handle the store of
the created Tasks. project_id, the id of the project to which the tasks belong.
importer_id being the name of the importer, like described above. Finally,
form_data will be a dictionary with the importer-specific form data (e.g. the
googledocs_url for a gdocs importer).

count_tasks_to_import takes as arguments the importer_id and **form_data, and
will return, before creating any task, the number of tasks that will be imported
from the source. This is used for instance for deciding whether to import the
tasks in a synchronous or an asynchronous way, depending on the amount of them.

get_all_importer_names returns a list of all the available importers. This list
may vary depending on the configuration of the server (e.g. if no API key for
integration with the Flickr service is found, then the Flickr importer won't be
available).

get_autoimporter_names returns a list of the available importers for using as
autoimport background jobs. Again, this list may vary depending on the  server
configuration.
