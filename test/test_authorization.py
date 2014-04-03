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

from base import web, model, Fixtures, db, redis_flushall, assert_not_raises
from pybossa.auth import require
from pybossa.auth import token as token_authorization
from pybossa.model import TaskRun, Task
from nose.tools import assert_equal, assert_raises
from werkzeug.exceptions import Forbidden, Unauthorized
from mock import patch, Mock




def setup_module():
    model.rebuild_db()


def teardown_module():
    db.session.remove()
    model.rebuild_db()
    redis_flushall()


def mock_current_user(anonymous=True, admin=None, id=None):
    mock = Mock(spec=model.User)
    mock.is_anonymous.return_value = anonymous
    mock.admin = admin
    mock.id = id
    return mock



class TestBlogpostAuthorization:

    mock_anonymous = mock_current_user()
    mock_authenticated = mock_current_user(anonymous=False, admin=False, id=2)
    mock_admin = mock_current_user(anonymous=False, admin=True, id=1)

    def setUp(self):
        model.rebuild_db()

    def tearDown(self):
        db.session.remove()
        redis_flushall()


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.blogpost.current_user', new=mock_anonymous)
    def test_anonymous_user_create_blogpost(self):
        """Test anonymous users cannot create blogposts"""

        with web.app.test_request_context('/'):
            root, user1, user2 = Fixtures.create_users()
            app = Fixtures.create_app('')
            app.owner = user1
            db.session.add_all([app, user1])
            db.session.commit()

            blogpost = model.Blogpost(title='title', app=app, owner=None)

            assert_raises(Unauthorized, getattr(require, 'blogpost').create, blogpost)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.blogpost.current_user', new=mock_admin)
    def test_non_owner_authenticated_user_create_blogpost(self):
        """Test authenticated user cannot create blogpost if is not the app owner"""

        with web.app.test_request_context('/'):
            root, user1, user2 = Fixtures.create_users()
            app = Fixtures.create_app('')
            app.owner = user1
            db.session.add_all([app, root, user1])
            db.session.commit()

            blogpost = model.Blogpost(title='title', app=app, owner=root)

            assert_raises(Forbidden, getattr(require, 'blogpost').create, blogpost)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.blogpost.current_user', new=mock_authenticated)
    def test_owner_create_blogpost(self):
        """Test authenticated user can create blogpost if is app owner"""

        with web.app.test_request_context('/'):
            root, user1, user2 = Fixtures.create_users()
            app = Fixtures.create_app('')
            app.owner = user1
            db.session.add_all([app, user1])
            db.session.commit()

            blogpost = model.Blogpost(title='title', app=app, owner=user1)

            assert_not_raises(Exception, getattr(require, 'blogpost').create, blogpost)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.blogpost.current_user', new=mock_anonymous)
    def test_anonymous_user_read_blogpost(self):
        """Test anonymous users can read blogposts"""

        with web.app.test_request_context('/'):
            root, user1, user2 = Fixtures.create_users()
            app = Fixtures.create_app('')
            app.owner = user1
            blogpost = model.Blogpost(title='title', app=app, owner=None)
            db.session.add_all([app, user1, blogpost])
            db.session.commit()

            assert_not_raises(Exception, getattr(require, 'blogpost').read, blogpost)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.blogpost.current_user', new=mock_admin)
    def test_non_owner_authenticated_user_read_blogpost(self):
        """Test authenticated user can read blogpost if is not the app owner"""

        with web.app.test_request_context('/'):
            root, user1, user2 = Fixtures.create_users()
            app = Fixtures.create_app('')
            app.owner = user1
            blogpost = model.Blogpost(title='title', app=app, owner=root)
            db.session.add_all([app, root, user1, blogpost])
            db.session.commit()

            assert_not_raises(Exception, getattr(require, 'blogpost').read, blogpost)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.blogpost.current_user', new=mock_authenticated)
    def test_owner_read_blogpost(self):
        """Test authenticated user can read blogpost if is the app owner"""

        with web.app.test_request_context('/'):
            root, user1, user2 = Fixtures.create_users()
            app = Fixtures.create_app('')
            app.owner = user1
            blogpost = model.Blogpost(title='title', app=app, owner=user1)
            db.session.add_all([app, user1, blogpost])
            db.session.commit()

            assert_not_raises(Exception, getattr(require, 'blogpost').read, blogpost)





