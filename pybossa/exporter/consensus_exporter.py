from collections import OrderedDict
import json
import tempfile

import pandas as pd

from sqlalchemy.sql import text
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from pybossa.exporter import Exporter
from pybossa.core import db, uploader
from pybossa.cache.task_browse_helpers import get_task_filters


def export_consensus(project, obj, filetype, expanded, filters):
    if expanded:
        get_data = get_consensus_data_metadata
    else:
        get_data = get_consensus_data
    if filetype == 'json':
        formatter = json_formatter
    else:
        formatter = csv_formatter
    exporter = ConsensusExporter(get_data, formatter)
    return exporter.export(project, obj, filters, filetype)


def csv_formatter(data, filename):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding='utf-8')


def json_formatter(data, fp):
    json.dump(data, fp)


def flatten(obj, level=1, prefix=None, sep='__', ignore=tuple()):
    flattened = OrderedDict()

    def _flatten(_obj, current_level, _prefix):
        if current_level > level or not isinstance(_obj, dict):
            flattened[_prefix] = _obj
            return

        for k, v in _obj.iteritems():
            if k in ignore:
                continue
            if _prefix is None:
                new_prefix = k
            else:
                new_prefix = '{}{}{}'.format(_prefix, sep, k)
            _flatten(v, current_level + 1, new_prefix)

    _flatten(obj, 0, prefix)
    return flattened


def format_consensus(rows):
    rv = []
    for row in rows:
        data = OrderedDict(row)
        consensus = data.pop('consensus') or OrderedDict()
        consensus = flatten(consensus, level=2,
                            ignore=['contributorsMetConsensus'])
        consensus.update(data)
        rv.append(consensus)
    return rv


def get_consensus_data(project_id, filters):
    conditions, filter_params = get_task_filters(filters)
    query = text('''
        SELECT
            task.id as task_id,
            task.project_id as project_id,
            r.info as consensus,
            taskruns.task_run__id as task_run__id,
            taskruns.task_run__created as task_run__created,
            taskruns.task_run__finish_time as task_run__finish_time,
            taskruns.task_run__user_id as task_run__user_id,
            taskruns.task_run__info as task_run__info

        FROM task LEFT JOIN (
            SELECT task_id,
                CAST(COUNT(tr.id) AS FLOAT) AS ct,
                MAX(tr.finish_time) as ft,
                array_agg(tr.id) as task_run__id,
                array_agg(tr.created) as task_run__created,
                array_agg(tr.finish_time) as task_run__finish_time,
                array_agg(tr.user_id) as task_run__user_id,
                array_agg(tr.info) as task_run__info
            FROM task_run tr
            WHERE project_id = :project_id
            GROUP BY task_id
            ) AS taskruns
        ON task.id = taskruns.task_id
        LEFT JOIN result r
            ON task.id = r.task_id
            AND r.last_version = True
        WHERE task.state = 'completed'
        AND task.project_id=:project_id
        {};
    '''.format(conditions))
    params = dict(project_id=project_id, **filter_params)
    rows = db.slave_session.execute(query, params).fetchall()
    return format_consensus(rows)


def get_consensus_data_metadata(project_id, filters):
    conditions, filter_params = get_task_filters(filters)
    query = text('''
        SELECT
            task.id as task_id,
            task.project_id as project_id,
            task.info as task_info,
            task.user_pref as user_pref,
            r.info as consensus,
            taskruns.task_run__id as task_run__id,
            taskruns.task_run__created as task_run__created,
            taskruns.task_run__finish_time as task_run__finish_time,
            taskruns.task_run__user_id as task_run__user_id,
            taskruns.task_run__info as task_run__info,
            taskruns.name as name,
            taskruns.email_addr as email_addr,
            taskruns.fullname as fullname

        FROM task LEFT JOIN (
            SELECT task_id,
                CAST(COUNT(tr.id) AS FLOAT) AS ct,
                MAX(tr.finish_time) as ft,
                array_agg(tr.id) as task_run__id,
                array_agg(tr.created) as task_run__created,
                array_agg(tr.finish_time) as task_run__finish_time,
                array_agg(tr.user_id) as task_run__user_id,
                array_agg(tr.info) as task_run__info,
                array_agg(u.name) as name,
                array_agg(u.email_addr) as email_addr,
                array_agg(u.fullname) as fullname
            FROM task_run tr
            JOIN public.user u
            ON tr.user_id = u.id
            WHERE project_id = :project_id
            GROUP BY task_id
            ) AS taskruns
        ON task.id = taskruns.task_id
        LEFT JOIN result r
            ON task.id = r.task_id
            AND r.last_version = True
        WHERE task.state = 'completed'
        AND task.project_id=:project_id
        {};
    '''.format(conditions))
    params = dict(project_id=project_id, **filter_params)
    rows = db.slave_session.execute(query, params).fetchall()
    return format_consensus(rows)


class ConsensusExporter(Exporter):

    def __init__(self, get_data, file_formatter):
        self._get_data = get_data
        self.to_file = file_formatter

    def data_to_file(self, project_id, filters, filename):
        data = self._get_data(project_id, filters or {})
        self.to_file(data, filename)

    def export(self, project, obj, filters, filetype):
        name = self._project_name_latin_encoded(project)
        with tempfile.NamedTemporaryFile() as datafile:
            self.data_to_file(project.id, filters, datafile)
            datafile.flush()
            with tempfile.NamedTemporaryFile() as zipped_datafile:
                _zip = self._zip_factory(zipped_datafile.name)
                _zip.write(
                    datafile.name, secure_filename('%s_%s.%s' % (name, obj, filetype)))
                _zip.close()
                container = "user_%d" % project.owner_id
                filename = self.download_name(project, obj, filetype)
                _file = FileStorage(
                    filename=filename, stream=zipped_datafile)
                uploader.upload_file(_file, container=container)
        return uploader.get_file_path(container, filename)
