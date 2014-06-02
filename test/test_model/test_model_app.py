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

from default import Test, db, with_context
from nose.tools import assert_raises
from pybossa.model.app import App
from pybossa.model.user import User
from sqlalchemy.exc import IntegrityError


class TestModelApp(Test):

    @with_context
    def test_app_errors(self):
        """Test project model errors."""
        app = App(name='Project',
                  short_name='proj',
                  description='desc',
                  owner_id=None)

        # App.owner_id shoult not be nullable
        db.session.add(app)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        # App.name shoult not be nullable
        user = User(email_addr="john.doe@example.com",
                    name="johndoe",
                    fullname="John Doe",
                    locale="en")
        db.session.add(user)
        db.session.commit()
        user = db.session.query(User).first()
        app.owner_id = user.id
        app.name = None
        db.session.add(app)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        app.name = ''
        db.session.add(app)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        # App.short_name shoult not be nullable
        app.name = "Project"
        app.short_name = None
        db.session.add(app)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        app.short_name = ''
        db.session.add(app)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        # App.description shoult not be nullable
        db.session.add(app)
        app.short_name = "project"
        app.description = None
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        app.description = ''
        db.session.add(app)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()
