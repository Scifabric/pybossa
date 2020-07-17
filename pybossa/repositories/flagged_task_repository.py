# -*- coding: utf8 -*-
# This file is part of myKaarma.
#
# 

from sqlalchemy.exc import IntegrityError
from sqlalchemy import cast, Date

from pybossa.repositories import Repository
from pybossa.model.task import Task
from pybossa.model.flagged_task import FlaggedTask
from pybossa.exc import WrongObjectError, DBIntegrityError
from pybossa.cache import projects as cached_projects
from pybossa.core import uploader
from sqlalchemy import text
from pybossa.core import db


class FlaggedTaskRepository(Repository):

    # Methods for saving, deleting and updating both FlaggedTask objects
    def save(self, element):
        self._validate_can_be('saved', element)
        try:
            self.db.session.add(element)
            self.db.session.commit()
            cached_projects.clean_project(element.project_id)
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def _validate_can_be(self, action, element):
        if not isinstance(element, FlaggedTask):
            name = element.__class__.__name__
            msg = '%s cannot be %s by %s' % (name, action, self.__class__.__name__)
            raise WrongObjectError(msg)

    def update(self, element):
        self._validate_can_be('updated', element)
        try:
            self.db.session.merge(element)
            self.db.session.commit()
            cached_projects.clean_project(element.project_id)
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def delete(self, element):
        self._delete(element)
        project = element.project
        self.db.session.commit()
        cached_projects.clean_project(element.project_id)
        self._delete_zip_files_from_store(project)