class TestTaskrunAuthorization:

    mock_anonymous = mock_current_user()
    mock_authenticated = mock_current_user(anonymous=False, admin=False, id=2)
    mock_admin = mock_current_user(anonymous=False, admin=True, id=1)


    def setUp(self):
        model.rebuild_db()
        self.root, self.user1, self.user2 = Fixtures.create_users()
        db.session.add_all([self.root, self.user1, self.user2])
        self.app = Fixtures.create_app('')
        self.app.owner = self.root
        db.session.add(self.app)
        db.session.commit()
        self.task = model.Task(app_id=self.app.id, state='0', n_answers=10)
        self.task.app = self.app
        db.session.add(self.task)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        redis_flushall()



    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_create_first_taskrun(self):
        """Test anonymous user can create a taskrun for a given task if he
        hasn't already done it"""

        with web.app.test_request_context('/'):
            taskrun = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user_ip='127.0.0.0',
                                    info="some taskrun info")
            assert_not_raises(Exception,
                          getattr(require, 'taskrun').create,
                          taskrun)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_create_repeated_taskrun(self):
        """Test anonymous user cannot create a taskrun for a task to which
        he has previously posted a taskrun"""

        with web.app.test_request_context('/'):
            taskrun1 = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user_ip='127.0.0.0',
                                    info="some taskrun info")
            db.session.add(taskrun1)
            db.session.commit()
            taskrun2 = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user_ip='127.0.0.0',
                                    info="a different taskrun info")
            assert_raises(Forbidden,
                        getattr(require, 'taskrun').create,
                        taskrun2)

            # But the user can still create taskruns for different tasks
            task2 = model.Task(app_id=self.app.id, state='0', n_answers=10)
            task2.app = self.app
            db.session.add(task2)
            db.session.commit()
            taskrun3 = model.TaskRun(app_id=self.app.id,
                                    task_id=task2.id,
                                    user_ip='127.0.0.0',
                                    info="some taskrun info")
            assert_not_raises(Exception,
                          getattr(require, 'taskrun').create,
                          taskrun3)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_create_first_taskrun(self):
        """Test authenticated user can create a taskrun for a given task if he
        hasn't already done it"""

        with web.app.test_request_context('/'):
            taskrun = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user_id=self.mock_authenticated.id,
                                    info="some taskrun info")
            assert_not_raises(Exception,
                          getattr(require, 'taskrun').create,
                          taskrun)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_create_repeated_taskrun(self):
        """Test authenticated user cannot create a taskrun for a task to which
        he has previously posted a taskrun"""

        with web.app.test_request_context('/'):
            taskrun1 = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user=self.user1,
                                    info="some taskrun info")
            db.session.add(taskrun1)
            db.session.commit()
            taskrun2 = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user=self.user1,
                                    info="a different taskrun info")
            assert_raises(Forbidden, getattr(require, 'taskrun').create, taskrun2)

            # But the user can still create taskruns for different tasks
            task2 = model.Task(app_id=self.app.id, state='0', n_answers=10)
            task2.app = self.app
            db.session.add(task2)
            db.session.commit()
            taskrun3 = model.TaskRun(app_id=self.app.id,
                                    task_id=task2.id,
                                    user_id=self.mock_authenticated.id,
                                    info="some taskrun info")
            assert_not_raises(Exception,
                          getattr(require, 'taskrun').create,
                          taskrun3)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_read(self):
        """Test anonymous user can read any taskrun"""

        with web.app.test_request_context('/'):
            anonymous_taskrun = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user_ip='127.0.0.0',
                                    info="some taskrun info")
            user_taskrun = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user_id=self.root.id,
                                    info="another taskrun info")

            assert_not_raises(Exception,
                          getattr(require, 'taskrun').read,
                          anonymous_taskrun)
            assert_not_raises(Exception,
                          getattr(require, 'taskrun').read,
                          user_taskrun)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_read(self):
        """Test authenticated user can read any taskrun"""

        with web.app.test_request_context('/'):
            anonymous_taskrun = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user_ip='127.0.0.0',
                                    info="some taskrun info")
            other_users_taskrun = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user_id=self.root.id,
                                    info="a different taskrun info")
            own_taskrun = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user_id=self.mock_authenticated.id,
                                    info="another taskrun info")

            assert_not_raises(Exception,
                          getattr(require, 'taskrun').read,
                          anonymous_taskrun)
            assert_not_raises(Exception,
                          getattr(require, 'taskrun').read,
                          other_users_taskrun)
            assert_not_raises(Exception,
                          getattr(require, 'taskrun').read,
                          own_taskrun)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_update_anoymous_taskrun(self):
        """Test anonymous users cannot update an anonymously posted taskrun"""

        with web.app.test_request_context('/'):
            anonymous_taskrun = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user_ip='127.0.0.0',
                                    info="some taskrun info")

            assert_raises(Unauthorized,
                          getattr(require, 'taskrun').update,
                          anonymous_taskrun)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_update_anonymous_taskrun(self):
        """Test authenticated users cannot update an anonymously posted taskrun"""

        with web.app.test_request_context('/'):
            anonymous_taskrun = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user_ip='127.0.0.0',
                                    info="some taskrun info")

            assert_raises(Forbidden,
                          getattr(require, 'taskrun').update,
                          anonymous_taskrun)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.taskrun.current_user', new=mock_admin)
    def test_admin_update_anonymous_taskrun(self):
        """Test admins cannot update anonymously posted taskruns"""

        with web.app.test_request_context('/'):
            anonymous_taskrun = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user_ip='127.0.0.0',
                                    info="some taskrun info")

            assert_raises(Forbidden,
                          getattr(require, 'taskrun').update,
                          anonymous_taskrun)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_update_user_taskrun(self):
        """Test anonymous user cannot update taskruns posted by authenticated users"""
        with web.app.test_request_context('/'):
            user_taskrun = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user_id=self.root.id,
                                    info="some taskrun info")

            assert_raises(Unauthorized,
                          getattr(require, 'taskrun').update,
                          user_taskrun)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_update_other_users_taskrun(self):
        """Test authenticated user cannot update any taskrun"""

        with web.app.test_request_context('/'):
            own_taskrun = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user_id=self.mock_authenticated.id,
                                    info="some taskrun info")
            other_users_taskrun = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user_id=self.root.id,
                                    info="a different taskrun info")

            assert_raises(Forbidden,
                          getattr(require, 'taskrun').update,
                          own_taskrun)
            assert_raises(Forbidden,
                          getattr(require, 'taskrun').update,
                          other_users_taskrun)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.taskrun.current_user', new=mock_admin)
    def test_admin_update_user_taskrun(self):
        """Test admins cannot update taskruns posted by authenticated users"""

        with web.app.test_request_context('/'):
                user_taskrun = model.TaskRun(app_id=self.app.id,
                                        task_id=self.task.id,
                                        user_id=self.user1.id,
                                        info="some taskrun info")

                assert_raises(Forbidden,
                              getattr(require, 'taskrun').update,
                              user_taskrun)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_delete_anonymous_taskrun(self):
        """Test anonymous users cannot delete an anonymously posted taskrun"""

        with web.app.test_request_context('/'):
            anonymous_taskrun = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user_ip='127.0.0.0',
                                    info="some taskrun info")

            assert_raises(Unauthorized,
                          getattr(require, 'taskrun').delete,
                          anonymous_taskrun)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_delete_anonymous_taskrun(self):
        """Test authenticated users cannot delete an anonymously posted taskrun"""

        with web.app.test_request_context('/'):
                    anonymous_taskrun = model.TaskRun(app_id=self.app.id,
                                            task_id=self.task.id,
                                            user_ip='127.0.0.0',
                                            info="some taskrun info")

                    assert_raises(Forbidden,
                                  getattr(require, 'taskrun').delete,
                                  anonymous_taskrun)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.taskrun.current_user', new=mock_admin)
    def test_admin_delete_anonymous_taskrun(self):
        """Test admins can delete anonymously posted taskruns"""

        with web.app.test_request_context('/'):
            anonymous_taskrun = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user_ip='127.0.0.0',
                                    info="some taskrun info")

            assert_not_raises(Exception,
                          getattr(require, 'taskrun').delete,
                          anonymous_taskrun)

    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_delete_user_taskrun(self):
        """Test anonymous user cannot delete taskruns posted by authenticated users"""

        with web.app.test_request_context('/'):
            user_taskrun = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user_id=self.root.id,
                                    info="some taskrun info")

            assert_raises(Unauthorized,
                      getattr(require, 'taskrun').delete,
                      user_taskrun)

    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_delete_other_users_taskrun(self):
        """Test authenticated user cannot delete a taskrun if it was created
        by another authenticated user, but can delete his own taskruns"""

        with web.app.test_request_context('/'):
            own_taskrun = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user_id=self.mock_authenticated.id,
                                    info="some taskrun info")
            other_users_taskrun = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user_id=self.root.id,
                                    info="a different taskrun info")

            assert_not_raises(Exception,
                      getattr(require, 'taskrun').delete,
                      own_taskrun)
            assert_raises(Forbidden,
                      getattr(require, 'taskrun').delete,
                      other_users_taskrun)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.taskrun.current_user', new=mock_admin)
    def test_admin_delete_user_taskrun(self):
        """Test admins can delete taskruns posted by authenticated users"""

        with web.app.test_request_context('/'):
            user_taskrun = model.TaskRun(app_id=self.app.id,
                                    task_id=self.task.id,
                                    user_id=self.user1.id,
                                    info="some taskrun info")

            assert_not_raises(Exception,
                      getattr(require, 'taskrun').delete,
                      user_taskrun)



