# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
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
Exporter module for exporting tasks and tasks results out of PyBossa
"""

import json
import tempfile
import zipfile
from StringIO import StringIO
from pybossa.core import db, uploader
# from pybossa.core import create_app
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from flask.ext.babel import gettext
from pybossa.util import UnicodeWriter
import pybossa.model as model
from werkzeug.datastructures import FileStorage

class Exporter(object):

    """Generic exporter class."""

    def __init__(self, app):
        """Init method to create a generic uploader."""
        self.app = app

    def _gen_json(self, table, id):
        n = db.slave_session.query(table)\
            .filter_by(app_id=id).count()
        sep = ", "
        yield "["
        for i, tr in enumerate(db.slave_session.query(table)
                                 .filter_by(app_id=id).yield_per(1), 1):
            item = json.dumps(tr.dictize())
            if (i == n):
                sep = ""
            yield item + sep
        yield "]"

    def _respond_json(self, ty, id):
        tables = {"task": model.task.Task, "task_run": model.task_run.TaskRun}
        try:
            table = tables[ty]
        except KeyError:
            print("key error")  # TODO

        return self._gen_json(table, id)

    def _format_csv_properly(self, row, ty=None):
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
            prefix, k = k.split("__")
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

    def _handle_task(self, writer, t):
        writer.writerow(self._format_csv_properly(t.dictize(), ty='task'))

    def _handle_task_run(self, writer, t):
        writer.writerow(self._format_csv_properly(t.dictize(), ty='taskrun'))

    def _get_csv(self, out, writer, table, handle_row, id):
        for tr in db.slave_session.query(table)\
                .filter_by(app_id=id)\
                .yield_per(1):
            handle_row(writer, tr)
        yield out.getvalue()

    def respond_csv(self, ty, id):
        try:
            # Export Task(/Runs) to CSV
            types = {
                "task": (
                    model.task.Task, self._handle_task,
                    (lambda x: True),
                    gettext(
                        "Oops, the project does not have tasks to \
                        export, if you are the owner add some tasks")),
                "task_run": (
                    model.task_run.TaskRun, self._handle_task_run,
                    (lambda x: True),
                    gettext(
                        "Oops, there are no Task Runs yet to export, invite \
                         some users to participate"))}
            try:
                table, handle_row, test, msg = types[ty]
            except KeyError:
                print "KeyError" # TODO

            out = StringIO()
            writer = UnicodeWriter(out)
            t = db.slave_session.query(table)\
                .filter_by(app_id=id)\
                .first()
            if t is not None:
                if test(t):
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
                    writer.writerow(sorted(keys))

                return self._get_csv(out, writer, table, handle_row, id)
            else:
                pass # TODO
        except: # pragma: no cover
            raise

    def _zip_factory(self, filename):
        try:
            import zlib
            zip_compression= zipfile.ZIP_DEFLATED
        except:
            zip_compression= zipfile.ZIP_STORED
        zip = zipfile.ZipFile(file=filename, mode='w', compression=zip_compression, allowZip64=True)
        return zip

    def export_json(self, app):
        print "%d (json)" % app.id
        name = app.short_name.encode('utf-8', 'ignore').decode('latin-1') # used for latin filename later
        json_task_generator = self._respond_json("task", app.id)
        if json_task_generator is not None:
            datafile = tempfile.NamedTemporaryFile()
            try:
                for line in json_task_generator:
                    datafile.write(str(line))
                datafile.flush()
                zipped_datafile = tempfile.NamedTemporaryFile()
                try:
                    zip = self._zip_factory(zipped_datafile.name)
                    zip.write(datafile.name, '%s_task.json' % name)
                    zip.close()
                    container = "user_%d" % app.owner_id
                    file = FileStorage(filename='%s_task_json.zip' % name, stream=zipped_datafile)
                    uploader.upload_file(file, container=container)
                finally:
                    zipped_datafile.close()
            finally:
                datafile.close()
        json_task_run_generator = self._respond_json("task_run", app.id)
        if json_task_run_generator is not None:
            datafile = tempfile.NamedTemporaryFile()
            try:
                for line in json_task_run_generator:
                    datafile.write(str(line))
                datafile.flush()
                zipped_datafile = tempfile.NamedTemporaryFile()
                try:
                    zip = self._zip_factory(zipped_datafile.name)
                    zip.write(datafile.name, '%s_task_run.json' % name)
                    zip.close()
                    container = "user_%d" % app.owner_id
                    file = FileStorage(filename='%s_task_run_json.zip' % name, stream=zipped_datafile)
                    uploader.upload_file(file, container=container)
                finally:
                    zipped_datafile.close()
            finally:
                datafile.close()

    def export_csv(self, app):
        print "%d (csv)" % app.id
        name = app.short_name.encode('utf-8', 'ignore').decode('latin-1') # used for latin filename later
        csv_task_generator = self.respond_csv("task", app.id)
        if csv_task_generator is not None:
            datafile = tempfile.NamedTemporaryFile()
            try:
                for line in csv_task_generator:
                    datafile.write(str(line))
                datafile.flush()
                zipped_datafile = tempfile.NamedTemporaryFile()
                try:
                    zip = self._zip_factory(zipped_datafile.name)
                    zip.write(datafile.name, '%s_task.csv' % name)
                    zip.close()
                    container = "user_%d" % app.owner_id
                    file = FileStorage(filename='%s_task_csv.zip' % name, stream=zipped_datafile)
                    uploader.upload_file(file, container=container)
                finally:
                    zipped_datafile.close()
            finally:
                datafile.close()
        csv_task_run_generator = self.respond_csv("task_run", app.id)
        if csv_task_run_generator is not None:
            datafile = tempfile.NamedTemporaryFile()
            try:
                for line in csv_task_run_generator:
                    datafile.write(str(line))
                datafile.flush()
                zipped_datafile = tempfile.NamedTemporaryFile()
                try:
                    zip = self._zip_factory(zipped_datafile.name)
                    zip.write(datafile.name, '%s_task_run.csv' % name)
                    zip.close()
                    container = "user_%d" % app.owner_id
                    file = FileStorage(filename='%s_task_run_csv.zip' % name, stream=zipped_datafile)
                    uploader.upload_file(file, container=container)
                finally:
                    zipped_datafile.close()
            finally:
                datafile.close()
