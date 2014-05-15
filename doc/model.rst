============
Domain Model
============

This section introduces the main domain objects present in the PyBossa system (see the :doc:`api` section for details about how you can access some of the objects using the API).


Overview
--------

PyBossa has 5 main domain objects:

  * App: the overall Project (formerly named Application) to which Tasks are associated.

    * HasMany: Tasks
    * HasA: Category

  * Task: an individual Task which can be performed by a user. A Task is associated to an App.

    * HasA: App
    * HasMany: TaskRuns

  * TaskRun: the results of a specific User performing a specific task

    * HasA: Task
    * HasA: User

  * User: a user account
  * Category: a project category

There are some attributes common across most of the domain objects notably:

  * `create_time`: the Datetime (as an integer) when object was created.
  * `info`: a 'blob-style' attribute into which one can store arbitrary JSON. This attribute is use to any additional information one wants (e.g. Task configuration or Task results on TaskRun)

The following excerpts directly from the PyBossa source to provide
documentation of main model attributes.

App
---

.. autoclass:: pybossa.model.app.App
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
