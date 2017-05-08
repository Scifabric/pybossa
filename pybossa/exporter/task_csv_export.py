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
from pybossa.uploader import local
from pybossa.exporter.csv_export import CsvExporter
from pybossa.core import uploader, task_repo
from pybossa.util import UnicodeWriter
from flask import url_for, safe_join, send_file, redirect


class TaskCsvExporter(CsvExporter):
    """CSV Exporter for exporting ``Task``s and ``TaskRun``s
    for a project.
    """

    @classmethod
    def get_keys(self, row, ty, parent_key=''):
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
            >>> sorted(exp.get_keys(row, 'taskrun'))
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
                keys = keys + self.get_keys(row[key], _prefix + key)
            except: pass

        return [str(key) for key in keys]

    @classmethod
    def get_value(self, row, *args):
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
            >>> exp.get_value(row, *['c', 'nested_y', 'double_nested'])
            'www.example.com'
        """
        while len(args) > 0:
            for arg in args:
                try:
                    args = args[1:]
                    return self.get_value(row[arg], *args)
                except:
                    return None
        return str(row)

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

    def _format_csv_row(self, row, ty, headers):
        return [self.get_value(row, *header.split('__')[1:])
                for header in headers]

    def _handle_row(self, writer, t, ty, headers):
        normal_ty = filter(lambda char: char.isalpha(), ty)
        writer.writerow(self._format_csv_row(self.merge_objects(t),
                                             ty=normal_ty,
                                             headers=headers))

    def _get_csv(self, out, writer, table, id, expanded=False):
        if table == 'task':
            query_filter = task_repo.filter_tasks_by
        elif table == 'task_run':
            query_filter = task_repo.filter_task_runs_by
        else:
            return

        objs = query_filter(project_id=id, yielded=True)
        headers = self._get_all_headers(objs, expanded)
        writer.writerow(headers)

        for obj in objs:
            self._handle_row(writer, obj, table, headers)
        out.seek(0)
        yield out.read()

    def _get_all_headers(self, objs, expanded):
        """Construct headers to **guarantee** that all headers
        for all tasks are included, regardless of whether
        or not all tasks were imported with the same headers.
        """
        obj_name = objs[0].__class__.__name__.lower()
        headers = set()

        for obj in objs:
            headers.update(self._get_headers_from_row(obj, obj_name, expanded))

        headers = sorted(list(headers))
        return headers

    def _get_headers_from_row(self, obj, obj_name, expanded):
        if expanded:
            obj_dict = self.merge_objects(obj)
        else:
            obj_dict = obj.dictize()

        headers = self.get_keys(obj_dict, obj_name)
        return headers

    def _respond_csv(self, ty, id, expanded=False):
        out = tempfile.TemporaryFile()
        writer = UnicodeWriter(out)

        try:
            return self._get_csv(out, writer, ty, id, expanded)
        except:
            def empty_csv(out):
                yield out.read()
            return empty_csv(out)

    def response_zip(self, project, ty, expanded=False):
        return self.get_zip(project, ty, expanded)

    def get_zip(self, project, ty, expanded=False):
        """Delete existing ZIP file directly from uploads directory,
        generate one on the fly and upload it.
        """
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
        file_format = 'csv'
        obj_generator = self._respond_csv(obj, project.id, expanded)
        self._make_zipfile(
                project, obj, file_format, obj_generator, expanded)
