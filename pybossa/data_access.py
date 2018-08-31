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
"""Module with data access helper functions."""
from functools import wraps

import app_settings


def access_controller(return_value=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if data_access_levels:
                return func(*args, **kwargs)
            return return_value
        return wrapper
    return decorator


def get_valid_project_levels_for_task(task):
    task_levels = (task.info or {}).get('data_access', [])
    return set([
        level for l in task_levels
        for level in data_access_levels['valid_project_levels_for_task_level'].get(l, [])
    ])


def get_valid_task_levels_for_project(project):
    assigned_project_levels = (project.info or {}).get('data_access', [])
    return set([
        level for apl in assigned_project_levels
        for level in data_access_levels['valid_task_levels_for_project_level'].get(apl, [])
    ])


def valid_access_levels(levels):
    """check if levels are valid levels"""

    access_levels = data_access_levels['valid_access_levels']
    access_levels = [level[0] for level in access_levels]
    return all(l in access_levels for l in levels)


@access_controller(return_value=True)
def can_assign_user(levels, user_levels):
    """check if user be assigned to an object(project/task) based on
    whether user_levels matches objects levels """
    if not (valid_access_levels(levels) and valid_access_levels(user_levels)):
        return False

    access_levels = data_access_levels['valid_access_levels']
    access_levels = [level[0] for level in access_levels]

    valid_user_levels_for_project_task_level = data_access_levels['valid_user_levels_for_project_task_level']
    valid_task_levels_for_user_level = data_access_levels['valid_task_levels_for_user_level']

    all_user_levels = get_all_access_levels(user_levels, valid_task_levels_for_user_level)
    all_levels = get_all_access_levels(levels, valid_user_levels_for_project_task_level)
    return bool(all_levels.intersection(all_user_levels))


def get_all_access_levels(levels, implicit_levels):
    """based on access level for an object(project/task/user), obtain
    all access levels considering default_levels for an objects"""

    all_levels = set(levels)
    for level in levels:
        for dlevel in implicit_levels[level]:
            all_levels.add(dlevel)
    return all_levels


def get_data_access_db_clause(access_levels):

    if not valid_access_levels(access_levels):
        return

    valid_user_levels_for_project_task_level = data_access_levels['valid_user_levels_for_project_task_level']

    levels = set([level for level in access_levels])
    for level in access_levels:
        ilevels = valid_user_levels_for_project_task_level.get(level, [])
        levels.update(ilevels)
    sql_clauses = [' info->\'data_access\' @> \'["{}"]\''.format(level) for level in levels]
    return ' OR '.join(sql_clauses)


@access_controller(return_value='')
def get_data_access_db_clause_for_task_assignment(user_id):
    from pybossa.cache.users import get_user_access_levels_by_id

    user_levels = get_user_access_levels_by_id(user_id)
    if not valid_access_levels(user_levels):
        raise Exception('Invalid user access level')

    valid_task_levels_for_user_level = data_access_levels['valid_task_levels_for_user_level']
    levels = set([level for level in user_levels])
    for level in user_levels:
        ilevels = valid_task_levels_for_user_level.get(level, [])
        levels.update(ilevels)

    levels = ['\'\"{}\"\''.format(level) for level in levels]
    sql_clause = ' AND task.info->\'data_access\' @> ANY(ARRAY[{}]::jsonb[]) '.format(', '.join(levels))
    return sql_clause


@access_controller()
def ensure_data_access_assignment_to_form(obj, form):
    access_levels = obj.get('data_access', [])
    if not valid_access_levels(access_levels):
        raise Exception('Invalid access levels')
    form.data_access.data = access_levels


@access_controller()
def ensure_data_access_assignment_from_form(obj, form):
    access_levels = form.data_access.data
    if not valid_access_levels(access_levels):
        raise Exception('Invalid access levels')
    obj['data_access'] = access_levels


@access_controller()
def ensure_task_assignment_to_project(task, project):
    if not project.info.get('ext_config', {}).get('data_access', {}).get('tracking_id'):
        raise Exception('Required Project > Settings > External Configurations are missing.')
    task_levels = get_valid_project_levels_for_task(task)
    if not task_levels:
        raise Exception('Task is missing data access level.')
    project_levels = get_valid_task_levels_for_project(project)
    if not project_levels:
        raise Exception('Project data access levels are not configured.')
    if not bool(task_levels & project_levels):
        raise Exception('Invalid or insufficient permission.')


@access_controller()
def ensure_valid_access_levels(access_levels):
    if not valid_access_levels(access_levels):
        raise ValueError(u'Invalid access levels {}'.format(', '.join(access_levels)))


@access_controller()
def copy_data_access_levels(target, access_levels):
    ensure_valid_access_levels(access_levels)
    target['data_access'] = access_levels


def ensure_user_assignment_to_project(project):
    from pybossa.cache.users import get_users_access_levels

    access_levels = project.info.get('data_access')
    ensure_valid_access_levels(access_levels)
    if not project.info.get('project_users'):
        return

    # ensure users assigned to project has project access levels
    project_levels = project.info['data_access']
    users = project.info['project_users']
    users = get_users_access_levels(users)
    invalid_user_ids = set()
    for user in users:
        user_levels = user.get('data_access', [])
        if not can_assign_user(project_levels, user_levels):
            invalid_user_ids.add(user['id'])
    if invalid_user_ids:
        raise ValueError(u'Data access level mismatch. Cannot assign user {} to project'
            .format(', '.join(map(str, invalid_user_ids))))


data_access_levels = {}
if app_settings.config.get('ENABLE_ACCESS_CONTROL'):
    data_access_levels = dict(
        valid_access_levels=app_settings.config['VALID_ACCESS_LEVELS'],
        valid_user_levels_for_project_task_level=app_settings.config['VALID_USER_LEVELS_FOR_PROJECT_TASK_LEVEL'],
        valid_task_levels_for_user_level=app_settings.config['VALID_TASK_LEVELS_FOR_USER_LEVEL'],
        valid_project_levels_for_task_level=app_settings.config['VALID_PROJECT_LEVELS_FOR_TASK_LEVEL'],
        valid_task_levels_for_project_level=app_settings.config['VALID_TASK_LEVELS_FOR_PROJECT_LEVEL']
    )
