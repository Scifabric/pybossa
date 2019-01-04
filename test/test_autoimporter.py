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
from default import db, with_context
from helper import web
from pybossa.jobs import import_tasks
from factories import ProjectFactory
from pybossa.repositories import UserRepository
from pybossa.repositories import ProjectRepository
from mock import patch, MagicMock
from mock import patch

project_repo = ProjectRepository(db)
user_repo = UserRepository(db)

class TestAutoimporterAccessAndResponses(web.Helper):

    @with_context
    def test_autoimporter_get_redirects_to_login_if_anonymous(self):
        """Test task autoimporter endpoint requires login"""
        project = ProjectFactory.create()
        url = "/project/%s/tasks/autoimporter" % project.short_name

        res = self.app.get(url)
        redirect_url = 'https://localhost/account/signin?next='
        assert res.status_code == 302, res.status_code
        assert redirect_url in res.location, res.location


    @with_context
    def test_autoimporter_get_forbidden_non_owner(self):
        """Test task autoimporter returns Forbidden if non owner accesses"""
        self.register()
        self.new_project()
        project = project_repo.get(1)
        self.signout()
        self.register(name='non-owner')
        url = "/project/%s/tasks/autoimporter" % project.short_name

        res = self.app.get(url)

        assert res.status_code == 403, res.status_code


    @with_context
    def test_autoimporter_get_forbidden_owner_no_pro(self):
        """Test task autoimporter returns Forbidden if no pro accesses"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        self.new_project()
        project = project_repo.get(1)
        url = "/project/%s/tasks/autoimporter" % project.short_name

        res = self.app.get(url, follow_redirects=True)
        assert  res.status_code == 403, res.status_code


    @with_context
    def test_autoimporter_get_owner_pro(self):
        """Test task autoimporter works for pro user"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        owner = user_repo.get_by_name("owner")
        owner.pro = True
        user_repo.save(owner)

        self.new_project()
        project = project_repo.get(1)
        url = "/project/%s/tasks/autoimporter" % project.short_name

        res = self.app.get(url, follow_redirects=True)
        assert  res.status_code == 200, res.status_code


    @with_context
    def test_autoimporter_get_admin(self):
        """Test task autoimporter works for admin user"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        self.new_project()
        self.signout()
        self.signin()
        project = project_repo.get(1)
        url = "/project/%s/tasks/autoimporter" % project.short_name

        res = self.app.get(url, follow_redirects=True)
        assert  res.status_code == 200, res.status_code


    @with_context
    def test_autoimporter_get_nonexisting_project(self):
        """Test task autoimporter to a non existing project returns 404"""
        self.register()
        res = self.app.get("/project/noExists/tasks/autoimporter")

        assert res.status_code == 404, res.status_code


    @with_context
    def test_autoimporter_post_redirects_to_login_if_anonymous(self):
        """Test task autoimporter endpoint post requires login"""
        project = ProjectFactory.create()
        url = "/project/%s/tasks/autoimporter" % project.short_name

        res = self.app.post(url, data={})
        redirect_url = 'https://localhost/account/signin?next='
        assert res.status_code == 302, res.status_code
        assert redirect_url in res.location, res.location


    @with_context
    def test_autoimporter_post_forbidden_non_owner(self):
        """Test task autoimporter post returns Forbidden if non owner accesses"""
        self.register()
        self.new_project()
        project = project_repo.get(1)
        self.signout()
        self.register(name='non-owner')
        url = "/project/%s/tasks/autoimporter" % project.short_name

        res = self.app.post(url, data={})

        assert res.status_code == 403, res.status_code


    @with_context
    def test_autoimporter_post_forbidden_owner_no_pro(self):
        """Test task autoimporter post returns Forbidden if no pro accesses"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        self.new_project()
        project = project_repo.get(1)
        url = "/project/%s/tasks/autoimporter" % project.short_name

        res = self.app.post(url, data={}, follow_redirects=True)
        assert  res.status_code == 403, res.status_code


    @with_context
    def test_autoimporter_post_owner_pro(self):
        """Test task autoimporter post works for pro user"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        owner = user_repo.get_by_name("owner")
        owner.pro = True
        user_repo.save(owner)

        self.new_project()
        project = project_repo.get(1)
        url = "/project/%s/tasks/autoimporter" % project.short_name

        res = self.app.post(url, data={'csv_url': 'http://as.com',
                                       'formtype': 'json', 'form_name': 'csv'},
                                       follow_redirects=True)
        assert  res.status_code == 200, res.status_code


    @with_context
    def test_autoimporter_post_admin(self):
        """Test task autoimporter post works for admin user"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        self.new_project()
        self.signout()
        self.signin()
        project = project_repo.get(1)
        url = "/project/%s/tasks/autoimporter" % project.short_name

        res = self.app.post(url, data={'csv_url': 'http://as.com',
                                       'formtype': 'json', 'form_name': 'csv'},
                                       follow_redirects=True)
        assert  res.status_code == 200, res.status_code


    @with_context
    def test_autoimporter_post_nonexisting_project(self):
        """Test task autoimporter post to a non existing project returns 404"""
        self.register()
        res = self.app.post("/project/noExists/tasks/autoimporter", data={})

        assert res.status_code == 404, res.status_code


    @with_context
    def test_delete_autoimporter_post_redirects_to_login_if_anonymous(self):
        """Test delete task autoimporter endpoint requires login"""
        project = ProjectFactory.create()
        url = "/project/%s/tasks/autoimporter/delete" % project.short_name

        res = self.app.post(url, data={})
        redirect_url = 'https://localhost/account/signin?next='
        assert res.status_code == 302, res.status_code
        assert redirect_url in res.location, res.location


    @with_context
    def test_delete_autoimporter_post_forbidden_non_owner(self):
        """Test delete task autoimporter returns Forbidden if non owner accesses"""
        self.register()
        self.new_project()
        project = project_repo.get(1)
        self.signout()
        self.register(name='non-owner')
        url = "/project/%s/tasks/autoimporter/delete" % project.short_name

        res = self.app.post(url, data={})

        assert res.status_code == 403, res.status_code


    @with_context
    def test_delete_autoimporter_post_forbidden_owner_no_pro(self):
        """Test delete task autoimporter returns Forbidden if no pro accesses"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        self.new_project()
        project = project_repo.get(1)
        url = "/project/%s/tasks/autoimporter/delete" % project.short_name

        res = self.app.post(url, data={}, follow_redirects=True)
        assert  res.status_code == 403, res.status_code


    @with_context
    def test_delete_autoimporter_post_owner_pro(self):
        """Test delete task autoimporter works for pro user"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        owner = user_repo.get_by_name("owner")
        owner.pro = True
        user_repo.save(owner)

        self.new_project()
        project = project_repo.get(1)
        url = "/project/%s/tasks/autoimporter/delete" % project.short_name

        res = self.app.post(url, data={}, follow_redirects=True)
        assert  res.status_code == 200, res.status_code


    @with_context
    def test_delete_autoimporter_post_admin(self):
        """Test delete task autoimporter works for admin user"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        self.new_project()
        self.signout()
        self.signin()
        project = project_repo.get(1)
        url = "/project/%s/tasks/autoimporter/delete" % project.short_name

        res = self.app.post(url, data={}, follow_redirects=True)
        assert  res.status_code == 200, res.status_code


    @with_context
    def test_delete_autoimporter_get_nonexisting_project(self):
        """Test task delete autoimporter to a non existing project returns 404"""
        self.register()
        res = self.app.post("/project/noExists/tasks/autoimporter/delete")

        assert res.status_code == 404, res.status_code



class TestAutoimporterBehaviour(web.Helper):

    @with_context
    def test_autoimporter_shows_template_to_create_new_if_no_autoimporter(self):
        """Test task autoimporter get renders the template for creating new
        autoimporter if none exists"""
        self.register()
        owner = user_repo.get(1)
        project = ProjectFactory.create(owner=owner)
        url = "/project/%s/tasks/autoimporter" % project.short_name
        expected_text = "Setup task autoimporter"

        res = self.app.get(url, follow_redirects=True)

        assert expected_text in str(res.data)
        assert 'CSV' in str(res.data)
        assert 'Google Drive Spreadsheet' in str(res.data)
        assert 'EpiCollect Plus Project' in str(res.data)
        assert 'Flickr' in str(res.data)
        assert 'Twitter' in str(res.data)
        assert 'Dropbox' not in str(res.data)


    @with_context
    @patch('pybossa.core.importer.get_autoimporter_names')
    def test_autoimporter_doesnt_show_unavailable_importers(self, names):
        names.return_value = ['csv', 'gdocs', 'epicollect']
        self.register()
        owner = user_repo.get(1)
        project = ProjectFactory.create(owner=owner)
        url = "/project/%s/tasks/autoimporter" % project.short_name

        res = self.app.get(url, follow_redirects=True)

        assert 'Flickr' not in str(res.data)


    @with_context
    def test_autoimporter_with_specific_variant_argument(self):
        """Test task autoimporter with specific autoimporter variant argument
        shows the form for it, for each of the variants"""
        self.register()
        owner = user_repo.get(1)
        project = ProjectFactory.create(owner=owner)

        # CSV
        url = "/project/%s/tasks/autoimporter?type=csv" % project.short_name
        res = self.app.get(url, follow_redirects=True)
        data = res.data.decode('utf-8')

        assert "From a CSV file" in data
        assert 'action="/project/%E2%9C%93project1/tasks/autoimporter"' in data

        # Google Docs
        url = "/project/%s/tasks/autoimporter?type=gdocs" % project.short_name
        res = self.app.get(url, follow_redirects=True)
        data = res.data.decode('utf-8')

        assert "From a Google Docs Spreadsheet" in data
        assert 'action="/project/%E2%9C%93project1/tasks/autoimporter"' in data

        # Epicollect Plus
        url = "/project/%s/tasks/autoimporter?type=epicollect" % project.short_name
        res = self.app.get(url, follow_redirects=True)
        data = res.data.decode('utf-8')

        assert "From an EpiCollect Plus project" in data
        assert 'action="/project/%E2%9C%93project1/tasks/autoimporter"' in data

        # Flickr
        url = "/project/%s/tasks/autoimporter?type=flickr" % project.short_name
        res = self.app.get(url, follow_redirects=True)
        data = res.data.decode('utf-8')

        assert "From a Flickr Album" in data
        assert 'action="/project/%E2%9C%93project1/tasks/autoimporter"' in data

        # Twitter
        url = "/project/%s/tasks/autoimporter?type=twitter" % project.short_name
        res = self.app.get(url, follow_redirects=True)
        data = res.data.decode('utf-8')

        assert "From a Twitter hashtag or account" in data
        assert 'action="/project/%E2%9C%93project1/tasks/autoimporter"' in data

        # Dropbox
        url = "/project/%s/tasks/autoimporter?type=dropbox" % project.short_name
        res = self.app.get(url, follow_redirects=True)
        data = res.data.decode('utf-8')

        assert res.status_code == 404, res.status_code

        # Invalid
        url = "/project/%s/tasks/autoimporter?type=invalid" % project.short_name
        res = self.app.get(url, follow_redirects=True)

        assert res.status_code == 404, res.status_code


    @with_context
    def test_autoimporter_shows_current_autoimporter_if_exists(self):
        """Test task autoimporter shows the current autoimporter if exists"""
        self.register()
        owner = user_repo.get(1)
        autoimporter = {'type': 'csv', 'csv_url': 'http://fakeurl.com'}
        project = ProjectFactory.create(owner=owner, info={'autoimporter': autoimporter})
        url = "/project/%s/tasks/autoimporter" % project.short_name

        res = self.app.get(url, follow_redirects=True)

        assert "You currently have the following autoimporter" in str(res.data)


    @with_context
    def test_autoimporter_post_creates_autoimporter_attribute(self):
        """Test a valid post to autoimporter endpoint sets an autoimporter to
        the project"""
        self.register()
        owner = user_repo.get(1)
        autoimporter = {'type': 'csv', 'csv_url': 'http://fakeurl.com'}
        project = ProjectFactory.create(owner=owner)
        url = "/project/%s/tasks/autoimporter" % project.short_name
        data = {'form_name': 'csv', 'csv_url': 'http://fakeurl.com'}

        self.app.post(url, data=data, follow_redirects=True)

        assert project.has_autoimporter() is True, project.get_autoimporter()
        assert project.get_autoimporter() == autoimporter, project.get_autoimporter()


    @with_context
    def test_autoimporter_prevents_from_duplicated(self):
        """Test a valid post to autoimporter endpoint will not create another
        autoimporter if one exists for that project"""
        self.register()
        owner = user_repo.get(1)
        autoimporter = {'type': 'csv', 'csv_url': 'http://fakeurl.com'}
        project = ProjectFactory.create(owner=owner, info={'autoimporter': autoimporter})
        url = "/project/%s/tasks/autoimporter" % project.short_name
        data = {'form_name': 'gdocs', 'googledocs_url': 'http://another.com'}

        res = self.app.post(url, data=data, follow_redirects=True)

        assert project.get_autoimporter() == autoimporter, project.get_autoimporter()


    @with_context
    def test_delete_autoimporter_deletes_current_autoimporter_job(self):
        self.register()
        owner = user_repo.get(1)
        autoimporter = {'type': 'csv', 'csv_url': 'http://fakeurl.com'}
        project = ProjectFactory.create(owner=owner, info={'autoimporter': autoimporter})
        url = "/project/%s/tasks/autoimporter/delete" % project.short_name

        res = self.app.post(url, data={}, follow_redirects=True)

        assert project.has_autoimporter() is False, project.get_autoimporter()


    @with_context
    def test_flickr_autoimporter_page_shows_option_to_log_in_to_flickr(self):
        self.register()
        owner = user_repo.get(1)
        project = ProjectFactory.create(owner=owner)
        url = "/project/%s/tasks/autoimporter?type=flickr" % project.short_name

        res = self.app.get(url)
        login_url = '/flickr/?next=%2Fproject%2F%25E2%259C%2593project1%2Ftasks%2Fautoimporter%3Ftype%3Dflickr'

        assert login_url in str(res.data)
