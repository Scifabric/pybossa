# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
#
# PyBossa is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBossa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBossa.  If not, see <http://www.gnu.org/licenses/>.
# Cache global variables for timeouts
"""
JSON Exporter module for exporting tasks and tasks results out of PyBossa
"""

from pybossa.exporter import Exporter
import json
import tempfile
from pybossa.core import db, uploader
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
import pybossa.model as model
from werkzeug.datastructures import FileStorage

class JsonExporter(Exporter):

    def _gen_json(self, table, id):
        n = db.slave_session.query(table)\
            .filter_by(app_id=id).count()
        sep = ", "
        yield "["
        for i, tr in enumerate(db.slave_session.query(table)
                                 .filter_by(app_id=id).yield_per(1), 1):
            item = json.dumps(tr.dictize())
            if (i == n):
                sep = ""
            yield item + sep
        yield "]"

    def _respond_json(self, ty, id):
        tables = {"task": model.task.Task, "task_run": model.task_run.TaskRun}
        try:
            table = tables[ty]
        except KeyError:
            print("key error")  # TODO

        return self._gen_json(table, id)

    def pregenerate_zip(self, app):
        print "%d (json)" % app.id
        name = self._app_name_encoded(app)
        json_task_generator = self._respond_json("task", app.id)
        if json_task_generator is not None:
            datafile = tempfile.NamedTemporaryFile()
            try:
                for line in json_task_generator:
                    datafile.write(str(line))
                datafile.flush()
                zipped_datafile = tempfile.NamedTemporaryFile()
                try:
                    zip = self._zip_factory(zipped_datafile.name)
                    zip.write(datafile.name, '%s_task.json' % name)
                    zip.close()
                    container = "user_%d" % app.owner_id
                    file = FileStorage(filename='%s_task_json.zip' % name, stream=zipped_datafile)
                    uploader.upload_file(file, container=container)
                finally:
                    zipped_datafile.close()
            finally:
                datafile.close()
        json_task_run_generator = self._respond_json("task_run", app.id)
        if json_task_run_generator is not None:
            datafile = tempfile.NamedTemporaryFile()
            try:
                for line in json_task_run_generator:
                    datafile.write(str(line))
                datafile.flush()
                zipped_datafile = tempfile.NamedTemporaryFile()
                try:
                    zip = self._zip_factory(zipped_datafile.name)
                    zip.write(datafile.name, '%s_task_run.json' % name)
                    zip.close()
                    container = "user_%d" % app.owner_id
                    file = FileStorage(filename='%s_task_run_json.zip' % name, stream=zipped_datafile)
                    uploader.upload_file(file, container=container)
                finally:
                    zipped_datafile.close()
            finally:
                datafile.close()
