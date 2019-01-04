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
PYBOSSA api module for domain object USER via an API.

This package adds GET method for:
    * users

"""
from .api_base import APIBase, error, jsonpify, ratelimits, ratelimit
from pybossa.model.user import User
from werkzeug.exceptions import MethodNotAllowed
from flask import request
from flask_login import current_user


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
        if current_user.is_authenticated and (current_user.admin or
                                                current_user.id ==
                                                user_data['id']):
            tmp = User().to_public_json(user_data)
            tmp['id'] = user_data['id']
            tmp['email_addr'] = user_data['email_addr']
            tmp['info'] = user_data['info']
            return tmp
        else:
            privacy = self._is_user_private(user_data)
            for attribute in list(user_data.keys()):
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
        return current_user.is_authenticated and current_user.admin

    def _custom_filter(self, filters):
        if self._private_attributes_in_request() and not self._is_requester_admin():
            filters['privacy_mode'] = False
        return filters

    def _private_attributes_in_request(self):
        for attribute in list(request.args.keys()):
            if (attribute in self.allowed_attributes and
                    attribute not in self.public_attributes):
                return True
        return False

    @jsonpify
    @ratelimit(limit=ratelimits.get('LIMIT'), per=ratelimits.get('PER'))
    def post(self):
        try:
            raise MethodNotAllowed
        except MethodNotAllowed as e:
            return error.format_exception(
                e,
                target=self.__class__.__name__.lower(),
                action='POST')

    @jsonpify
    @ratelimit(limit=ratelimits.get('LIMIT'), per=ratelimits.get('PER'))
    def delete(self, oid=None):
        try:
            raise MethodNotAllowed
        except MethodNotAllowed as e:
            return error.format_exception(
                e,
                target=self.__class__.__name__.lower(),
                action='DEL')
