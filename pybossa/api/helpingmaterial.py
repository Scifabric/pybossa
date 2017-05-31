# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2017 Scifabric LTD.
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
"""
PYBOSSA api module for domain object HelpingMaterial via an API.

This package adds GET, POST, PUT and DELETE methods for:
    * helpingmaterial

"""
from api_base import APIBase
from pybossa.model.helpingmaterial import HelpingMaterial
from pybossa.core import user_repo, project_repo, uploader
from pybossa.util import get_avatar_url
from flask.ext.login import current_user
from flask import current_app
from werkzeug.exceptions import BadRequest, NotFound
from pybossa.auth import ensure_authorized_to
import json


class HelpingMaterialAPI(APIBase):

    """Class API for domain object HelpingMaterial."""

    reserved_keys = set(['id', 'created'])

    __class__ = HelpingMaterial

    def _file_upload(self, request):
        content_type = 'multipart/form-data'
        if content_type in request.headers.get('Content-Type'):
            tmp = dict()
            for key in request.form.keys():
                tmp[key] = request.form[key]

            ensure_authorized_to('create', HelpingMaterial,
                                 project_id=tmp['project_id'])
            upload_method = current_app.config.get('UPLOAD_METHOD')
            if request.files.get('file') is None:
                raise AttributeError
            _file = request.files['file']
            container = "user_%s" % current_user.id
            uploader.upload_file(_file,
                                 container=container)
            file_url = get_avatar_url(upload_method,
                                      _file.filename, container)
            tmp['media_url'] = file_url
            if tmp.get('info') is None:
                tmp['info'] = dict()
            tmp['info']['container'] = container
            tmp['info']['file_name'] = _file.filename
            return tmp
        else:
            return None

    def _file_delete(self, request, obj):
        """Delete file from obj."""
        keys = obj.info.keys()
        if 'file_name' in keys and 'container' in keys:
            ensure_authorized_to('delete', obj)
            uploader.delete_file(obj.info['file_name'],
                                 obj.info['container'])


    def _forbidden_attributes(self, data):
        for key in data.keys():
            if key in self.reserved_keys:
                raise BadRequest("Reserved keys in payload")

    def _update_object(self, obj):
        if not current_user.is_anonymous():
            obj.user_id = current_user.id
