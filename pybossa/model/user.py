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

from sqlalchemy import Integer, Boolean, Unicode, Text, String, BigInteger
from sqlalchemy.schema import Column
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from flask_login import UserMixin
from flask import current_app

from pybossa.core import db, signer
from pybossa.model import DomainObject, make_timestamp, make_uuid
from pybossa.model.project import Project
from pybossa.model.task_run import TaskRun
from pybossa.model.blogpost import Blogpost


class User(db.Model, DomainObject, UserMixin):
    '''A registered user of the PYBOSSA system'''

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    #: UTC timestamp of the user when it's created.
    created = Column(Text, default=make_timestamp)
    email_addr = Column(Unicode(length=254), unique=True, nullable=False)
    #: Name of the user (this is used as the nickname).
    name = Column(Unicode(length=254), unique=True, nullable=False)
    #: Fullname of the user.
    fullname = Column(Unicode(length=500), nullable=False)
    #: Language used by the user in the PYBOSSA server.
    locale = Column(Unicode(length=254), default=u'en', nullable=False)
    api_key = Column(String(length=36), default=make_uuid, unique=True)
    passwd_hash = Column(Unicode(length=254), unique=True)
    ldap = Column(Unicode, unique=True)
    admin = Column(Boolean, default=False)
    pro = Column(Boolean, default=False)
    privacy_mode = Column(Boolean, default=True, nullable=False)
    restrict = Column(Boolean, default=False, nullable=False)
    category = Column(Integer)
    flags = Column(Integer)
    twitter_user_id = Column(BigInteger, unique=True)
    facebook_user_id = Column(BigInteger, unique=True)
    google_user_id = Column(String, unique=True)
    ckan_api = Column(String, unique=True)
    newsletter_prompted = Column(Boolean, default=False)
    valid_email = Column(Boolean, default=False)
    confirmation_email_sent = Column(Boolean, default=False)
    subscribed = Column(Boolean, default=False)
    consent = Column(Boolean, default=False)
    info = Column(MutableDict.as_mutable(JSONB), default=dict())
    subadmin = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
    user_pref = Column(JSONB)
    last_login = Column(Text, default=make_timestamp)

    ## Relationships
    task_runs = relationship(TaskRun, backref='user')
    projects = relationship(Project, backref='owner')
    blogposts = relationship(Blogpost, backref='owner')


    def get_id(self):
        '''id for login system. equates to name'''
        return self.name


    def set_password(self, password):
        self.passwd_hash = signer.generate_password_hash(password)


    def check_password(self, password):
        # OAuth users do not have a password
        if self.passwd_hash:
            return signer.check_password_hash(self.passwd_hash, password)
        return False

    @classmethod
    def public_attributes(self):
        """Return a list of public attributes."""
        return ['created', 'name', 'fullname', 'info',
                'n_answers', 'registered_ago', 'rank', 'score', 'locale']

    @classmethod
    def public_info_keys(self):
        """Return a list of public info keys."""
        default = ['avatar', 'container', 'extra', 'avatar_url']
        extra = current_app.config.get('USER_INFO_PUBLIC_FIELDS')
        if extra:
            return list(set(default).union(set(extra)))
        else:
            return default

    def get_quiz_for_project(self, project):
        # This user's quiz info for all projects
        user_quizzes = self.info.get('quiz', {})
        # This user's quiz info for project_id
        project_key = str(project.id)
        user_project_quiz = user_quizzes.get(project_key)
        if not user_project_quiz:
            user_project_quiz = {
                'status': 'not_started',
                'result': {
                    'right': 0,
                    'wrong': 0
                },
                # We take a snapshot of the project's quiz settings on the first use.
                'config': project.get_quiz()
            }
            user_quizzes[project_key] = user_project_quiz
        user_project_quiz_config = user_project_quiz['config']
        if 'passing' not in user_project_quiz_config:
            user_project_quiz_config['passing'] = user_project_quiz_config['pass']
            del user_project_quiz_config['pass']
        # You have to assign to the property in order for SQLAlchemy to detect the change.
        # Just doing setdefault() will cause the changes to get lost.
        self.info['quiz'] = user_quizzes
        return user_project_quiz

    def add_quiz_right_answer(self, project):
        quiz = self.get_quiz_for_project(project)
        if (quiz['status'] != 'in_progress'):
            raise Exception('Cannot add right answer to quiz that is not in progress.')
        result = quiz['result']
        result['right'] += 1
        self.update_quiz_status(project)

    def add_quiz_wrong_answer(self, project):
        quiz = self.get_quiz_for_project(project)
        if (quiz['status'] != 'in_progress'):
            raise Exception('Cannot add wrong answer to quiz that is not in progress.')
        result = quiz['result']
        result['wrong'] += 1
        self.update_quiz_status(project)

    def get_quiz_in_progress(self, project):
        return self.get_quiz_for_project(project)['status'] == 'in_progress'

    def get_quiz_failed(self, project):
        return self.get_quiz_for_project(project)['status'] == 'failed'

    def get_quiz_passed(self, project):
        return self.get_quiz_for_project(project)['status'] == 'passed'

    def get_quiz_not_started(self, project):
        return self.get_quiz_for_project(project)['status'] == 'not_started'

    def get_quiz_enabled(self, project):
        return self.get_quiz_for_project(project)['config']['enabled']

    def set_quiz_status(self, project, status):
        self.get_quiz_for_project(project)['status'] = status

    def set_quiz_for_project(self, project_id, project_quiz):
        quiz = self.info.get('quiz', {})
        self.info['quiz'] = quiz
        quiz[str(project_id)] = project_quiz

    def update_quiz_status(self, project):
        quiz = self.get_quiz_for_project(project)
        right_count = quiz['result']['right']
        correct_to_pass = quiz['config']['passing']
        questions = quiz['config']['questions']
        status = None
        if right_count >= correct_to_pass:
            status = 'passed'
        elif quiz['result']['wrong'] > questions - correct_to_pass:
            status = 'failed'

        if not status:
            return
        
        if quiz['config']['short_circuit'] or right_count + wrong_count >= questions:
            quiz['status'] = status        

    def reset_quiz(self, project):
        # This user's quiz info for all projects
        user_quizzes = self.info.get('quiz', {})
        # Delete this user's quiz info for project_id
        project_key = str(project.id)
        user_quizzes.pop(project_key, None)
        self.info['quiz'] = user_quizzes
        if self.get_quiz_enabled(project):
            self.set_quiz_status(project, 'in_progress')
        from pybossa.sched import release_user_locks_for_project
        release_user_locks_for_project(self.id, project.id)


