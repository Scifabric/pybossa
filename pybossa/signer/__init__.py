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

from itsdangerous import URLSafeTimedSerializer
from werkzeug import generate_password_hash, check_password_hash


class Signer(object):

    def __init__(self, app=None):
        self.app = app
        if app is not None: # pragma: no cover
            self.init_app(app)


    def init_app(self, app):
        key = app.config['ITSDANGEROUSKEY']
        self.signer = URLSafeTimedSerializer(key)


    def loads(self, string, **kwargs):
        return self.signer.loads(string, **kwargs)


    def dumps(self, key, **kwargs):
        return self.signer.dumps(key, **kwargs)


    def generate_password_hash(self, password):
        return generate_password_hash(password)


    def check_password_hash(self, passwd_hash, password):
        return check_password_hash(passwd_hash, password)
