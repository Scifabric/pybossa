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

    def tasks(self):

        from SPARQLWrapper import SPARQLWrapper, JSON

        sparql = SPARQLWrapper(self.sparql_url)
        sparql.setQuery("""
            PREFIX dbo: <http://dbpedia.org/ontology/>
            PREFIX dbr: <http://dbpedia.org/resource/>
            PREFIX dbp: <http://dbpedia.org/property/>
            PREFIX foaf: <http://xmlns.com/foaf/0.1/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

                        SELECT ?members ?bandName where {
                        ?band dbo:genre dbr:Punk_rock .
                        ?band dbp:currentMembers ?members.
                        ?band foaf:name ?bandName
                        FILTER(langMatches(lang(?bandName), "en"))
                        } LIMIT 20
        """)
        sparql.setReturnFormat(JSON)
        results = sparql.queryAndConvert()
        for result in results["results"]["bindings"]:
            task_data = {
                "info": {},
            }
            if self.task_priority != "":
                task_data["priority_0"] = self.task_priority
            if self.task_n_answers != "":
                task_data["n_answers"] = self.task_n_answers

            for binding in result.keys():
                task_data["info"][binding] = result[binding]["value"]

            print task_data
            yield task_data
