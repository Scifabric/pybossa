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
"""
PYBOSSA api module for user oauth tokens via an API.

This package adds GET method for:
    * user oauth tokens

"""
import json
from werkzeug.exceptions import MethodNotAllowed, NotFound
from flask import Response
from flask_login import current_user
from pybossa.util import jsonpify
from pybossa.ratelimit import ratelimit
from .api_base import APIBase, error
from pybossa.auth import ensure_authorized_to


class TokenAPI(APIBase):

    """
    Class for user oauth tokens

    """

    _resource_name = 'token'
    oauth_providers = ('twitter', 'facebook', 'google')

    @jsonpify
    @ratelimit(limit=300, per=15 * 60)
    def get(self, token):
        try:
            ensure_authorized_to('read', self._resource_name, token=token)
            user_tokens = self._get_all_tokens()
            if token:
                response = self._get_token(token, user_tokens)
            else:
                response = user_tokens
            return Response(json.dumps(response), mimetype='application/json')
        except Exception as e:
            return error.format_exception(
                e,
                target=self._resource_name,
                action='GET')

    def _get_token(self, token, user_tokens):
        token = '%s_token' % token
        if token in user_tokens:
            return {token: user_tokens[token]}
        raise NotFound

    def _get_all_tokens(self):
        tokens = {}
        for provider in self.oauth_providers:
            token = self._create_token_for('%s_token' % provider)
            if token:
                tokens['%s_token' % provider] = token
        return tokens

    def _create_token_for(self, provider):
        token_value = dict(current_user.info).get(provider)
        if token_value:
            token = dict(oauth_token=token_value['oauth_token'])
            if token_value.get('oauth_token_secret'):
                token['oauth_token_secret'] = token_value['oauth_token_secret']
            return token
        return None

    def post(self):
        raise MethodNotAllowed(valid_methods=['GET'])

    def delete(self, oid=None):
        raise MethodNotAllowed(valid_methods=['GET'])

    def put(self, oid=None):
        raise MethodNotAllowed(valid_methods=['GET'])
