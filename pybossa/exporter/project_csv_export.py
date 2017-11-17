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
from pybossa.core import uploader, project_repo, user_repo
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from pybossa.cache.helpers import n_available_tasks
import pandas as pd
from collections import OrderedDict


class ProjectCsvExporter(CsvExporter):

    def get_projects_report(self, base_url):
        results = project_repo.get_projects_report()
        projects = []

        for row in results:
            owners_ids = project_repo.get_by_shortname(row.short_name).owners_ids
            coowners = (co for co in user_repo.get_users(owners_ids)
                        if co.name != row.owner_name)
            num_available_tasks = n_available_tasks(row.id)
            coowner_names = '|'.join('{};{}'.format(co.name, co.email_addr)
                                     for co in coowners)
            if not coowner_names:
                coowner_names = 'None'
            has_completed = str(num_available_tasks == 0)
            project = OrderedDict([
                ('id', row.id),
                ('name', row.name),
                ('short_name', row.short_name),
                ('url', base_url + row.short_name),
                ('description', row.description),
                ('long_description', row.long_description),
                ('created', row.created),
                ('owner_name', row.owner_name),
                ('owner_email', row.owner_email),
                ('coowners', coowner_names),
                ('category_name', row.category_name),
                ('allow_anonymous_contributors', row.allow_anonymous_contributors),
                ('password_protected', row.password_protected),
                ('webhook', row.webhook),
                ('scheduler', row.scheduler),
                ('has_completed', has_completed),
                ('finish_time', row.ft),
                ('percent_complete', row.percent_complete),
                ('n_tasks', row.n_tasks),
                ('pending_tasks', row.pending_tasks),
                ('n_workers', row.n_workers),
                ('n_answers', row.n_answers),
                ('workers', row.workers)])

            projects.append(project)
        return pd.DataFrame(projects)

    def _make_zip(self, info):
        name = self.download_name(info)
        dataframe = self.get_projects_report(info['base_url'])
        if dataframe is not None:
            datafile = tempfile.NamedTemporaryFile()
            try:
                dataframe.to_csv(datafile, index=False,
                                 encoding='utf-8')
                datafile.flush()
                zipped_datafile = tempfile.NamedTemporaryFile()
                try:
                    _zip = self._zip_factory(zipped_datafile.name)
                    _zip.write(
                        datafile.name, secure_filename('{}.csv'.format(name)))
                    _zip.close()
                    container = "user_%d" % info['user_id']
                    _file = FileStorage(
                        filename=self.zip_name(info), stream=zipped_datafile)
                    uploader.upload_file(_file, container=container)
                finally:
                    zipped_datafile.close()
            finally:
                datafile.close()

    def zip_name(self, info):
        return secure_filename('{}.zip'.format(self.download_name(info)))

    def download_name(self, info):
        return '{}_projects'.format(info['timestamp'])

    def pregenerate_zip_files(self, info):
        self._make_zip(info)
