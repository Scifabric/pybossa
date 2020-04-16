# -*- coding: utf8 -*-
from bs4 import BeautifulSoup
import json
from mock import patch

from default import db, with_context
from factories import ProjectFactory, TaskFactory
from helper import web
from pybossa.repositories import ProjectRepository, UserRepository

project_repo = ProjectRepository(db)
user_repo = UserRepository(db)


class TestTaskNotificationConfig(web.Helper):

    @with_context
    def test_get_configuration(self):
        ''' get correct configuration from project.info'''
        project = ProjectFactory.create(published=True, info={'progress_reminder': {'target_remaining': 5}})
        url = '/project/%s/tasks/task_notification?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app.get(url)
        assert res.status_code == 200, res.data
        dom = BeautifulSoup(res.data)
        assert dom.find(id='remaining')['value'] == '5', dom

    @with_context
    def test_post_reminder(self):
        ''' post correct configuration'''
        project = ProjectFactory.create(published=True)
        task = TaskFactory.create(id=1, project=project)
        url = '/project/%s/tasks/task_notification?api_key=%s' % (project.short_name, project.owner.api_key)
        data = {'remaining': 0}
        res = self.app.post(url, data=data)
        assert project.info['progress_reminder']['target_remaining'] == 0
        assert not project.info['progress_reminder']['sent'], project.info

    @with_context
    def test_post_reminder_with_webhook(self):
        ''' post correct configuration'''
        project = ProjectFactory.create(published=True)
        task = TaskFactory.create(id=1, project=project)
        url = '/project/%s/tasks/task_notification?api_key=%s' % (project.short_name, project.owner.api_key)
        data = {'remaining': 0, 'webhook':'http://google.com#test'}
        res = self.app.post(url, data=data)
        assert project.info['progress_reminder']['target_remaining'] == 0
        assert project.info['progress_reminder']['webhook'] == 'http://google.com#test'
        assert not project.info['progress_reminder']['sent'], project.info

    @with_context
    def test_post_invalid_reminder(self):
        ''' should not post to project.info if check fails'''
        project = ProjectFactory.create(published=True)
        task = TaskFactory.create(id=1, project=project)
        url = '/project/%s/tasks/task_notification?api_key=%s' % (project.short_name, project.owner.api_key)
        data = {'remaining': 10}
        res = self.app.post(url, data=data)
        assert not project.info.get('progress_reminder'), project.info

    @with_context
    def test_post_invalid_reminder_webhook(self):
        ''' should not post to project.info if check fails'''
        project = ProjectFactory.create(published=True)
        task = TaskFactory.create(id=1, project=project)
        url = '/project/%s/tasks/task_notification?api_key=%s' % (project.short_name, project.owner.api_key)
        data = {'remaining': 0, 'webhook':'not_a_url'}
        res = self.app.post(url, data=data)
        assert not project.info.get('progress_reminder'), project.info

    @with_context
    def test_disable_reminder(self):
        ''' if post empty value, should disable reminder'''
        project = ProjectFactory.create(published=True)
        task = TaskFactory.create(id=1, project=project)
        url = '/project/%s/tasks/task_notification?api_key=%s' % (project.short_name, project.owner.api_key)
        data = {'remaining': None}
        res = self.app.post(url, data=data)
        assert project.info['progress_reminder']['target_remaining'] is None, project.info
