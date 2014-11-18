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
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
import pybossa.model as model
from werkzeug.datastructures import FileStorage
from flask import Response, url_for, safe_join

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

    def zip_existing(self, app, ty):
        super(JsonExporter, self).zip_existing(app, ty)
        filepath = self._download_path(app)
        filename=self.download_name(app, ty)
        # TODO: This only works on local files !!!
        return os.path.isfile(safe_join(filepath, filename))
        # TODO: Check rackspace file existence

    def get_zip(self, app, ty):
        super(JsonExporter, self).get_zip(app, ty)
        filepath = self._download_path(app)
        filename=self.download_name(app, ty)
        print "Hallo?!"
        if not self.zip_existing(app, ty):
            print "OMG this JSON is not existing!!!"
            self._make_zip(app, ty)     # TODO: make this with RQ?
        print "filepath %s   filename %s" % (filepath, filename)
        return send_from_directory(filepath, filename)

    def response_zip(self, app, ty):
        container = "user_%d" % app.owner_id
        filepath = safe_join(uploader.upload_folder, container)
        url = url_for(self.download_name(app, ty), filename=safe_join(container, self.download_name(app, ty)))
        return Response(url , mimetype='application/octet-stream')

    def pregenerate_zip_files(self, app):
        print "%d (json)" % app.id
        self._make_zip(app, "task")
        self._make_zip(app, "task_run")
