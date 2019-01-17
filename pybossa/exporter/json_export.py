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

import uuid
import json
import tempfile
from pybossa.exporter import Exporter
from pybossa.core import uploader, task_repo, sentinel
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from rq_scheduler import Scheduler
from datetime import timedelta
from flask import current_app

redis_conn = sentinel.master
scheduler = Scheduler(queue_name='scheduled_jobs', connection=redis_conn)


class JsonExporter(Exporter):

    def gen_json(self, table, project_id):
        return self._get_data(table, project_id)

    def _respond_json(self, ty, id):  # TODO: Refactor _respond_json out?
        # TODO: check ty here
        return self.gen_json(ty, id)

    def _make_zip(self, project, ty, name=None, data=None, user_id=None,
                  zipname=None):
        if data:
            return self.handle_zip(name, data, ty,
                                   user_id, project,
                                   'json', zipname)
        else:
            name = self._project_name_latin_encoded(project)
            json_task_generator = self._respond_json(ty, project.id)
            if json_task_generator is not None:
                return self.handle_zip(name, json_task_generator,
                                       ty, user_id, project, 'json', zipname)

    def download_name(self, project, ty):
        return super(JsonExporter, self).download_name(project, ty, 'json')

    def pregenerate_zip_files(self, project):
        print("%d (json)" % project.id)
        self._make_zip(project, "task")
        self._make_zip(project, "task_run")
        self._make_zip(project, "result")

    def handle_zip(self, name, data, ty, user_id, project, ext, zipname=None):
        zipped_datafile = tempfile.NamedTemporaryFile()
        _zip = self._zip_factory(zipped_datafile.name)
        try:
            datafile = tempfile.NamedTemporaryFile(mode='w')
            try:
                datafile.write(json.dumps(data))
                datafile.flush()
                _zip.write(datafile.name,
                           secure_filename('%s_%s.%s' % (name, ty, ext)))
            finally:
                datafile.close()
        finally:
            _zip.close()
            if user_id:
                container = "user_%d" % user_id
                if zipname is None:
                    zipname = "user_%s.zip" % user_id
                else:
                    zipname = "%s_sec_%s" % (uuid.uuid1(), zipname)
                _file = FileStorage(filename=zipname,
                                    stream=zipped_datafile)
            else:
                container = "user_%d" % project.owner_id
                fname = self.download_name(project, ty)
                _file = FileStorage(filename=fname,
                                    stream=zipped_datafile)
            uploader.upload_file(_file, container=container)

            if zipname and "_sec_" in zipname:
                days = current_app.config.get('TTL_ZIP_SEC_FILES', 3)
                scheduler.enqueue_in(timedelta(days=days),
                                     uploader.delete_file,
                                     zipname,
                                     container)
            zipped_datafile.close()
            return zipname
