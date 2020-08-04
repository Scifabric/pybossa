from collections import OrderedDict
from contextlib import closing
import json
import re
import tempfile

import pandas as pd

from sqlalchemy.sql import text
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from pybossa.exporter import Exporter
from pybossa.core import db, uploader
from pybossa.cache.task_browse_helpers import get_task_filters
from pybossa.cache.users import get_user_info


__KEY_RE = re.compile(
    '^consensus__(?P<ans_key>.+)__contributorsConsensusPercentage$')


def export_consensus_json(project, ty, expanded, filters, *nargs):
    return export_consensus(project, ty, 'json', expanded, filters)


def export_consensus_csv(project, ty, expanded, filters, *nargs):
    return export_consensus(project, ty, 'csv', expanded, filters)


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
    for row in data:
        for k, v in row.items():
            if isinstance(v, (dict, list)):
                row[k] = json.dumps(v)
    df = pd.DataFrame(data)
    cols = sorted(df.columns)
    df[cols].to_csv(filename, index=False, encoding='utf-8')


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
                new_prefix = u'{}{}{}'.format(_prefix, sep, k)
            _flatten(v, current_level + 1, new_prefix)

    _flatten(obj, 0, prefix)
    return flattened

def get_contributor_answer(data, path, answer_field_config):

    def match_nested_value(record):
        match = [record[k] == v for k, v in key_value_pair.items()]
        return all(patch)

    if not answer_field_config or not path:
        return None
    paths = path.split('.')
    if answer_field_config.get('type') == 'categorical_nested':
        key_values = answer_field_config.get('config', {}).get('keyValues', [])

        field_name = paths[0]
        key = paths[-1]
        values = paths[1 : -2]
        key_value_pair = {key_value[i]: values[i] for i in range(len(key_values))}

        field_data = data.get(field_name, [])
        target_field_data = [d for d in field_data if match_nested_value(d)]
        return target_field_data[0][key] if target_field_data else None
    else:
        return get_value_by_path(data, paths)

def get_value_by_path(data, path, consensus_type):
    if not path or not data:
        return data
    key = path[0]
    try:
        index = int(key)
        return get_value_by_path(data[index], path[1:], consensus_type)
    except ValueError:
        return get_value_by_path(data.get(key), path[1:], consensus_type)


def format_consensus(rows):
    # cons = {
    # "context.0.name": {
    #     "answser_field_config": {
    #         "config": {
    #             "keys": [
    #             "contract_size",
    #             "last_delivery_date",
    #             "last_trade_date",
    #             "full_exchange_symbol",
    #             "first_trade_date",
    #             "first_notice_date",
    #             "first_delivery_date",
    #             "tick_size"
    #             ],
    #             "keyValues": [
    #             "month",
    #             "year"
    #             ]
    #         },
    #         "type": "categorical_nested",
    #         "retry_for_consensus": False
    #     },
    #     "contributorsMetConsensus": [
    #     894
    #     ],
    #     "percentage": 100.0,
    #     "contributorsConsensusPercentage": [
    #     {
    #         "percentage": 100.0,
    #         "user_id": 894
    #     }
    #     ],
    #     "value": "ywr"
    # },
    # "context.1.name": {
    #     "contributorsMetConsensus": [
    #     894
    #     ],
    #     "percentage": 100.0,
    #     "contributorsConsensusPercentage": [
    #     {
    #         "percentage": 100.0,
    #         "user_id": 894
    #     }
    #     ],
    #     "value": "ljh"
    # },
    # "context.1.addr": {
    #     "contributorsMetConsensus": [
    #     894
    #     ],
    #     "percentage": 100.0,
    #     "contributorsConsensusPercentage": [
    #     {
    #         "percentage": 100.0,
    #         "user_id": 894
    #     }
    #     ],
    #     "value": "ny"
    # },
    # "context.0.addr": {
    #     "contributorsMetConsensus": [
    #     894
    #     ],
    #     "percentage": 100.0,
    #     "contributorsConsensusPercentage": [
    #     {
    #         "percentage": 100.0,
    #         "user_id": 894
    #     }
    #     ],
    #     "value": "nj"
    # },
    # "context": {
    #     "contributorsMetConsensus": [
    #     894
    #     ],
    #     "percentage": 100.0,
    #     "contributorsConsensusPercentage": [
    #     {
    #         "percentage": 100.0,
    #         "user_id": 894
    #     }
    #     ],
    #     "value": [
    #     {
    #         "addr": "nj",
    #         "name": "ywr"
    #     },
    #     {
    #         "addr": "ny",
    #         "name": "ljh"
    #     }
    #     ]
    # }
    # }
    rv = []
    local_user_cache = {}
    import pdb; pdb.set_trace()
    for row in rows:
        data = OrderedDict(row)
        task_info = flatten(data.get('task_info', {}), prefix='task_info')
        data.update(task_info)
        consensus = data.pop('consensus') or OrderedDict()
        # consensus = dict(consensus=cons)
        answer_fields = {k: v.get('answser_field_config', {}) for k, v in consensus['consensus'].items()}
        consensus = flatten(consensus, level=2,
                            ignore=['contributorsMetConsensus', 'answser_field_config'])
        print(consensus)
        task_runs = data['task_run__info']
        for k, v in consensus.items():
            match = re.match(__KEY_RE, k)
            if match:
                import pdb; pdb.set_trace()
                ans_key = match.group('ans_key')
                for user_pct in v:
                    user_id = user_pct.pop('user_id')
                    if user_id not in local_user_cache:
                        user_info = get_user_info(user_id) or {'user_id': user_id}
                        local_user_cache[user_id] = user_info
                    user_name = user_info.get('name')
                    tr = task_runs.get(user_name, {})
                    user_pct['contributor_name'] = user_name
                    user_pct['contributor_answer'] = get_contributor_answer(tr, ans_key, answer_fields[ans_key])
                    user_pct['answer_percentage'] = user_pct.pop('percentage', None)

        consensus.update(data)
        rv.append(consensus)
    return rv


