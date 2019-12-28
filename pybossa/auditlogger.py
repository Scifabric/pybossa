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
"""AuditLogger module."""
from pybossa.model.auditlog import Auditlog
import json


class AuditLogger(object):

    """Class for logging actions on projects."""

    def __init__(self, auditlog_repo, caller='web'):
        """Setup repository."""
        self.repo = auditlog_repo
        self.caller = caller

    def log_event(self, project, user, action, attribute,
                  old_value, new_value):
        """Log event."""

        if type(old_value) in [dict, list]:
            old_value = json.dumps(old_value)

        if type(new_value) in [dict, list]:
            new_value = json.dumps(new_value)

        log = Auditlog(
            project_id=project.id,
            project_short_name=project.short_name,
            user_id=user.id,
            user_name=user.name,
            action=action,
            caller=self.caller,
            attribute=attribute,
            old_value=old_value,
            new_value=new_value)
        self.repo.save(log)

    def get_project_logs(self, project_id):
        """Get all project logs."""
        return self.repo.filter_by(project_id=project_id)

    def add_log_entry(self, old_project, new_project, user):
        """Add log entry."""
        if old_project is None:
            self.log_event(new_project, user, 'create', 'project',
                           'Nothing', 'New project')
            return
        if new_project is None:
            self.log_event(old_project, user, 'delete',
                           'project', 'Saved', 'Deleted')
            return
        old = old_project.dictize()
        new = new_project.dictize()
        attributes = (set(old.keys()) | set(new.keys())) - set(['updated'])
        changes = {attr: (old.get(attr), new.get(attr))
                   for attr in attributes if old.get(attr) != new.get(attr)}
        for attr in changes:
            old_value = changes[attr][0]
            new_value = changes[attr][1]
            if attr == 'info':
                old_value = old_value if old_value is not None else {}
                self._manage_info_keys(new_project, user, old_value, new_value)
            else:
                if old_value is None:
                    old_value = ''
                if new_value is None:
                    new_value = ''
                if (str(old_value) != str(new_value)):
                    self.log_event(new_project, user, 'update', attr,
                                   str(old_value), str(new_value))

    def _manage_info_keys(self, project, user,
                          old_value, new_value, action='update'):
        """Manage info keys."""
        s_o = set(old_value.keys())
        s_n = set(new_value.keys())
        # For new keys
        for new_key in (s_n - s_o):
            # only log changed keys
            if new_value.get(new_key) is None:
                continue
            self.log_event(project, user, action, new_key,
                           old_value.get(new_key),
                           new_value.get(new_key))
        # For updated keys
        for same_key in (s_n & s_o):
            # only log changed keys
            if old_value.get(same_key) == new_value.get(same_key):
                continue
            self.log_event(project, user, action, same_key,
                           old_value.get(same_key), new_value.get(same_key))
