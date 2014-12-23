# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
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

import json
from flask import request
from sqlalchemy.orm.attributes import get_history
from sqlalchemy.exc import IntegrityError

from pybossa.model.auditlog import Auditlog

class AuditLogger(object):

    def __init__(self, auditlog_repo):
        self.repo = auditlog_repo

    def log_event(self, app, user, action, attribute, old_value, new_value):
        log = Auditlog(
            app_id=app.id,
            app_short_name=app.short_name,
            user_id=user.id,
            user_name=user.name,
            action=action,
            caller='web',
            attribute=attribute,
            old_value=old_value,
            new_value=new_value)
        self.repo.save(log)

    def get_project_logs(self, project_id):
        return self.repo.filter_by(app_id=project_id)


    def add_log_entry(self, project, user, action, caller):
        if action == 'create':
            log = Auditlog(
                app_id=project.id,
                app_short_name=project.short_name,
                user_id=user.id,
                user_name=user.name,
                action=action,
                caller=caller,
                attribute='project',
                old_value='Nothing',
                new_value='New project')
            self.repo.save(log)
        elif action == 'delete':
            log = Auditlog(
                app_id=project.id,
                app_short_name=project.short_name,
                user_id=user.id,
                user_name=user.name,
                action=action,
                caller=caller,
                attribute='project',
                old_value='Saved',
                new_value='Deleted')
            self.repo.save(log)
        else:
            user_id, user_name = self._get_user_for_log(user)
            history = {}
            for attr in project.dictize().keys():
                history[attr] = get_history(project, attr)
            for attr in history:
                if history[attr].has_changes():
                    if (len(history[attr].deleted) == 0 and
                        len(history[attr].added) > 0 and
                        attr == 'info'):
                        old_value = {}
                        new_value = history[attr].added[0]
                        self._manage_info_keys(project, user_id, user_name,
                                               old_value, new_value, action,
                                               caller)
                    if (len(history[attr].deleted) > 0 and
                        len(history[attr].added) > 0):
                        old_value = history[attr].deleted[0]
                        new_value = history[attr].added[0]
                        if attr == 'info':
                            self._manage_info_keys(project, user_id, user_name,
                                                   old_value, new_value, action,
                                                   caller)
                        else:
                            if old_value is None or '':
                                old_value = ''
                            if new_value is None or '':
                                new_value = ''
                            if (unicode(old_value) != unicode(new_value)):
                                log = Auditlog(
                                    app_id=project.id,
                                    app_short_name=project.short_name,
                                    user_id=user_id,
                                    user_name=user_name,
                                    action=action,
                                    caller=caller,
                                    attribute=attr,
                                    old_value=old_value,
                                    new_value=new_value)
                                self.repo.save(log)

    def _get_user_for_log(self, user):
        if user.is_authenticated():
            user_id = user.id
            user_name = user.name
        else:
            user_id = request.remote_addr
            user_name = 'anonymous'
        return user_id, user_name

    def _manage_info_keys(self, project, user_id, user_name,
                          old_value, new_value, action, caller):
        s_o = set(old_value.keys())
        s_n = set(new_value.keys())

        # For new keys
        for new_key in (s_n - s_o):
            # handle special case passwd_hash
            if (old_value.get(new_key) is None and
                new_value.get(new_key) is None and
                new_key == 'passwd_hash'):
                pass
            else:
                log = Auditlog(
                    app_id=project.id,
                    app_short_name=project.short_name,
                    user_id=user_id,
                    user_name=user_name,
                    action=action,
                    caller=caller,
                    attribute=new_key,
                    old_value=old_value.get(new_key),
                    new_value=new_value.get(new_key))
                self.repo.save(log)
        # For updated keys
        for same_key in (s_n & s_o):
            log = Auditlog(
                app_id=project.id,
                app_short_name=project.short_name,
                user_id=user_id,
                user_name=user_name,
                action=action,
                caller=caller,
                attribute=same_key,
                old_value=old_value.get(same_key),
                new_value=new_value.get(same_key))
            self.repo.save(log)
