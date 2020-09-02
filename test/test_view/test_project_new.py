# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2019 Scifabric LTD.
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

from default import with_context
from flask import current_app
from helper.web import Helper
from factories import UserFactory


class TestProjectNew(Helper):

    @with_context
    def test_new_project_with_data_classification_missing(self):
        # delete the key DATA_CLASSIFICATION to test the edge case
        data_classification = current_app.config.pop('DATA_CLASSIFICATION', None)

        try:
            admin = UserFactory.create()
            url = '/project/new?api_key=%s' % admin.api_key
            res = self.app.post(url)
        finally:
            # Reset the key value so that not affecting other tests
            current_app.config['DATA_CLASSIFICATION'] = data_classification
            print(current_app.config['DATA_CLASSIFICATION'])

        assert res.status_code == 200, res.data

    @with_context
    def test_new_project(self):
        admin = UserFactory.create()
        url = '/project/new?api_key=%s' % admin.api_key
        res = self.app.post(url)
        assert res.status_code == 200, res.data
