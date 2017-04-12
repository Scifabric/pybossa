# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2017 SciFabric LTD.
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

import json
import tempfile
import uuid
import datetime
from flask import url_for, safe_join, send_file, redirect
from pybossa.uploader import local
from pybossa.exporter import Exporter
from pybossa.exporter.json_export import JsonExporter
from pybossa.core import uploader, task_repo
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from pybossa.uploader.s3_uploader import s3_upload_file_storage


class TaskJsonExporter(JsonExporter):
    """JSON Exporter for exporting ``Task``s and ``TaskRun``s
    for a project.
    """

    @staticmethod
    def merge_objects(t):
        """Merge joined objects into a single dictionary."""
        obj_dict = {}

        try:
            obj_dict = t.dictize()
        except:
            pass

        try:
            task = t.task.dictize()
            obj_dict['task'] = task
        except:
            pass

        try:
            user = t.user.dictize()
            allowed_attributes = ['name', 'fullname', 'created',
                                  'email_addr', 'admin', 'subadmin']
            user = {k: v for (k, v) in user.iteritems() if k in allowed_attributes}
            obj_dict['user'] = user
        except:
            pass

        return obj_dict

    def gen_json(self, table, id, expanded=False):
        if table == 'task':
            query_filter = task_repo.filter_tasks_by
        elif table == 'task_run':
            query_filter = task_repo.filter_task_runs_by
        else:
            return

        n = getattr(task_repo, 'count_%ss_with' % table)(project_id=id)
        sep = ", "
        yield "["

        for i, tr in enumerate(query_filter(project_id=id, yielded=True), 1):
            if expanded:
                item = self.merge_objects(tr)
            else:
                item = tr.dictize()

            item = json.dumps(item)

            if (i == n):
                sep = ""
            yield item + sep
        yield "]"

    def _respond_json(self, ty, id, expanded=False):
        return self.gen_json(ty, id, expanded)

    def response_zip(self, project, ty, expanded=False):
        return self.get_zip(project, ty, expanded)

    def get_zip(self, project, ty, expanded=False):
        """Delete existing ZIP file directly from uploads directory,
        generate one on the fly and upload it."""
        filename = self.download_name(project, ty)
        self.delete_existing_zip(project, ty)
        self._make_zip(project, ty, expanded)
        if isinstance(uploader, local.LocalUploader):
            filepath = self._download_path(project)
            res = send_file(filename_or_fp=safe_join(filepath, filename),
                            mimetype='application/octet-stream',
                            as_attachment=True,
                            attachment_filename=filename)
            # fail safe mode for more encoded filenames.
            # It seems Flask and Werkzeug do not support RFC 5987
            # http://greenbytes.de/tech/tc2231/#encoding-2231-char
            # res.headers['Content-Disposition'] = 'attachment; filename*=%s' % filename
            return res
        else:
            return redirect(url_for('rackspace', filename=filename,
                                    container=self._container(project),
                                    _external=True))

    def _make_zip(self, project, obj, expanded=False):
        file_format = 'json'
        obj_generator = self._respond_json(obj, project.id, expanded)
        self._make_zipfile(
                project, obj, file_format, obj_generator, expanded)

    def export_zip_to_s3(self, project, ty, expanded=False):
        """Create a zip file and export it to S3.

        Returns the URL where the file was saved.
        """
        name = self._project_name_latin_encoded(project)
        json_task_generator = self._respond_json(ty, project.id, expanded)
        if json_task_generator is not None:
            datafile = tempfile.NamedTemporaryFile()
            try:
                for line in json_task_generator:
                    datafile.write(str(line))
                datafile.flush()
                zipped_datafile = tempfile.NamedTemporaryFile()
                try:
                    filedate = datetime.date.strftime(datetime.date.today(), '%Y%m%d')
                    fileuuid = uuid.uuid4().hex
                    _zip = self._zip_factory(zipped_datafile.name)
                    _zip.write(datafile.name,
                               secure_filename('{0}_{1}_{2}_{3}.csv'.format(name,
                                                                            ty,
                                                                            filedate,
                                                                            fileuuid)))
                    _zip.content_type = 'application/zip'
                    _zip.close()

                    zip_file = FileStorage(filename=self.download_name_randomized(project, ty),
                                           stream=zipped_datafile)
                    url = s3_upload_file_storage(source_file=zip_file,
                                                 directory='',
                                                 public=True)
                finally:
                    zipped_datafile.close()
            finally:
                datafile.close()

        try:
            return url
        except:
            return

    def download_name_randomized(self, project, ty):
        return super(TaskJsonExporter, self).download_name_randomized(project, ty, 'json')
