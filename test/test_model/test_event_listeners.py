# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
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

from default import Test, with_context
from factories import TaskFactory, TaskRunFactory
from mock import patch, MagicMock
from pybossa.core import task_repo, result_repo
from pybossa.model.event_listeners import *
from pybossa.jobs import notify_blog_users


"""Tests for model event listeners."""



class TestModelEventListeners(Test):

    @with_context
    @patch('pybossa.model.event_listeners.update_feed')
    @patch('pybossa.model.event_listeners.mail_queue')
    def test_add_blog_event(self, mock_queue, mock_update_feed):
        """Test add_blog_event is called."""
        conn = MagicMock()
        target = MagicMock()
        target.id = 1
        target.project_id = 1
        tmp = MagicMock()
        tmp.name = 'name'
        tmp.short_name = 'short_name'
        tmp.info = dict()
        conn.execute.return_value = [tmp]
        add_blog_event(None, conn, target)
        mock_queue.enqueue.assert_called_with(notify_blog_users,
                                              blog_id=target.id,
                                              project_id=target.project_id)
        assert mock_update_feed.called

    @with_context
    @patch('pybossa.model.event_listeners.update_feed')
    def test_add_project_event(self, mock_update_feed):
        """Test add_project_event is called."""
        conn = MagicMock()
        target = MagicMock()
        target.id = 1
        target.project_id = 1
        tmp = MagicMock()
        tmp.name = 'name'
        tmp.short_name = 'short_name'
        tmp.info = dict()
        conn.execute.return_value = [tmp]
        add_project_event(None, conn, target)
        assert mock_update_feed.called

    @with_context
    @patch('pybossa.model.event_listeners.update_feed')
    def test_add_task_event(self, mock_update_feed):
        """Test add_task_event is called."""
        conn = MagicMock()
        target = MagicMock()
        target.id = 1
        target.project_id = 1
        tmp = MagicMock()
        tmp.name = 'name'
        tmp.short_name = 'short_name'
        tmp.info = dict()
        conn.execute.return_value = [tmp]
        add_task_event(None, conn, target)
        assert mock_update_feed.called

    @with_context
    @patch('pybossa.model.event_listeners.update_feed')
    def test_add_user_event(self, mock_update_feed):
        """Test add_user_event is called."""
        conn = MagicMock()
        target = MagicMock()
        target.id = 1
        target.project_id = 1
        tmp = MagicMock()
        tmp.name = 'name'
        tmp.short_name = 'short_name'
        tmp.info = dict()
        conn.execute.return_value = [tmp]
        add_user_event(None, conn, target)
        assert mock_update_feed.called

    @with_context
    @patch('pybossa.model.event_listeners.create_result')
    def test_create_result_event(self, mock_create_result):
        """Test create_result is called."""
        from pybossa.core import db
        task = TaskFactory.create(n_answers=1)
        TaskRunFactory.create(task=task)
        conn = db.engine.connect()
        result_id = create_result(conn, task.project_id, task.id)
        result = result_repo.filter_by(project_id=task.project_id,
                                       task_id=task.id,
                                       last_version=True)[0]

        assert mock_create_result.called
        err_msg = "The result should ID should be the same"
        assert result_id == result.id, err_msg

        task.n_answers = 2
        task_repo.update(task)
        TaskRunFactory.create(task=task)

        result_id = create_result(conn, task.project_id, task.id)
        assert mock_create_result.called
        result = result_repo.filter_by(project_id=task.project_id,
                                       task_id=task.id,
                                       last_version=True)
        assert len(result) == 1, len(result)
        result = result[0]
        err_msg = "The result should ID should be the same"
        assert result_id == result.id, err_msg
