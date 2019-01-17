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

import json
import io
from default import with_context
from factories import UserFactory
from helper import web


class TestExportUsers(web.Helper):

    exportable_attributes = ('id', 'name', 'fullname', 'email_addr',
                             'created', 'locale', 'admin', 'consent',
                             'restrict')

    @with_context
    def test_json_contains_all_attributes(self):
        self.register()

        res = self.app.get('/admin/users/export?format=json',
                           follow_redirects=True)
        data = json.loads(res.data.decode('utf-8'))

        for attribute in self.exportable_attributes:
            assert attribute in data[0].keys(), data

    @with_context
    def test_json_returns_all_users(self):
        restricted = UserFactory.create(restrict=True, id=5000014)
        self.register(fullname="Manolita")
        self.signout()
        self.register(fullname="Juan Jose", name="juan",
                      email="juan@juan.com", password="juan")
        self.signout()
        self.register(fullname="Juan Jose2", name="juan2",
                      email="juan2@juan.com", password="juan2")
        self.signin()

        res = self.app.get('/admin/users/export?format=json',
                            follow_redirects=True)
        data = res.data
        json_data = json.loads(data)

        assert "Juan Jose" in str(data), data
        assert "Manolita" in str(data), data
        assert "Juan Jose2" in str(data), data
        assert restricted.name not in str(data), data
        assert len(json_data) == 3

    @with_context
    def test_csv_contains_all_attributes(self):
        self.register()

        restricted = UserFactory.create(restrict=True, id=5000015)

        res = self.app.get('/admin/users/export?format=csv',
                            follow_redirects=True)
        data = res.data

        for attribute in self.exportable_attributes:
            assert attribute in str(data), str(data)
        assert restricted.name not in str(data), str(data)

    @with_context
    def test_csv_returns_all_users(self):
        restricted = UserFactory.create(restrict=True, id=5000016)
        self.register(fullname="Manolita")
        self.signout()
        self.register(fullname="Juan Jose", name="juan",
                      email="juan@juan.com", password="juan")
        self.signout()
        self.register(fullname="Juan Jose2", name="juan2",
                      email="juan2@juan.com", password="juan2")
        self.signin()

        res = self.app.get('/admin/users/export?format=csv',
                           follow_redirects=True)
        data = res.data
        assert restricted.name not in str(data.decode('utf-8'))
        import pandas as pd
        df = pd.DataFrame.from_csv(io.StringIO(data.decode('utf-8')))
        assert df.shape[0] == 3, df.shape[0]
