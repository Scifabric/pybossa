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

from default import Test, with_context
from mock import patch, MagicMock
from pybossa.model.event_listeners import add_blog_event
from pybossa.jobs import notify_blog_users


"""Tests for model event listeners."""



class TestModelEventListeners(Test):

    @with_context
    @patch('pybossa.model.event_listeners.mail_queue')
    def test_add_blog_event(self, mock_queue):
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
