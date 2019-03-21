# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2021 Scifabric LTD.
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
import requests
from default import Test, with_context
from factories import performance_repo
from factories import (ProjectFactory, TaskFactory, TaskRunFactory,
    UserFactory, PerformanceStatsFactory)


from pybossa.api.task_run import update_gold_stats


class TestUpdateGoldStats(Test):

    @with_context
    def test_create_new_row(self):
        answer_fields = {
            'hello': {
                'type': 'categorical',
                'config': {
                    'labels': ['A', 'B']
                }
            }
        }
        project = ProjectFactory.create(info={'answer_fields': answer_fields})
        task = TaskFactory.create(project=project, calibration=1, gold_answers={'hello': 'A'})
        task_run = TaskRunFactory.create(task=task, info={'hello': 'A'})

        update_gold_stats(task_run.user_id, task.id, task_run.dictize())
        stats = performance_repo.filter_by(project_id=project.id)
        assert len(stats) == 1
        assert stats[0].info['matrix'] == [[1, 0], [0, 0]]

    @with_context
    def test_update_row(self):
        answer_fields = {
            'hello': {
                'type': 'categorical',
                'config': {
                    'labels': ['A', 'B']
                }
            }
        }
        project = ProjectFactory.create(info={'answer_fields': answer_fields})
        task = TaskFactory.create(project=project, calibration=1, gold_answers={'hello': 'A'})
        task_run = TaskRunFactory.create(task=task, info={'hello': 'B'})
        stat = PerformanceStatsFactory.create(user_id=task_run.user_id,
            project_id=project.id, field='hello',
            info={'matrix': [[1, 4], [2, 3]]})

        update_gold_stats(task_run.user_id, task.id, task_run.dictize())
        stats = performance_repo.filter_by(project_id=project.id)
        assert len(stats) == 1
        assert stats[0].info['matrix'] == [[1, 5], [2, 3]]
