# -*- coding: utf8 -*-

import requests
from StringIO import StringIO
from flask.ext.babel import gettext
from pybossa.util import unicode_csv_reader

from .base import BulkTaskImport, BulkImportException
from werkzeug.datastructures import FileStorage
import io
import time


class BulkTaskSPARQLImport(BulkTaskImport):
    """Class to import tasks with a SPARQL query."""

    importer_id = "sparql"

    def __init__(self,
                 sparql_url,
                 sparql_query,
                 task_priority,
                 task_n_answers,
                 last_import_meta=None):
        self.sparql_url = sparql_url
        self.sparql_query = sparql_query
        self.task_priority = task_priority
        self.task_n_answers = task_n_answers
        self.last_import_meta = last_import_meta

    def convertToJsonValue(self, value):
        from SPARQLWrapper.SmartWrapper import Value
        if value.type == Value.TypedLiteral:
            if value.datatype == "http://www.w3.org/2001/XMLSchema#int":
                return int(value.value)
            elif value.datatype == "http://www.w3.org/2001/XMLSchema#double":
                return float(value.value)
        else:
            return value.value


    def tasks(self):
        from SPARQLWrapper import SPARQLWrapper2, JSON
        sparql = SPARQLWrapper2(self.sparql_url)
        sparql.setQuery(self.sparql_query)
        results = sparql.query().bindings
        for result in results:
            task_data = {
                "info": {},
            }
            if self.task_priority != "":
                task_data["priority_0"] = self.task_priority
            if self.task_n_answers != "":
                task_data["n_answers"] = self.task_n_answers
            for binding in result:
                task_data["info"][binding] = self.convertToJsonValue(result[binding])
            yield task_data
