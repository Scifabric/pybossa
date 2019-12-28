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
CSV Exporter module for exporting tasks and tasks results out of PYBOSSA
"""

import tempfile
from pybossa.exporter import Exporter
from pybossa.core import uploader, task_repo
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
import pandas as pd


class CsvExporter(Exporter):

    def _respond_csv(self, table, project_id, info_only=False):
        flat_data = self._get_data(table, project_id,
                                   flat=True, info_only=info_only)
        return pd.DataFrame(flat_data)

    def _make_zip(self, project, ty):
        name = self._project_name_latin_encoded(project)
        dataframe = self._respond_csv(ty, project.id)
        if dataframe is not None:
            info_dataframe = self._respond_csv(ty, project.id, info_only=True)
            datafile = tempfile.NamedTemporaryFile(mode='w')
            info_datafile = tempfile.NamedTemporaryFile(mode='w')
            try:
                dataframe.to_csv(
                    datafile, index=False, encoding='utf-8')
                info_dataframe.to_csv(
                    info_datafile, index=False, encoding='utf-8')
                datafile.flush()
                info_datafile.flush()
                zipped_datafile = tempfile.NamedTemporaryFile()
                try:
                    _zip = self._zip_factory(zipped_datafile.name)
                    _zip.write(
                        datafile.name, secure_filename('%s_%s.csv' % (name, ty)))
                    _zip.write(
                        info_datafile.name, secure_filename('%s_%s_info_only.csv' % (name, ty)))
                    _zip.close()
                    container = "user_%d" % project.owner_id
                    _file = FileStorage(
                        filename=self.download_name(project, ty), stream=zipped_datafile)
                    uploader.upload_file(_file, container=container)
                finally:
                    zipped_datafile.close()
            finally:
                datafile.close()
                info_datafile.close()

    def download_name(self, project, ty):
        return super(CsvExporter, self).download_name(project, ty, 'csv')

    def pregenerate_zip_files(self, project):
        print("%d (csv)" % project.id)
        self._make_zip(project, "task")
        self._make_zip(project, "task_run")
        self._make_zip(project, "result")
