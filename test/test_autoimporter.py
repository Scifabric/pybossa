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
from default import db
from helper import web
from mock import patch
from pybossa.model.app import App
from pybossa.model.user import User
from pybossa.jobs import import_tasks
from factories import AppFactory


class TestAutoimporter(web.Helper):
    def test_autoimporter_get_redirects_to_login_if_anonymous(self):
        """Test task autoimporter endpoint requires login"""
        app = AppFactory.create()
        url = "/app/%s/tasks/autoimporter" % app.short_name

        res = self.app.get(url)
        redirect_url = 'http://localhost/account/signin?next='
        assert res.status_code == 302, res.status_code
        assert redirect_url in res.location, res.location

    def test_autoimporter_get_forbidden_non_owner(self):
        """Test task autoimporter returns Forbidden if non owner accesses"""
        self.register()
        self.new_application()
        app = db.session.query(App).first()
        self.signout()
        self.register(name='non-owner')
        url = "/app/%s/tasks/autoimporter" % app.short_name

        res = self.app.get(url)

        assert res.status_code == 403, res.status_code

    def test_autoimporter_get_forbidden_owner_no_pro(self):
        """Test task autoimporter returns Forbidden if no pro accesses"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        self.new_application()
        app = db.session.query(App).first()
        url = "/app/%s/tasks/autoimporter" % app.short_name

        res = self.app.get(url, follow_redirects=True)
        assert  res.status_code == 403, res.status_code

    def test_autoimporter_get_owner_pro(self):
        """Test task autoimporter works for pro user"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        owner = db.session.query(User).filter_by(name="owner").first()
        owner.pro = True
        db.session.commit()

        self.new_application()
        app = db.session.query(App).first()
        url = "/app/%s/tasks/autoimporter" % app.short_name

        res = self.app.get(url, follow_redirects=True)
        assert  res.status_code == 200, res.status_code

    def test_autoimporter_get_admin(self):
        """Test task autoimporter works for admin user"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        self.new_application()
        self.signout()
        self.signin()
        app = db.session.query(App).first()
        url = "/app/%s/tasks/autoimporter" % app.short_name

        res = self.app.get(url, follow_redirects=True)
        assert  res.status_code == 200, res.status_code

    def test_autoimporter_get_nonexisting_project(self):
        """Test task autoimporter to a non existing project returns 404"""
        self.register()
        res = self.app.get("/app/noExists/tasks/autoimporter")

        assert res.status_code == 404, res.status_code

    def test_autoimporter_post_redirects_to_login_if_anonymous(self):
        """Test task autoimporter endpoint post requires login"""
        app = AppFactory.create()
        url = "/app/%s/tasks/autoimporter" % app.short_name

        res = self.app.post(url, data={})
        redirect_url = 'http://localhost/account/signin?next='
        assert res.status_code == 302, res.status_code
        assert redirect_url in res.location, res.location

    def test_autoimporter_post_forbidden_non_owner(self):
        """Test task autoimporter post returns Forbidden if non owner accesses"""
        self.register()
        self.new_application()
        app = db.session.query(App).first()
        self.signout()
        self.register(name='non-owner')
        url = "/app/%s/tasks/autoimporter" % app.short_name

        res = self.app.post(url, data={})

        assert res.status_code == 403, res.status_code

    def test_autoimporter_post_forbidden_owner_no_pro(self):
        """Test task autoimporter post returns Forbidden if no pro accesses"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        self.new_application()
        app = db.session.query(App).first()
        url = "/app/%s/tasks/autoimporter" % app.short_name

        res = self.app.post(url, data={}, follow_redirects=True)
        assert  res.status_code == 403, res.status_code

    def test_autoimporter_post_owner_pro(self):
        """Test task autoimporter post works for pro user"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        owner = db.session.query(User).filter_by(name="owner").first()
        owner.pro = True
        db.session.commit()

        self.new_application()
        app = db.session.query(App).first()
        url = "/app/%s/tasks/autoimporter" % app.short_name

        res = self.app.post(url, data={'csv_url': 'http://as.com',
                                       'formtype': 'json', 'form_name': 'csv'},
                                       follow_redirects=True)
        assert  res.status_code == 200, res.status_code

    def test_autoimporter_post_admin(self):
        """Test task autoimporter post works for admin user"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        self.new_application()
        self.signout()
        self.signin()
        app = db.session.query(App).first()
        url = "/app/%s/tasks/autoimporter" % app.short_name

        res = self.app.post(url, data={'csv_url': 'http://as.com',
                                       'formtype': 'json', 'form_name': 'csv'},
                                       follow_redirects=True)
        assert  res.status_code == 200, res.status_code

    def test_autoimporter_post_nonexisting_project(self):
        """Test task autoimporter post to a non existing project returns 404"""
        self.register()
        res = self.app.post("/app/noExists/tasks/autoimporter", data={})

        assert res.status_code == 404, res.status_code

    def test_delete_autoimporter_post_redirects_to_login_if_anonymous(self):
        """Test delete task autoimporter endpoint requires login"""
        app = AppFactory.create()
        url = "/app/%s/tasks/autoimporter/delete" % app.short_name

        res = self.app.post(url, data={})
        redirect_url = 'http://localhost/account/signin?next='
        assert res.status_code == 302, res.status_code
        assert redirect_url in res.location, res.location

    def test_delete_autoimporter_post_forbidden_non_owner(self):
        """Test delete task autoimporter returns Forbidden if non owner accesses"""
        self.register()
        self.new_application()
        app = db.session.query(App).first()
        self.signout()
        self.register(name='non-owner')
        url = "/app/%s/tasks/autoimporter/delete" % app.short_name

        res = self.app.post(url, data={})

        assert res.status_code == 403, res.status_code

    def test_delete_autoimporter_post_forbidden_owner_no_pro(self):
        """Test delete task autoimporter returns Forbidden if no pro accesses"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        self.new_application()
        app = db.session.query(App).first()
        url = "/app/%s/tasks/autoimporter/delete" % app.short_name

        res = self.app.post(url, data={}, follow_redirects=True)
        assert  res.status_code == 403, res.status_code

    def test_delete_autoimporter_post_owner_pro(self):
        """Test delete task autoimporter works for pro user"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        owner = db.session.query(User).filter_by(name="owner").first()
        owner.pro = True
        db.session.commit()

        self.new_application()
        app = db.session.query(App).first()
        url = "/app/%s/tasks/autoimporter/delete" % app.short_name

        res = self.app.post(url, data={}, follow_redirects=True)
        assert  res.status_code == 200, res.status_code


    def test_delete_autoimporter_post_admin(self):
        """Test delete task autoimporter works for admin user"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        self.new_application()
        self.signout()
        self.signin()
        app = db.session.query(App).first()
        url = "/app/%s/tasks/autoimporter/delete" % app.short_name

        res = self.app.post(url, data={}, follow_redirects=True)
        assert  res.status_code == 200, res.status_code

    def test_delete_autoimporter_get_nonexisting_project(self):
        """Test task delete autoimporter to a non existing project returns 404"""
        self.register()
        res = self.app.post("/app/noExists/tasks/autoimporter/delete")

        assert res.status_code == 404, res.status_code
