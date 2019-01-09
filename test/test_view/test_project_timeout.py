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
from bs4 import BeautifulSoup

from default import Test, db, with_context
from factories import ProjectFactory
from helper.web import Helper


class TestProjectTimeout(Helper):

    @with_context
    def test_default_timeout(self):
        project = ProjectFactory.create()
        url = '/project/%s/tasks/timeout?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app.get(url)
        assert res.status_code == 200, res.data
        dom = BeautifulSoup(res.data)
        assert dom.find(id='minutes')['value'] == '60'
        assert dom.find(id='seconds')['value'] == '0'

    @with_context
    def test_set_timeout(self):
        project = ProjectFactory.create()
        data = {'minutes': 10, 'seconds': 30}
        url = '/project/%s/tasks/timeout?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app.post(url, data=data)
        res = self.app.get(url)
        assert res.status_code == 200, res.data
        dom = BeautifulSoup(res.data)
        assert dom.find(id='minutes')['value'] == '10'
        assert dom.find(id='seconds')['value'] == '30'

    @with_context
    def test_set_timeout_too_low(self):
        project = ProjectFactory.create()
        data = {'minutes': 0, 'seconds': 20}
        url = '/project/%s/tasks/timeout?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app.post(url, data=data)
        assert 'Timeout should be between 30 seconds and 120 minuntes' in res.data

    @with_context
    def test_set_timeout_too_high_seconds(self):
        project = ProjectFactory.create()
        data = {'minutes': 0, 'seconds': 200 * 60}
        url = '/project/%s/tasks/timeout?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app.post(url, data=data)
        assert 'Timeout should be between 30 seconds and 120 minuntes' in res.data

    @with_context
    def test_set_timeout_too_high_minutes(self):
        project = ProjectFactory.create()
        data = {'minutes': 200, 'seconds': 0}
        url = '/project/%s/tasks/timeout?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app.post(url, data=data)
        assert 'Timeout should be between 30 seconds and 120 minuntes' in res.data
