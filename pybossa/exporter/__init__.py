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

from contextlib import closing, contextmanager
import copy
import os
import zipfile
import tempfile
import json
from pybossa.core import uploader, task_repo, result_repo
import tempfile
from pybossa.uploader import local
from unidecode import unidecode
from flask import url_for, safe_join, send_file, redirect, current_app
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flatten_json import flatten
from werkzeug.datastructures import FileStorage


@contextmanager
def make_zip_context(zip_result):
    yield zip_result
    if isinstance(zip_result, dict) and zip_result.get('delete'):
        os.remove(zip_result['filepath'])


class Exporter(object):

    """Abstract generic exporter class."""

    repositories = dict(task=[task_repo, 'filter_tasks_by'],
                        task_run=[task_repo, 'filter_task_runs_by'],
                        result=[result_repo, 'filter_by'])

    def _get_data(self, table, project_id, flat=False, info_only=False):
        """Get the data for a given table."""
        repo, query = self.repositories[table]
        data = getattr(repo, query)(project_id=project_id)
        ignore_keys = current_app.config.get('IGNORE_FLAT_KEYS') or []
        if table == 'task':
            csv_export_key = current_app.config.get('TASK_CSV_EXPORT_INFO_KEY')
        if table == 'task_run':
            csv_export_key = current_app.config.get('TASK_RUN_CSV_EXPORT_INFO_KEY')
        if table == 'result':
            csv_export_key = current_app.config.get('RESULT_CSV_EXPORT_INFO_KEY')
        if info_only:
            if flat:
                tmp = []
                for row in data:
                    inf = copy.deepcopy(row.dictize()['info'])
                    if inf and type(inf) == dict and csv_export_key and inf.get(csv_export_key):
                        inf = inf[csv_export_key]
                    new_key = '%s_id' % table
                    if inf and type(inf) == dict:
                        inf[new_key] = row.id
                        tmp.append(flatten(inf,
                                           root_keys_to_ignore=ignore_keys))
                    elif inf and type(inf) == list:
                        for datum in inf:
                            if type(datum) == dict:
                                datum[new_key] = row.id
                                tmp.append(flatten(datum,
                                                   root_keys_to_ignore=ignore_keys))
            else:
                tmp = []
                for row in data:
                    if row.dictize()['info']:
                        tmp.append(row.dictize()['info'])
                    else:
                        tmp.append({})
        else:
            if flat:
                tmp = []
                for row in data:
                    cleaned = row.dictize()
                    fav_user_ids = None
                    task_run_ids = None
                    if cleaned.get('fav_user_ids'):
                        fav_user_ids = cleaned['fav_user_ids']
                        cleaned.pop('fav_user_ids')
                    if cleaned.get('task_run_ids'):
                        task_run_ids = cleaned['task_run_ids']
                        cleaned.pop('task_run_ids')

                    cleaned = flatten(cleaned,
                                      root_keys_to_ignore=ignore_keys)

                    if fav_user_ids:
                        cleaned['fav_user_ids'] = fav_user_ids
                    if task_run_ids:
                        cleaned['task_run_ids'] = task_run_ids

                    tmp.append(cleaned)
            else:
                tmp = [row.dictize() for row in data]
        return tmp

    def _project_name_latin_encoded(self, project):
        """project short name for later HTML header usage"""
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

    def _make_zip(self, project, ty, **kwargs):
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
            assert uploader.delete_file(filename, self._container(project))

    def get_zip(self, project, ty, **kwargs):
        """Delete existing ZIP file directly from uploads directory,
        generate one on the fly and upload it."""
        filename = self.download_name(project, ty)
        self.delete_existing_zip(project, ty)
        with make_zip_context(self._make_zip(project, ty, **kwargs)) as zip_result:
            if (not zip_result) and isinstance(uploader, local.LocalUploader):
                filepath = self._download_path(project)
                zip_result = dict(filepath=safe_join(filepath, filename),
                                  filename=filename)
            if zip_result:
                res = send_file(filename_or_fp=zip_result['filepath'],
                                mimetype='application/octet-stream',
                                as_attachment=True,
                                attachment_filename=zip_result['filename'])
                return res
            else:
                return redirect(url_for('rackspace', filename=filename,
                                        container=self._container(project),
                                        _external=True))

    def response_zip(self, project, ty, **kwargs):
        return self.get_zip(project, ty, **kwargs)

    def pregenerate_zip_files(self, project):
        """Cache and generate all types (tasks and task_run) of ZIP files"""
        pass

    def _make_zipfile(self, project, obj, file_format, obj_generator, expanded=False):
        """Generate a ZIP of a certain type and upload it.

        :param project: A project object
        :param obj: The domain object to be exported
        :param file_format: The file format of the export
        :param obj_generator: A generator object containing
            the data to be written to file
        :param expanded: Boolean indicating whether or not
            relevant object metadata should be included
            in the export

        :return: The path where the .zip file is saved
        """
        name = self._project_name_latin_encoded(project)
        if obj_generator is not None:
            with tempfile.NamedTemporaryFile() as datafile:
                for line in obj_generator:
                    datafile.write(str(line))
                datafile.flush()
                obj_generator.close()

                zipped_datafile = tempfile.NamedTemporaryFile()

                with self._zip_factory(zipped_datafile.name) as _zip:
                    _zip.write(datafile.name,
                               secure_filename('{0}_{1}.{2}'
                                               .format(name, obj, file_format)))
                    _zip.content_type = 'application/zip'

                filename = self.download_name(project, obj)
                fs = FileStorage(filename=filename, stream=zipped_datafile)
                return closing(fs)
