# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2018 Scifabric LTD.
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
import random

from mock import patch

from helper import sched
from default import Test, db, with_context
from pybossa.model.task import Task
from pybossa.model.project import Project
from pybossa.model.user import User
from pybossa.model.task_run import TaskRun
from pybossa.model.category import Category
from pybossa.core import task_repo, project_repo, user_repo
from factories import TaskFactory, ProjectFactory, TaskRunFactory, UserFactory
import pybossa
from pybossa.sched import Schedulers
from default import with_context
import json
from mock import patch

class TestLockedSched(sched.Helper):

    @with_context
    def test_user_logout_unlocks_locked_tasks(self):
        """ Test user logout unlocks/expires all locks locked by user """
        owner = UserFactory.create(id=500)
        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = Schedulers.locked

        task1 = TaskFactory.create(project=project, info='project 1')

        project2 = ProjectFactory.create(owner=owner)
        project2.info['sched'] = Schedulers.locked

        task2 = TaskFactory.create(project=project2, info='project 2')

        self.register(name='johndoe')
        self.signin(email='johndoe@example.com')

        res = self.app.get('api/project/1/newtask')
        data = json.loads(res.data)
        assert data.get('info'), data

        res = self.app.get('api/project/2/newtask')
        data = json.loads(res.data)
        assert data.get('info'), data
        self.signout()

        #login with different user and ensure unlocked tasks are presented to user
        self.register(name='jsnow')
        self.signin(email='jsnow@example.com')
        res = self.app.get('api/project/1/newtask')
        data = json.loads(res.data)
        assert data.get('info'), data

        res = self.app.get('api/project/2/newtask')
        data = json.loads(res.data)
        assert data.get('info'), data
        self.signout()
