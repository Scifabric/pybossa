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
import tempfile
from pybossa.exporter.csv_export import CsvExporter
from pybossa.core import project_repo
from pybossa.util import UnicodeWriter
from werkzeug.utils import secure_filename
from pybossa.cache.projects import get_project_report_projectdata
from pybossa.cache.users import get_project_report_userdata

class ProjectReportCsvExporter(CsvExporter):
    """Project reports exporter in CSV format"""

    def response_zip(self, project, ty):
        return super(ProjectReportCsvExporter, self).response_zip(project, ty)


    def download_name(self, project, ty):
        """Get the filename (without) path of the file which should be downloaded.
           This function does not check if this filename actually exists!"""
        validReports = ('project')

        if ty not in validReports:
            return abort(404)

        name = self._project_name_latin_encoded(project)
        filename = '%s_%s_%s_report.zip' % (str(project.id), name, ty)  # Example: 123_feynman_project_report_csv.zip
        filename = secure_filename(filename)
        return filename
    def _get_csv(self, out, writer):
        out.seek(0)
        yield out.read()

    def _respond_csv(self, ty, id):
        out = tempfile.TemporaryFile()
        writer = UnicodeWriter(out)
        empty_row = []
        p = project_repo.get(id)
        if p is not None:
            project_section = ['Project Statistics']
            project_header = ['Id', 'Name', 'Short Name', 'Total Tasks', 'First Task Submission',
                              'Last Task Submission', 'Average Time Spend Per Task', 'Task Redundancy']
            writer.writerow(project_section)
            writer.writerow(project_header)
            project_data = get_project_report_projectdata(id)
            writer.writerow(project_data)

            writer.writerow(empty_row)
            user_section = ['User Statistics']
            user_header = ['Id', 'Name', 'Fullname', 'Email', 'Admin', 'Subadmin', 'Languages',
                           'Locations', 'Start Time', 'End Time', 'Timezone', 'Type of User',
                           'Additional Comments', 'Total Tasks Completed', 'Percent Tasks Completed']
            writer.writerow(user_section)
            writer.writerow(user_header)
            try:
                users_project_data = get_project_report_userdata(id)
            except Exception:
                current_app.logger.exception('Error in get_project_report_userdata. project_id: {}'.format(id))
                raise BadRequest("Failed to obtain user Statistics")
            for user_data in users_project_data:
                writer.writerow(user_data)

            return self._get_csv(out, writer)
        else:
            def empty_csv(out):
                yield out.read()
            return empty_csv(out)

    def pregenerate_zip_files(self, project):
        self._make_zip(project, "project")
