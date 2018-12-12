# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2018 Scifabric LTD.
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

from functools import wraps
from flask import Blueprint, current_app, Response, request
from flask.ext.login import current_user, login_required

import requests
from werkzeug.exceptions import Forbidden, BadRequest, InternalServerError, NotFound

from pybossa.cache.projects import get_project_data
from boto.exception import S3ResponseError
from pybossa.cloud_store_api.connection import create_connection
from pybossa.contributions_guard import ContributionsGuard
from pybossa.core import task_repo, signer
from pybossa.encryption import AESWithGCM
from pybossa.hdfs.client import HDFSKerberos
from pybossa.sched import has_lock


blueprint = Blueprint('files', __name__)


def no_cache(view_func):
    @wraps(view_func)
    def decorated(*args, **kwargs):
        response = view_func(*args, **kwargs)
        response.headers.add('Cache-Control', 'no-store')
        response.headers.add('Pragma', 'no-cache')
        return response
    return decorated


def check_allowed(user_id, task_id, project, file_url):
    task = task_repo.get_task(task_id)

    if not task or task.project_id != project['id']:
        raise BadRequest('Task does not exist')

    if file_url not in task.info.values():
        raise Forbidden('Invalid task content')

    if current_user.admin:
        return True

    if has_lock(task_id, user_id,
                project['info'].get('timeout', ContributionsGuard.STAMP_TTL)):
        return True

    if user_id in project['owners_ids']:
        return True

    raise Forbidden('FORBIDDEN')


@blueprint.route('/encrypted/<string:store>/<string:bucket>/<int:project_id>/<path:path>')
@no_cache
@login_required
def encrypted_file(store, bucket, project_id, path):
    """Proxy encrypted task file in a cloud storage"""
    current_app.logger.info('Project id {} decrypt file. {}'.format(project_id, path))
    conn_args = current_app.config.get('S3_TASK_REQUEST', {})
    signature = request.args.get('task-signature')
    if not signature:
        current_app.logger.exception('Project id {} no signature {}'.format(project_id, path))
        raise Forbidden('No signature')

    project = get_project_data(project_id)
    timeout = project['info'].get('timeout', ContributionsGuard.STAMP_TTL)

    payload = signer.loads(signature, max_age=timeout)
    task_id = payload['task_id']

    check_allowed(current_user.id, task_id, project, request.path)

    ## download file
    try:
        key = '/{}/{}'.format(project_id, path)
        conn = create_connection(**conn_args)
        _bucket = conn.get_bucket(bucket, validate=False)
        _key = _bucket.get_key(key, validate=False)
        content = _key.get_contents_as_string()
    except S3ResponseError as e:
        current_app.logger.exception('Project id {} get task file {} {}'.format(project_id, path, e))
        if e.error_code == 'NoSuchKey':
            raise NotFound('File Does Not Exist')
        else:
            raise InternalServerError('An Error Occurred')

    ## decyrpt file
    secret = current_app.config.get('FILE_ENCRYPTION_KEY')
    cipher = AESWithGCM(secret)
    decrypted = cipher.decrypt(content)

    response = Response(decrypted, content_type=_key.content_type)
    response.headers.add('Content-Encoding', _key.content_encoding)
    response.headers.add('Content-Disposition', _key.content_disposition)
    return response


@blueprint.route('/hdfs/<int:project_id>/<string:cluster>/<path:path>')
@no_cache
@login_required
def hdfs_file(project_id, cluster, path):
    signature = request.args.get('task-signature')
    if not signature:
        raise Forbidden('No signature')

    project = get_project_data(project_id)
    timeout = project['info'].get('timeout', ContributionsGuard.STAMP_TTL)
    payload = signer.loads(signature, max_age=timeout)
    task_id = payload['task_id']
    check_allowed(current_user.id, task_id, project, request.path)

    client = HDFSKerberos(**current_app.config['HDFS_CONFIG'][cluster])
    try:
        content = client.get('/{}'.format(path))
        project_encryption = project['info'].get('ext_config', {}).get('encryption', {})
        if project_encryption:
            secret = get_secret_from_vault(project_encryption)
            cipher = AESWithGCM(secret)
            content = cipher.decrypt(content)
    except Exception:
        current_app.logger.exception('Project id {} get task file {}'.format(project_id, path))
        raise InternalServerError('An error Occurred')

    return Response(content)


def get_secret_from_vault(project_encryption):
    config = current_app.config['VAULT_CONFIG']
    res = requests.get(config['url'].format(**project_encryption), **config['request'])
    data = res.json()
    try:
        return get_path(data, config['response'])
    except Exception:
        raise RuntimeError(get_path(data, config['error']))


def get_path(dict_, path):
    if not path:
        return dict_
    return get_path(dict_[path[0]], path[1:])
