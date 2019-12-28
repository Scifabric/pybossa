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

from yacryptopan import CryptoPAn
from pybossa.model.task_run import TaskRun
from . import BaseFactory, factory, task_repo
import settings_test

cp = CryptoPAn(str.encode(settings_test.CRYPTOPAN_KEY))

class TaskRunFactory(BaseFactory):
    class Meta:
        model = TaskRun

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        taskrun = model_class(*args, **kwargs)
        task_repo.save(taskrun)
        return taskrun

    id = factory.Sequence(lambda n: n)
    task = factory.SubFactory('factories.TaskFactory')
    task_id = factory.LazyAttribute(lambda task_run: task_run.task.id)
    project = factory.SelfAttribute('task.project')
    project_id = factory.LazyAttribute(lambda task_run: task_run.project.id)
    user = factory.SubFactory('factories.UserFactory')
    user_id = factory.LazyAttribute(lambda task_run: task_run.user.id)
    info = dict(answer='yes')


class AnonymousTaskRunFactory(TaskRunFactory):
    user = None
    user_id = None
    user_ip = cp.anonymize('127.0.0.1')
    info = 'yes'


class ExternalUidTaskRunFactory(TaskRunFactory):
    user = None
    user_id = None
    user_ip = cp.anonymize('127.0.0.1')
    external_uid = '1xa'
    info = 'yes'
