# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
#
# PYBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PYBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PYBOSSA.  If not, see <http://www.gnu.org/licenses/>.

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

    def __init__(self, sparql_url, sparql_query, last_import_meta=None):
        self.sparql_url = sparql_url
        self.sparql_query = sparql_query
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
        result = sparql.queryAndConvert()
        for bindings in result["results"]["bindings"]:
            task_data = {"info": {}}
            for binding in bindings.keys():
                task_data["info"][binding] = bindings[binding]["value"]
                print task_data
                yield task_data

