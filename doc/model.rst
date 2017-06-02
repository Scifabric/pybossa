============
Domain Model
============

This section introduces the main domain objects present in the PYBOSSA system (see the :doc:`api` section for details about how you can access some of the objects using the API).


Overview
--------

PYBOSSA has 5 main domain objects:

  * **Project**: the overall Project to which Tasks are associated.

    * HasA: Category
    * HasMany: Tasks

  * **Task**: an individual Task which can be performed by a user. A Task is associated to a project.

    * HasA: Project
    * HasA: Result
    * HasMany: TaskRuns

  * **TaskRun**: the answers of a specific User performing a specific task

    * HasA: Task
    * HasA: User

  * **Result**: the statistical result of analyzing the task runs for a given task in a project

    * HasA: Task
    * HasMany: TaskRuns

  * **HelpingMaterial**: media files for building advance tutorials

    * HasA: Project

  * **User**: a user account

  * **Category**: a project category

    * HasMany: Projects

There are some attributes common across most of the domain objects notably:

  * `create_time`: the Datetime (as an integer) when object was created.
  * `info`: a 'blob-style' attribute into which one can store arbitrary JSON. This attribute is use to any additional information one wants (e.g. Task configuration or Task results on TaskRun)

The following excerpts directly from the PYBOSSA source to provide
documentation of main model attributes.

Project
-------

.. autoclass:: pybossa.api.Project
   :members:


Category
--------

.. autoclass:: pybossa.model.category.Category
    :members:

Task
----

.. autoclass:: pybossa.model.task.Task
   :members:

TaskRun
-------

.. autoclass:: pybossa.model.task_run.TaskRun
   :members:

User
----

.. autoclass:: pybossa.model.user.User
   :members:

Blogpost
--------

.. autoclass:: pybossa.model.blogpost.Blogpost
   :members:


HelpingMaterial
---------------

.. autoclass:: pybossa.model.helpingmaterial.HelpingMaterial
   :members:

