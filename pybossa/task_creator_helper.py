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
"""Module with PyBossa create task helper."""
from flask import current_app
import hashlib
from pybossa.cloud_store_api.s3 import upload_json_data
from pybossa.data_access import data_access_levels
from werkzeug.exceptions import BadRequest, Conflict
from flask import url_for

def set_gold_answer(task, project_id, gold_answers, file_id=None):
    if not gold_answers:
        return
    if data_access_levels:
        file_name = 'task_private_gold_answer.json'
        gold_answers = dict(gold_ans_url=upload_files_priv(task, project_id, gold_answers, file_name, file_id))

    if type(task) is dict:
        task['gold_answers'] = gold_answers
    else:
        task.gold_answers = gold_answers


def upload_files_priv(task, project_id, data, file_name, file_id=None):
    encryption = current_app.config.get('ENABLE_ENCRYPTION', False)
    bucket = current_app.config.get("S3_REQUEST_BUCKET")
    if file_id:
        task_hash = file_id
    else:
        task_hash = hashlib.md5(json.dumps(task)).hexdigest()
    path = "{}/{}".format(project_id, task_hash)
    s3_conn_type = current_app.config.get('S3_CONN_TYPE')
    values = dict(store=s3_conn_type, bucket=bucket, project_id=project_id, path='{}/{}'.format(task_hash, file_name))
    file_url = url_for('fileproxy.encrypted_file', **values)
    upload_json_data(bucket=bucket,
    json_data=data, upload_path=path,
    file_name=file_name, encryption=encryption,
    conn_name='S3_TASK_REQUEST')
    return file_url