class TestTokenAuthorization:

    auth_providers = ('twitter', 'facebook', 'google')
    mock_anonymous = mock_current_user()
    mock_authenticated = mock_current_user(anonymous=False, admin=False, id=2)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_delete(self):
        """Test anonymous user is not allowed to delete an oauth token"""
        with web.app.test_request_context('/'):
            for token in self.auth_providers:
                assert_raises(Unauthorized,
                          getattr(require, 'token').delete,
                          token)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_delete(self):
        """Test authenticated user is not allowed to delete an oauth token"""
        with web.app.test_request_context('/'):
            for token in self.auth_providers:
                assert_raises(Forbidden,
                          getattr(require, 'token').delete,
                          token)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_create(self):
        """Test anonymous user is not allowed to create an oauth token"""
        with web.app.test_request_context('/'):
            for token in self.auth_providers:
                assert_raises(Unauthorized,
                          getattr(require, 'token').create,
                          token)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_create(self):
        """Test authenticated user is not allowed to create an oauth token"""
        with web.app.test_request_context('/'):
            for token in self.auth_providers:
                assert_raises(Forbidden,
                          getattr(require, 'token').create,
                          token)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_update(self):
        """Test anonymous user is not allowed to update an oauth token"""
        with web.app.test_request_context('/'):
            for token in self.auth_providers:
                assert_raises(Unauthorized,
                          getattr(require, 'token').update,
                          token)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_update(self):
        """Test authenticated user is not allowed to update an oauth token"""
        with web.app.test_request_context('/'):
            for token in self.auth_providers:
                assert_raises(Forbidden,
                          getattr(require, 'token').update,
                          token)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_read(self):
        """Test anonymous user is not allowed to read an oauth token"""
        with web.app.test_request_context('/'):
            for token in self.auth_providers:
                assert_raises(Unauthorized,
                          getattr(require, 'token').read,
                          token)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_read(self):
        """Test authenticated user is allowed to read his own oauth tokens"""
        with web.app.test_request_context('/'):
            for token in self.auth_providers:
                assert_raises(Forbidden,
                          getattr(require, 'token').read,
                          token)

