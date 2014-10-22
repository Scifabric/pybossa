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

#!/usr/bin/env python
import os
import sys
import optparse
import inspect
import json
from StringIO import StringIO
import zipfile
from pybossa.core import db, uploader
from pybossa.core import create_app
from pybossa.model.app import App
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from flask.ext.babel import gettext
from pybossa.util import UnicodeWriter
import pybossa.model as model

app = create_app()

def export_tasks():
    '''Export tasks to zip'''

    def gen_json(table, id):
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

    def respond_json(ty, id):
        tables = {"task": model.task.Task, "task_run": model.task_run.TaskRun}
        try:
            table = tables[ty]
        except KeyError:
            print("key error")  # TODO

        return gen_json(table, id)

    def format_csv_properly(row, ty=None):
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

    def handle_task(writer, t):
        writer.writerow(format_csv_properly(t.dictize(), ty='task'))

    def handle_task_run(writer, t):
        writer.writerow(format_csv_properly(t.dictize(), ty='taskrun'))

    def get_csv(out, writer, table, handle_row, id):
        for tr in db.slave_session.query(table)\
                .filter_by(app_id=id)\
                .yield_per(1):
            handle_row(writer, tr)
            yield out.getvalue()

    def respond_csv(ty, id):
        try:
            # Export Task(/Runs) to CSV
            types = {
                "task": (
                    model.task.Task, handle_task,
                    (lambda x: True),
                    gettext(
                        "Oops, the project does not have tasks to \
                        export, if you are the owner add some tasks")),
                "task_run": (
                    model.task_run.TaskRun, handle_task_run,
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

                return get_csv(out, writer, table, handle_row, id)
            else:
                pass # TODO
        except: # pragma: no cover
            raise

    def make_onefile_memzip(memfile, filename):
        memzip = StringIO()
        try:
            import zlib
            mode= zipfile.ZIP_DEFLATED
        except:
            mode= zipfile.ZIP_STORED
        zipf = zipfile.ZipFile(memzip, 'w', mode)
        memfile.seek(0)
        zipf.writestr(filename, memfile.getvalue())
        zipf.close()
        memzip.seek(0)
        return memzip

    def export_json(app):
        print app.id
        name = app.short_name.encode('utf-8', 'ignore').decode('latin-1') # used for latin filename later
        json_task_generator = respond_json("task", app.id)
        if json_task_generator is not None:
            memfile = StringIO()
            for line in json_task_generator:
                memfile.write(str(line))
            memzip = make_onefile_memzip(memfile, '%s_task.json' % name)
            # TODO: use pybossa uploader! Only for debugging:
            open('/tmp/%d_%s_task_json.zip' % (app.id, name), 'wb').write(memzip.getvalue())
        json_task_run_generator = respond_json("task_run", app.id)
        if json_task_run_generator is not None:
            memfile = StringIO()
            for line in json_task_run_generator:
                memfile.write(str(line))
            memzip = make_onefile_memzip(memfile, '%s_task_run.json' % name)
            # TODO: use pybossa uploader! Only for debugging:
            open('/tmp/%d_%s_task_run_json.zip' % (app.id, name), 'wb').write(memzip.getvalue())


    def export_csv(app):
        print app.id
        name = app.short_name.encode('utf-8', 'ignore').decode('latin-1') # used for latin filename later
        csv_task_generator = respond_csv("task", app.id)
        if csv_task_generator is not None:
            memfile = StringIO()
            for line in csv_task_generator:
                memfile.write(str(line))
            memzip = make_onefile_memzip(memfile, '%s_task.csv' % name)
            # TODO: use pybossa uploader! Only for debugging:
            open('/tmp/%d_%s_task_csv.zip' % (app.id, name), 'wb').write(memzip.getvalue())
        csv_task_run_generator = respond_csv("task_run", app.id)
        if csv_task_run_generator is not None:
            memfile = StringIO()
            for line in csv_task_run_generator:
                memfile.write(str(line))
            memzip = make_onefile_memzip(memfile, '%s_task_run.csv' % name)
            # TODO: use pybossa uploader! Only for debugging:
            open('/tmp/%d_%s_task_run_csv.zip' % (app.id, name), 'wb').write(memzip.getvalue())

    # go through all apps and generate json and csv

    apps = db.slave_session.query(App).all()

    # Test only with first
    # export_json(apps[0])
    # export_csv(apps[0])

    for app_x in apps:
        export_json(app_x)
        export_csv(app_x)


## ==================================================
## Misc stuff for setting up a command line interface

def _module_functions(functions):
    local_functions = dict(functions)
    for k,v in local_functions.items():
        if not inspect.isfunction(v) or k.startswith('_'):
            del local_functions[k]
    return local_functions

def _main(functions_or_object):
    isobject = inspect.isclass(functions_or_object)
    if isobject:
        _methods = _object_methods(functions_or_object)
    else:
        _methods = _module_functions(functions_or_object)

    usage = '''%prog {action}

Actions:
    '''
    usage += '\n    '.join(
        [ '%s: %s' % (name, m.__doc__.split('\n')[0] if m.__doc__ else '') for (name,m)
        in sorted(_methods.items()) ])
    parser = optparse.OptionParser(usage)
    # Optional: for a config file
    # parser.add_option('-c', '--config', dest='config',
    #         help='Config file to use.')
    options, args = parser.parse_args()

    if not args or not args[0] in _methods:
        parser.print_help()
        sys.exit(1)

    method = args[0]
    if isobject:
        getattr(functions_or_object(), method)(*args[1:])
    else:
        _methods[method](*args[1:])

__all__ = [ '_main' ]

if __name__ == '__main__':
    _main(locals())
