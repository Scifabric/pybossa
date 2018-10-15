# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
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
CSV Exporter module for exporting tasks and tasks results out of PyBossa
"""

import tempfile
from pybossa.exporter.csv_export import CsvExporter
from pybossa.core import project_repo, user_repo
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from pybossa.cache.helpers import n_available_tasks
import pandas as pd
from collections import OrderedDict


class ProjectCsvExporter(CsvExporter):

    def get_projects_report(self, base_url):
        projects = project_repo.get_projects_report(base_url)
        return projects

    def _make_zip(self, info):
        name = self.download_name(info)
        dataframe = self.get_projects_report(info['base_url'])
        if dataframe is not None:
            datafile = tempfile.NamedTemporaryFile()
            try:
                dataframe.to_csv(datafile, index=False,
                                 encoding='utf-8')
                datafile.flush()
                zipped_datafile = tempfile.NamedTemporaryFile(delete=False)
                try:
                    _zip = self._zip_factory(zipped_datafile.name)
                    _zip.write(
                        datafile.name, secure_filename('{}.csv'.format(name)))
                    _zip.close()
                    container = "user_%d" % info['user_id']
                    return zipped_datafile.name
                finally:
                    zipped_datafile.close()
            finally:
                datafile.close()

    def zip_name(self, info):
        return secure_filename('{}.zip'.format(self.download_name(info)))

    def download_name(self, info):
        return '{}_projects'.format(info['timestamp'])

    def generate_zip_files(self, info):
        return self._make_zip(info)
