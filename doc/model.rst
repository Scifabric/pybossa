====================
Domain Model and API
====================

This section introduces the main domain objects present in the BOSSA system and how they can be accessed via the API.

Domain Model
============

BOSSA has 4 main domain objects:

  * Project: the overall projects to which Tasks are associated.
  * User: someone who performs a task
  * Task: an individual Task which can be performed by a user. A Task is associated to a Project.
  * TaskRun: the results of a specific User performing a specific task

There are some attributes common across most of the domain objects notably:

  * `create_time`: the Datetime (as an integer) when object was created.
  * `info`: a 'blob-style' attribute into which one can store arbitrary JSON. This attribute is use to any additional information one wants (e.g. Task configuration or Task results on TaskRun)


RESTful API
===========

The RESTful API is located at::

  http://{pybossa-site-url}/api

It expects and returns JSON.

Operations:

  List domain objects

  GET http://{pybossa-site-url}/api/{domain-object}


  Get a specific domain object by id

  GET http://{pybossa-site-url}/api/{domain-object}/{id}

  
  Create a domain object
  :return: 

  POST http://{pybossa-site-url}/api/{domain-object}


  Update a domain object (not yet implemented)
  PUT http://{pybossa-site-url}/api/{domain-object}/{id}


  Delete a domain object (not yet implemented)
  DELETE http://{pybossa-site-url}/api/{domain-object}/{id}


Example usage::

  curl -X POST -H "Content-Type:application/json" -s -d '{"name":"myapp", "info":{"xyz":1}}' 'http://localhost:5000/api/app'


