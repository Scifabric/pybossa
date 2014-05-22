# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
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

import json
import StringIO
from default import with_context
from pybossa.util import unicode_csv_reader
from helper import web



class TestExportUsers(web.Helper):

    exportable_attributes = ('id', 'name', 'fullname', 'email_addr',
                             'created', 'locale', 'admin')

    @with_context
    def test_json_contains_all_attributes(self):
        self.register()

        res = self.app.get('/admin/users/export?format=json',
                            follow_redirects=True)
        data = json.loads(res.data)

        for attribute in self.exportable_attributes:
            assert attribute in data[0], data

    @with_context
    def test_json_returns_all_users(self):
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

        assert "Juan Jose" in data, data
        assert "Manolita" in data, data
        assert "Juan Jose2" in data, data
        assert len(json_data) == 3

    @with_context
    def test_csv_contains_all_attributes(self):
        self.register()

        res = self.app.get('/admin/users/export?format=csv',
                            follow_redirects=True)
        data = res.data

        for attribute in self.exportable_attributes:
            assert attribute in data, data

    @with_context
    def test_csv_returns_all_users(self):
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
        csv_content = StringIO.StringIO(data)
        csvreader = unicode_csv_reader(csv_content)

        # number of users is -1 because the first row in csv are the headers
        number_of_users = -1
        for row in csvreader:
            number_of_users += 1

        assert number_of_users == 3, number_of_users




