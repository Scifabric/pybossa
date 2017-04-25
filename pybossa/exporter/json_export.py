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
# Cache global variables for timeouts
"""
JSON Exporter module for exporting tasks and tasks results out of PYBOSSA
"""

import json
import tempfile
from pybossa.exporter import Exporter
from pybossa.core import uploader, task_repo
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

class JsonExporter(Exporter):

    def gen_json(self, table, id):
        data = getattr(task_repo, 'filter_%ss_by' % table)(project_id=id)
        tmp = [row.dictize() for row in data]
        return tmp

    def _respond_json(self, ty, id):  # TODO: Refactor _respond_json out?
        # TODO: check ty here
        return self.gen_json(ty, id)

    def _make_zip(self, project, ty):
        name = self._project_name_latin_encoded(project)
        json_task_generator = self._respond_json(ty, project.id)
        if json_task_generator is not None:
            datafile = tempfile.NamedTemporaryFile()
            try:
                datafile.write(json.dumps(json_task_generator))
                datafile.flush()
                zipped_datafile = tempfile.NamedTemporaryFile()
                try:
                    _zip = self._zip_factory(zipped_datafile.name)
                    _zip.write(datafile.name, secure_filename('%s_%s.json' % (name, ty)))
                    _zip.close()
                    container = "user_%d" % project.owner_id
                    _file = FileStorage(filename=self.download_name(project, ty), stream=zipped_datafile)
                    uploader.upload_file(_file, container=container)
                finally:
                    zipped_datafile.close()
            finally:
                datafile.close()

    def download_name(self, project, ty):
        return super(JsonExporter, self).download_name(project, ty, 'json')

    def pregenerate_zip_files(self, project):
        print "%d (json)" % project.id
        self._make_zip(project, "task")
        self._make_zip(project, "task_run")
