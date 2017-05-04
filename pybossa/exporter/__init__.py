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
Exporter module for exporting tasks and tasks results out of PYBOSSA
"""

import os
import zipfile
from pybossa.core import uploader, task_repo, result_repo
import tempfile
from pybossa.uploader import local
from unidecode import unidecode
from flask import url_for, safe_join, send_file, redirect
from flask import current_app as app
from werkzeug.utils import secure_filename
from flatten_json import flatten
from werkzeug.datastructures import FileStorage


class Exporter(object):

    """Abstract generic exporter class."""

    repositories = dict(task=[task_repo, 'filter_tasks_by'],
                        task_run=[task_repo, 'filter_task_runs_by'],
                        result=[result_repo, 'filter_by'])

    def _get_data(self, table, project_id, flat=False, info_only=False):
        """Get the data for a given table."""
        repo, query = self.repositories[table]
        data = getattr(repo, query)(project_id=project_id)
        if info_only:
            if flat:
                tmp = []
                for row in data:
                    inf = row.dictize()['info']
                    if inf and type(inf) == dict:
                        tmp.append(flatten(inf))
                    else:
                        tmp.append({'info': inf})
            else:
                tmp = []
                for row in data:
                    if row.dictize()['info']:
                        tmp.append(row.dictize()['info'])
                    else:
                        tmp.append({})
        else:
            if flat:
                tmp = [flatten(row.dictize()) for row in data]
            else:
                tmp = [row.dictize() for row in data]
        return tmp

    def _project_name_latin_encoded(self, project):
        """project short name for later HTML header usage"""
        # name = project.short_name.encode('utf-8', 'ignore').decode('latin-1')
        name = unidecode(project.short_name)
        return name

    def _zip_factory(self, filename):
        """create a ZipFile Object with compression and allow big ZIP files (allowZip64)"""
        try:
            import zlib
            assert zlib
            zip_compression= zipfile.ZIP_DEFLATED
        except Exception as ex:
            zip_compression= zipfile.ZIP_STORED
        _zip = zipfile.ZipFile(file=filename, mode='w', compression=zip_compression, allowZip64=True)
        return _zip

    def _make_zip(self, project, ty):
        """Generate a ZIP of a certain type and upload it"""
        pass

    def _container(self, project):
        return "user_%d" % project.owner_id

    def _download_path(self, project):
        container = self._container(project)
        if isinstance(uploader, local.LocalUploader):
            filepath = safe_join(uploader.upload_folder, container)
        else:
            print("The method Exporter _download_path should not be used for Rackspace etc.!")  # TODO: Log this stuff
            filepath = container
        return filepath

    def download_name(self, project, ty, _format):
        """Get the filename (without) path of the file which should be downloaded.
           This function does not check if this filename actually exists!"""
        # TODO: Check if ty is valid
        name = self._project_name_latin_encoded(project)
        filename = '%s_%s_%s_%s.zip' % (str(project.id), name, ty, _format)  # Example: 123_feynman_tasks_json.zip
        filename = secure_filename(filename)
        return filename

    def zip_existing(self, project, ty):
        """Check if exported ZIP is existing"""
        # TODO: Check ty
        filename = self.download_name(project, ty)
        return uploader.file_exists(filename, self._container(project))

    def delete_existing_zip(self, project, ty):
        """Delete existing ZIP from uploads directory"""
        filename = self.download_name(project, ty)
        if uploader.file_exists(filename, self._container(project)):
            uploader.delete_file(filename, self._container(project))

    def get_zip(self, project, ty):
        """Delete existing ZIP file directly from uploads directory,
        generate one on the fly and upload it."""
        filename = self.download_name(project, ty)
        self.delete_existing_zip(project, ty)
        self._make_zip(project, ty)
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

    def response_zip(self, project, ty):
        return self.get_zip(project, ty)

    def pregenerate_zip_files(self, project):
        """Cache and generate all types (tasks and task_run) of ZIP files"""
        pass

    def _make_zipfile(self, project, ty, _format, _task_generator, expanded=False):
        """Generate a ZIP of a certain type and upload it"""
        name = self._project_name_latin_encoded(project)
        if _task_generator is not None:

           # Write data to file
            datafile = tempfile.NamedTemporaryFile()
            try:
                for line in _task_generator:
                    datafile.write(str(line))
                datafile.flush()
                _task_generator.close()
            except Exception as e:
                app.logger.exception(
                        'File Writing Failed - Project: {0}, Type: {1}, Format: {2} - Error: {3}'
                        .format(project.short_name, ty, _format, e))

            # Create .zip archive
            zipped_datafile = tempfile.NamedTemporaryFile()
            try:
                _zip = self._zip_factory(zipped_datafile.name)
                _zip.write(
                    datafile.name,
                    secure_filename('{0}_{1}.{2}'.format(name, ty, _format)))
                _zip.close()
                container = "user_%d" % project.owner_id
                _file = FileStorage(
                    filename=self.download_name(project, ty), stream=zipped_datafile)
            except Exception as e:
                app.logger.exception(
                        '.zip Creation Failed - Project: {0}, Type: {1}, Format: {2} - Error: {3}'
                        .format(project.short_name, ty, _format, e))

            # Upload data
            try:
                uploader.upload_file(_file, container=container)
            except Exception as e:
                app.logger.exception(
                        'File Upload Failed - Project: {0}, Type: {1}, Format: {2} - Error: {3}'
                        .format(project.short_name, ty, _format, e))
            finally:
                zipped_datafile.close()
                datafile.close()
