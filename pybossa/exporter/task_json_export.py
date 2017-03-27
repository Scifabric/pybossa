# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2017 SciFabric LTD.
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
# Cache global variables for timeouts

import json
import tempfile
from pybossa.exporter import Exporter
from pybossa.exporter.json_export import JsonExporter
from pybossa.core import uploader, task_repo
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


class TaskJsonExporter(JsonExporter):
    """JSON Exporter for exporting ``Task``s and ``TaskRun``s
    for a project.
    """

    @staticmethod
    def merge_objects(t):
        """Merge joined objects into a single dictionary."""
        obj_dict = {}

        try:
            obj_dict = t.dictize()
        except:
            pass

        try:
            task = t.task.dictize()
            obj_dict['task'] = task
        except:
            pass

        try:
            user = t.user.dictize()
            allowed_attributes = ['name', 'fullname', 'created',
                                  'email_addr', 'admin', 'subadmin']
            user = {k: v for (k, v) in user.iteritems() if k in allowed_attributes}
            obj_dict['user'] = user
        except:
            pass

        return obj_dict

    def gen_json(self, table, id):
        if table == 'task':
            filter_table =  task_repo.filter_tasks_by
        # If table is task_run, user filter with additional data
        elif table == 'task_run':
            filter_table =  task_repo.filter_task_runs_with_task_and_user
        else:
            return

        n = getattr(task_repo, 'count_%ss_with' % table)(project_id=id)
        sep = ", "
        yield "["
        for i, tr in enumerate(filter_table(project_id=id, yielded=True), 1):
            item = self.merge_objects(tr)
            item = json.dumps(item)
            if (i == n):
                sep = ""
            yield item + sep
        yield "]"
