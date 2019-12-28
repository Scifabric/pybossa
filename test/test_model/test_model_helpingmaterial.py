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

from default import Test, db, with_context
from nose.tools import assert_raises
from sqlalchemy.exc import IntegrityError
from pybossa.model.helpingmaterial import HelpingMaterial
from factories import HelpingMaterialFactory


class TestModelHelpingMaterial(Test):

    @with_context
    def test_helpingmaterial_public_attributes(self):
        """Test public attributes works."""
        hm = HelpingMaterialFactory.create()
        public_attributes = ['created', 'id', 'info', 'media_url', 'priority']
        assert sorted(hm.public_attributes()) == sorted(public_attributes)
