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
import os
import json
import tempfile
from pybossa.core import db, uploader
from pybossa.uploader import local, rackspace
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
import pybossa.model as model
from werkzeug.datastructures import FileStorage
from flask import url_for, safe_join, send_file, redirect

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

    def _make_zip(self, app, ty):
        name = self._app_name_encoded(app)
        json_task_generator = self._respond_json(ty, app.id)
        if json_task_generator is not None:
            datafile = tempfile.NamedTemporaryFile()
            try:
                for line in json_task_generator:
                    datafile.write(str(line))
                datafile.flush()
                zipped_datafile = tempfile.NamedTemporaryFile()
                try:
                    zip = self._zip_factory(zipped_datafile.name)
                    zip.write(datafile.name, '%s_%s.json' % (name, ty))
                    zip.close()
                    container = "user_%d" % app.owner_id
                    file = FileStorage(filename=self.download_name(app, ty), stream=zipped_datafile)
                    uploader.upload_file(file, container=container)
                finally:
                    zipped_datafile.close()
            finally:
                datafile.close()

    def download_name(self, app, ty):
        super(JsonExporter, self).download_name(app, ty)
        name = self._app_name_encoded(app)
        filename='%s_%s_json.zip' % (name, ty)
        return filename

    def get_zip(self, app, ty):
        super(JsonExporter, self).get_zip(app, ty)
        filepath = self._download_path(app)
        filename=self.download_name(app, ty)
        if not self.zip_existing(app, ty):
            print "Warning: Generating CSV on the fly now!"
            self._make_zip(app, ty)
        if isinstance(uploader, local.LocalUploader):
            return send_file(filename_or_fp=safe_join(filepath, filename), as_attachment=True)
        else:
            return redirect(url_for('rackspace', filename=filename, container=self._container(app)))


    def response_zip(self, app, ty):
        super(JsonExporter, self).response_zip(app, ty)
        return self.get_zip(app, ty)

    def pregenerate_zip_files(self, app):
        print "%d (json)" % app.id
        self._make_zip(app, "task")
        self._make_zip(app, "task_run")
