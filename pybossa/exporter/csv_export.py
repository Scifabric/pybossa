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
from pybossa.util import UnicodeWriter
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
import pandas as pd


class CsvExporter(Exporter):

    def _respond_csv(self, table, project_id, info_only=False):
        flat_data = self._get_data(table, project_id,
                                   flat=True, info_only=info_only)
        return pd.DataFrame(flat_data)

    def _format_csv_row(self, row, ty):
        tmp = row.keys()
        task_keys = []
        for k in tmp:
            k = "%s__%s" % (ty, k)
            task_keys.append(k)
        if (type(row['info']) == dict):
            task_info_keys = []
            tmp = row['info'].keys()
            for k in tmp:
                k = "%sinfo__%s" % (ty, k)
                task_info_keys.append(k)
        else:
            task_info_keys = []

        keys = sorted(task_keys + task_info_keys)
        values = []
        _prefix = "%sinfo" % ty
        for k in keys:
            prefix, k = k.split("__", 1)
            if prefix == _prefix:
                if row['info'].get(k) is not None:
                    values.append(row['info'][k])
                else:
                    values.append(None)
            else:
                if row.get(k) is not None:
                    values.append(row[k])
                else:
                    values.append(None)

        return values

    @classmethod
    def _get_keys(self, row, ty, parent_key=''):
        """Recursively get keys from a dictionary.
        Nested keys are prefixed with their parents key.

        Ex:
            >>> row = {"a": {"nested_x": "N"},
            ...        "b": 1,
            ...        "c": {
            ...          "nested_y": {"double_nested": "www.example.com"},
            ...          "nested_z": True
            ...       }}
            >>> exp = CsvExporter()
            >>> sorted(exp._get_keys(row, 'taskrun'))
            ['taskrun__a',
             'taskrun__a__nested_x',
             'taskrun__b',
             'taskrun__c',
             'taskrun__c__nested_y',
             'taskrun__c__nested_y__double_nested',
             'taskrun__c__nested_z']

        """
        _prefix = '{}__{}'.format(ty, parent_key)
        keys = []

        for key in row.keys():
            keys = keys + [_prefix + key]
            try:
                keys = keys + self._get_keys(row[key], _prefix + key)
            except: pass

        return [str(key) for key in keys]

    @classmethod
    def _get_value(self, row, *args):
        """Recursively get value from a dictionary by
        passing an arbitrarily long list of nested keys.

        Ex:
            >>> row = {"a": {"nested_x": "N"},
            ...        "b": 1,
            ...        "c": {
            ...          "nested_y": {"double_nested": "www.example.com"},
            ...          "nested_z": True
            ...       }}
            >>> exp = CsvExporter()
            >>> exp._get_value(row, *['c', 'nested_y', 'double_nested'])
            'www.example.com'

        """
        while len(args) > 0:
            for arg in args:
                try:
                    args = args[1:]
                    return self._get_value(row[arg], *args)
                except:
                    return None
        return str(row)

    def _handle_row(self, writer, t, ty):
        normal_ty = filter(lambda char: char.isalpha(), ty)
        writer.writerow(self._format_csv_row(t.dictize(), ty=normal_ty))

    def _get_csv(self, out, writer, table, id):
        for tr in getattr(task_repo, 'filter_%ss_by' % table)(project_id=id,
                                                              yielded=True):
            self._handle_row(writer, tr, table)
        out.seek(0)
        yield out.read()

    def _format_headers(self, t, ty):
        tmp = t.dictize().keys()
        task_keys = []
        for k in tmp:
            k = "%s__%s" % (ty, k)
            task_keys.append(k)
        if (type(t.info) == dict):
            task_info_keys = []
            tmp = t.info.keys()
            for k in tmp:
                k = "%sinfo__%s" % (ty, k)
                task_info_keys.append(k)
        else:
            task_info_keys = []
        keys = task_keys + task_info_keys
        return sorted(keys)

    def _make_zip(self, project, ty):
        name = self._project_name_latin_encoded(project)
        dataframe = self._respond_csv(ty, project.id)
        if dataframe is not None:
            info_dataframe = self._respond_csv(ty, project.id, info_only=True)
            datafile = tempfile.NamedTemporaryFile()
            info_datafile = tempfile.NamedTemporaryFile()
            try:
                dataframe.to_csv(datafile, index=False,
                                 encoding='utf-8')
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
        print "%d (csv)" % project.id
        self._make_zip(project, "task")
        self._make_zip(project, "task_run")
        self._make_zip(project, "result")