def get_consensus_data(project_id, filters):
    conditions, filter_params = get_task_filters(filters)
    query = text('''
        SELECT
            task.id as task_id,
            task.project_id as project_id,
            task.calibration as gold,
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
                json_object_agg(u.name, tr.info) as task_run__info
            FROM task_run tr
            JOIN "user" u
            ON tr.user_id = u.id
            WHERE project_id = :project_id
            GROUP BY task_id
            ) AS taskruns
        ON task.id = taskruns.task_id
        LEFT JOIN result r
            ON task.id = r.task_id
            AND r.last_version = True
        WHERE (task.state = 'completed' OR (task.calibration = 1 AND taskruns.ct > 0))
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
            task.calibration as gold,
            task.info as task_info,
            task.user_pref as user_pref,
            r.info as consensus,
            taskruns.task_run__id as task_run__id,
            taskruns.task_run__created as task_run__created,
            taskruns.task_run__finish_time as task_run__finish_time,
            taskruns.task_run__user_id as task_run__user_id,
            taskruns.task_run__info as task_run__info,
            taskruns.email_addr as email_addr,
            taskruns.fullname as fullname

        FROM task LEFT JOIN (
            SELECT task_id,
                CAST(COUNT(tr.id) AS FLOAT) AS ct,
                MAX(tr.finish_time) as ft,
                array_agg(tr.id) as task_run__id,
                array_agg(tr.created) as task_run__created,
                array_agg(tr.finish_time) as task_run__finish_time,
                json_object_agg(u.name, tr.info) as task_run__info,
                array_agg(tr.user_id) as task_run__user_id,
                array_agg(u.email_addr) as email_addr,
                array_agg(u.fullname) as fullname
            FROM task_run tr
            JOIN "user" u
            ON tr.user_id = u.id
            WHERE project_id = :project_id
            GROUP BY task_id
            ) AS taskruns
        ON task.id = taskruns.task_id
        LEFT JOIN result r
            ON task.id = r.task_id
            AND r.last_version = True
        WHERE (task.state = 'completed' OR (task.calibration = 1 AND taskruns.ct > 0))
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
            file_name = secure_filename(u'%s_%s.%s' % (name, obj, filetype))
            zipped_datafile = tempfile.NamedTemporaryFile()
            _zip = self._zip_factory(zipped_datafile.name)
            _zip.write(
                datafile.name, file_name)
            _zip.close()
            container = "user_%d" % project.owner_id
            filename = self.download_name(project, obj, filetype)
            fs = FileStorage(filename=filename, stream=zipped_datafile)
            return closing(fs)
