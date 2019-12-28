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

from pybossa.core import db

import factory

from pybossa.repositories import UserRepository
from pybossa.repositories import ProjectRepository
from pybossa.repositories import AnnouncementRepository
from pybossa.repositories import BlogRepository
from pybossa.repositories import TaskRepository
from pybossa.repositories import AuditlogRepository
from pybossa.repositories import WebhookRepository
from pybossa.repositories import HelpingMaterialRepository
from pybossa.repositories import PageRepository

user_repo = UserRepository(db)
project_repo = ProjectRepository(db)
announcement_repo = AnnouncementRepository(db)
blog_repo = BlogRepository(db)
task_repo = TaskRepository(db)
auditlog_repo = AuditlogRepository(db)
webhook_repo = WebhookRepository(db)
helping_repo = HelpingMaterialRepository(db)
page_repo = PageRepository(db)


def reset_all_pk_sequences():
    ProjectFactory.reset_sequence()
    AnnouncementFactory.reset_sequence()
    BlogpostFactory.reset_sequence()
    CategoryFactory.reset_sequence()
    TaskFactory.reset_sequence()
    TaskRunFactory.reset_sequence()
    UserFactory.reset_sequence()
    AuditlogFactory.reset_sequence()
    WebhookFactory.reset_sequence()
    HelpingMaterialFactory.reset_sequence()
    PageFactory.reset_sequence()


class BaseFactory(factory.Factory):
    @classmethod
    def _setup_next_sequence(cls):
        return 1

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        project = model_class(*args, **kwargs)
        db.session.remove()
        return project


# Import the factories
from .project_factory import ProjectFactory
from .announcement_factory import AnnouncementFactory
from .blogpost_factory import BlogpostFactory
from .category_factory import CategoryFactory
from .task_factory import TaskFactory
from .taskrun_factory import TaskRunFactory, AnonymousTaskRunFactory, ExternalUidTaskRunFactory
from .user_factory import UserFactory
from .auditlog_factory import AuditlogFactory
from .webhook_factory import WebhookFactory
from .helping_material import HelpingMaterialFactory
from .page import PageFactory
