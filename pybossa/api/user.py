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
"""
PyBossa api module for domain object USER via an API.

This package adds GET method for:
    * users

"""
from api_base import APIBase
from pybossa.model import User
import pybossa.cache.users as cached_users
from werkzeug.exceptions import MethodNotAllowed
from flask import request
from flask.ext.login import current_user


class UserAPI(APIBase):

    """
    Class for the domain object User.

    """

    __class__ = User

    # Define private and public fields available through the API
    # (maybe should be defined in the model?) There are fields like password hash
    # that shouldn't be visible even for admins

    # Attributes that are always visible from everyone
    public_attributes = ('locale', 'name')

    # Attributes that are visible only for admins or everyone if the user
    # has privacy_mode disabled
    allowed_attributes = ('name', 'locale', 'fullname', 'created')


    def _select_attributes(self, user_data):
        privacy = self._is_user_private(user_data)
        for attribute in user_data.keys():
            self._remove_attribute_if_private(attribute, user_data, privacy)
        return user_data

    def _remove_attribute_if_private(self, attribute, user_data, privacy):
        if self._is_attribute_private(attribute, privacy):
            del user_data[attribute]

    def _is_attribute_private(self, attribute, privacy):
        return (attribute not in self.allowed_attributes or
                privacy and attribute not in self.public_attributes)

    def _is_user_private(self, user):
        return not self._is_requester_admin() and user['privacy_mode']

    def _is_requester_admin(self):
        return current_user.is_authenticated() and current_user.admin

    def _custom_filter(self, query):
        if self._private_attributes_in_request() and not self._is_requester_admin():
            query = query.filter(getattr(User, 'privacy_mode') == False)
        return query

    def _private_attributes_in_request(self):
        for attribute in request.args.keys():
            if (attribute in self.allowed_attributes and
                attribute not in self.public_attributes):
                return True
        return False

    def post(self):
        raise MethodNotAllowed(valid_methods=['GET'])

    def delete(self):
        raise MethodNotAllowed(valid_methods=['GET'])

    def put(self):
        raise MethodNotAllowed(valid_methods=['GET'])
