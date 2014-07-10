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

from pybossa.model.task_run import TaskRun
from . import BaseFactory, factory, task_repo


class TaskRunFactory(factory.Factory):
    class Meta:
        model = TaskRun

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        taskrun = model_class(*args, **kwargs)
        task_repo.save(taskrun)
        return taskrun

    @classmethod
    def _setup_next_sequence(cls):
        return 1

    id = factory.Sequence(lambda n: n)
    task = factory.SubFactory('factories.TaskFactory')
    task_id = factory.LazyAttribute(lambda task_run: task_run.task.id)
    app = factory.SelfAttribute('task.app')
    app_id = factory.LazyAttribute(lambda task_run: task_run.app.id)
    user = factory.SubFactory('factories.UserFactory')
    user_id = factory.LazyAttribute(lambda task_run: task_run.user.id)


class AnonymousTaskRunFactory(TaskRunFactory):
    user = None
    user_id = None
    user_ip = '127.0.0.1'
