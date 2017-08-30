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
import json
from default import db, with_context
from test_api import TestAPI
from factories import AnnouncementFactory
from factories import UserFactory, HelpingMaterialFactory, ProjectFactory
from pybossa.repositories import AnnouncementRepository
from mock import patch

announcement_repo = AnnouncementRepository(db)


class TestAnnouncementAPI(TestAPI):

    @with_context
    def test_query_announcement(self):
        """Test API query for announcement endpoint works"""
        owner = UserFactory.create()
        user = UserFactory.create()
        # project = ProjectFactory(owner=owner)
        announcements = AnnouncementFactory.create_batch(9)
        announcement = AnnouncementFactory.create()

        # As anon
        url = '/api/announcement'
        res = self.app_get_json(url)
        print res.data
        #data = json.loads(res.data)
        #assert len(data['announcements']) == 10, data

