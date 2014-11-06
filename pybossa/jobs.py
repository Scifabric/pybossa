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

import os

def get_all_jobs():
    return [warm_up_stats, export_tasks]

def export_tasks():
    '''Export tasks to zip'''

    import json
    import tempfile
    import zipfile
    from StringIO import StringIO
    from pybossa.core import db, uploader
    from pybossa.core import create_app
    from pybossa.model.app import App
    from pybossa.model.task import Task
    from pybossa.model.task_run import TaskRun
    from flask.ext.babel import gettext
    from pybossa.util import UnicodeWriter
    import pybossa.model as model
    from werkzeug.datastructures import FileStorage

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

    def zip_factory(filename):
        try:
            import zlib
            zip_compression= zipfile.ZIP_DEFLATED
        except:
            zip_compression= zipfile.ZIP_STORED
        zip = zipfile.ZipFile(file=filename, mode='w', compression=zip_compression, allowZip64=True)
        return zip

    def export_json(app):
        print "%d (json)" % app.id
        name = app.short_name.encode('utf-8', 'ignore').decode('latin-1') # used for latin filename later
        json_task_generator = respond_json("task", app.id)
        if json_task_generator is not None:
            datafile = tempfile.NamedTemporaryFile()
            try:
                for line in json_task_generator:
                    datafile.write(str(line))
                datafile.flush()
                zipped_datafile = tempfile.NamedTemporaryFile()
                try:
                    zip = zip_factory(zipped_datafile.name)
                    zip.write(datafile.name, '%s_task.json' % name)
                    zip.close()
                    file = FileStorage(filename='%d_%s_task_json.zip' % (app.id, name), stream=zipped_datafile)
                    uploader.upload_file(file, container='export') # TODO: right container folder?!
                finally:
                    zipped_datafile.close()
            finally:
                datafile.close()
        json_task_run_generator = respond_json("task_run", app.id)
        if json_task_run_generator is not None:
            datafile = tempfile.NamedTemporaryFile()
            try:
                for line in json_task_run_generator:
                    datafile.write(str(line))
                datafile.flush()
                zipped_datafile = tempfile.NamedTemporaryFile()
                try:
                    zip = zip_factory(zipped_datafile.name)
                    zip.write(datafile.name, '%s_task_run.json' % name)
                    zip.close()
                    file = FileStorage(filename='%d_%s_task_run_json.zip' % (app.id, name), stream=zipped_datafile)
                    uploader.upload_file(file, container='export') # TODO: right container folder?!
                finally:
                    zipped_datafile.close()
            finally:
                datafile.close()


    def export_csv(app):
        print "%d (csv)" % app.id
        name = app.short_name.encode('utf-8', 'ignore').decode('latin-1') # used for latin filename later
        csv_task_generator = respond_csv("task", app.id)
        if csv_task_generator is not None:
            datafile = tempfile.NamedTemporaryFile()
            try:
                for line in csv_task_generator:
                    datafile.write(str(line))
                datafile.flush()
                zipped_datafile = tempfile.NamedTemporaryFile()
                try:
                    zip = zip_factory(zipped_datafile.name)
                    zip.write(datafile.name, '%s_task.csv' % name)
                    zip.close()
                    file = FileStorage(filename='%d_%s_task_csv.zip' % (app.id, name), stream=zipped_datafile)
                    uploader.upload_file(file, container='export') # TODO: right container folder?!
                finally:
                    zipped_datafile.close()
            finally:
                datafile.close()
        csv_task_run_generator = respond_csv("task_run", app.id)
        if csv_task_run_generator is not None:
            datafile = tempfile.NamedTemporaryFile()
            try:
                for line in csv_task_run_generator:
                    datafile.write(str(line))
                datafile.flush()
                zipped_datafile = tempfile.NamedTemporaryFile()
                try:
                    zip = zip_factory(zipped_datafile.name)
                    zip.write(datafile.name, '%s_task_run.csv' % name)
                    zip.close()
                    file = FileStorage(filename='%d_%s_task_run_csv.zip' % (app.id, name), stream=zipped_datafile)
                    uploader.upload_file(file, container='export') # TODO: right container folder?!
                finally:
                    zipped_datafile.close()
            finally:
                datafile.close()

    print "Running on the background export tasks ZIPs"

    # go through all apps and generate json and csv
    app = create_app(run_as_server=False)
    apps = db.slave_session.query(App).all()

    # Test only with first
    # export_json(apps[0])
    # export_csv(apps[0])

    for app_x in apps:
        export_json(app_x)
        export_csv(app_x)


def warm_up_stats():
    print "Running on the background warm_up_stats"
    from pybossa.cache.site_stats import (n_auth_users, n_anon_users,
        n_tasks_site, n_total_tasks_site, n_task_runs_site,
        get_top5_apps_24_hours, get_top5_users_24_hours, get_locs)

    env_cache_disabled = os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED')
    if not env_cache_disabled:
        os.environ['PYBOSSA_REDIS_CACHE_DISABLED'] = '1'

    n_auth_users()
    n_anon_users()
    n_tasks_site()
    n_total_tasks_site()
    n_task_runs_site()
    get_top5_apps_24_hours()
    get_top5_users_24_hours()
    get_locs()

    if env_cache_disabled is None:
        del os.environ['PYBOSSA_REDIS_CACHE_DISABLED']
    else:
        os.environ['PYBOSSA_REDIS_CACHE_DISABLED'] = env_cache_disabled

    return True


def warm_cache():
    '''Warm cache'''
    from pybossa.core import create_app
    app = create_app(run_as_server=False)
    # Disable cache, so we can refresh the data in Redis
    env_cache_disabled = os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED')
    if not env_cache_disabled:
        os.environ['PYBOSSA_REDIS_CACHE_DISABLED'] = '1'
    # Cache 3 pages
    apps_cached = []
    pages = range(1, 4)
    import pybossa.cache.apps as cached_apps
    import pybossa.cache.categories as cached_cat
    import pybossa.cache.users as cached_users
    import pybossa.cache.project_stats  as stats

    def warm_app(id, short_name, featured=False):
        if id not in apps_cached:
            cached_apps.get_app(short_name)
            cached_apps.n_tasks(id)
            n_task_runs = cached_apps.n_task_runs(id)
            cached_apps.overall_progress(id)
            cached_apps.last_activity(id)
            cached_apps.n_completed_tasks(id)
            cached_apps.n_volunteers(id)
            if n_task_runs >= 1000 or featured:
                print "Getting stats for %s as it has %s task runs" % (short_name, n_task_runs)
                stats.get_stats(id, app.config.get('GEO'))
            apps_cached.append(id)

    # Cache top projects
    apps = cached_apps.get_top()
    for a in apps:
        warm_app(a['id'], a['short_name'])
    for page in pages:
        apps = cached_apps.get_featured('featured', page,
                                        app.config['APPS_PER_PAGE'])
        for a in apps:
            warm_app(a['id'], a['short_name'], featured=True)

    # Categories
    categories = cached_cat.get_used()
    for c in categories:
        for page in pages:
             apps = cached_apps.get(c['short_name'],
                                    page,
                                    app.config['APPS_PER_PAGE'])
             for a in apps:
                 warm_app(a['id'], a['short_name'])
    # Users
    cached_users.get_leaderboard(app.config['LEADERBOARD'], 'anonymous')
    cached_users.get_top()

    if env_cache_disabled is None:
        del os.environ['PYBOSSA_REDIS_CACHE_DISABLED']
    else:
        os.environ['PYBOSSA_REDIS_CACHE_DISABLED'] = env_cache_disabled

    return True
