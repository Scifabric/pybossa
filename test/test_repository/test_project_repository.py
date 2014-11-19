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
# Cache global variables for timeouts

from default import Test, db
from nose.tools import assert_raises
from factories import AppFactory, CategoryFactory
from pybossa.repositories import ProjectRepository
from pybossa.exc import WrongObjectError, DBIntegrityError


class TestProjectRepositoryForProjects(Test):

    def setUp(self):
        super(TestProjectRepositoryForProjects, self).setUp()
        self.project_repo = ProjectRepository(db)


    def test_get_return_none_if_no_project(self):
        """Test get method returns None if there is no project with the
        specified id"""

        project = self.project_repo.get(2)

        assert project is None, project


    def test_get_returns_project(self):
        """Test get method returns a project if exists"""

        project = AppFactory.create()

        retrieved_project = self.project_repo.get(project.id)

        assert project == retrieved_project, retrieved_project


    def test_get_by_shortname_return_none_if_no_project(self):
        """Test get_by_shortname returns None when a project with the specified
        short_name does not exist"""

        project = self.project_repo.get_by_shortname('thisprojectdoesnotexist')

        assert project is None, project


    def test_get_by_shortname_returns_the_project(self):
        """Test get_by_shortname returns a project if exists"""

        project = AppFactory.create()

        retrieved_project = self.project_repo.get_by_shortname(project.short_name)

        assert project == retrieved_project, retrieved_project


    def test_get_by(self):
        """Test get_by returns a project with the specified attribute"""

        project = AppFactory.create(name='My Project', short_name='myproject')

        retrieved_project = self.project_repo.get_by(name=project.name)

        assert project == retrieved_project, retrieved_project


    def test_get_by_returns_none_if_no_project(self):
        """Test get_by returns None if no project matches the query"""

        AppFactory.create(name='My Project', short_name='myproject')

        project = self.project_repo.get_by(name='no_name')

        assert project is None, project


    def get_all_returns_list_of_all_projects(self):
        """Test get_all returns a list of all the existing projects"""

        projects = AppFactory.create_batch(3)

        retrieved_projects = self.project_repo.get_all()

        assert isinstance(retrieved_projects, list)
        assert len(retrieved_projects) == len(projects), retrieved_projects
        for project in retrieved_projects:
            assert project in projects, project


    def test_filter_by_no_matches(self):
        """Test filter_by returns an empty list if no projects match the query"""

        AppFactory.create(name='My Project', short_name='myproject')

        retrieved_projects = self.project_repo.filter_by(name='no_name')

        assert isinstance(retrieved_projects, list)
        assert len(retrieved_projects) == 0, retrieved_projects


    def test_filter_by_one_condition(self):
        """Test filter_by returns a list of projects that meet the filtering
        condition"""

        AppFactory.create_batch(3, allow_anonymous_contributors=False)
        should_be_missing = AppFactory.create(allow_anonymous_contributors=True)

        retrieved_projects = self.project_repo.filter_by(allow_anonymous_contributors=False)

        assert len(retrieved_projects) == 3, retrieved_projects
        assert should_be_missing not in retrieved_projects, retrieved_projects


    def test_filter_by_multiple_conditions(self):
        """Test filter_by supports multiple-condition queries"""

        AppFactory.create_batch(2, allow_anonymous_contributors=False, hidden=0)
        project = AppFactory.create(allow_anonymous_contributors=False, hidden=1)

        retrieved_projects = self.project_repo.filter_by(
                                            allow_anonymous_contributors=False,
                                            hidden=1)

        assert len(retrieved_projects) == 1, retrieved_projects
        assert project in retrieved_projects, retrieved_projects


    def test_save(self):
        """Test save persist the project"""

        project = AppFactory.build()
        assert self.project_repo.get(project.id) is None

        self.project_repo.save(project)

        assert self.project_repo.get(project.id) == project, "Project not saved"


    def test_save_fails_if_integrity_error(self):
        """Test save raises a DBIntegrityError if the instance to be saved lacks
        a required value"""

        project = AppFactory.build(name=None)

        assert_raises(DBIntegrityError, self.project_repo.save, project)


    def test_save_only_saves_projects(self):
        """Test save raises a WrongObjectError when an object which is not
        a Project (App) instance is saved"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.project_repo.save, bad_object)


    def test_update(self):
        """Test update persists the changes made to the project"""

        project = AppFactory.create(description='this is a project')
        project.description = 'the description has changed'

        self.project_repo.update(project)
        updated_project = self.project_repo.get(project.id)

        assert updated_project.description == 'the description has changed', updated_project


    def test_update_fails_if_integrity_error(self):
        """Test update raises a DBIntegrityError if the instance to be updated
        lacks a required value"""

        project = AppFactory.create()
        project.name = None

        assert_raises(DBIntegrityError, self.project_repo.update, project)


    def test_update_only_updates_projects(self):
        """Test update raises a WrongObjectError when an object which is not
        a Project (App) instance is updated"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.project_repo.update, bad_object)


    def test_delete(self):
        """Test delete removes the project instance"""

        project = AppFactory.create()

        self.project_repo.delete(project)
        deleted = self.project_repo.get(project.id)

        assert deleted is None, deleted


    def test_delete_also_removes_dependant_resources(self):
        """Test delete removes project tasks and taskruns too"""
        from factories import TaskFactory, TaskRunFactory, BlogpostFactory
        from pybossa.repositories import TaskRepository, BlogRepository

        project = AppFactory.create()
        task = TaskFactory.create(app=project)
        taskrun = TaskRunFactory.create(task=task)
        blogpost = BlogpostFactory.create(app=project)

        self.project_repo.delete(project)
        deleted_task = TaskRepository(db).get_task(task.id)
        deleted_taskrun = TaskRepository(db).get_task_run(taskrun.id)
        deleted_blogpost = BlogRepository(db).get(blogpost.id)

        assert deleted_task is None, deleted_task
        assert deleted_taskrun is None, deleted_taskrun


    def test_delete_only_deletes_projects(self):
        """Test delete raises a WrongObjectError if is requested to delete other
        than a project"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.project_repo.delete, bad_object)



class TestProjectRepositoryForCategories(Test):

    def setUp(self):
        super(TestProjectRepositoryForCategories, self).setUp()
        self.project_repo = ProjectRepository(db)


    def test_get_category_return_none_if_no_category(self):
        """Test get_category method returns None if there is no category with
        the specified id"""

        category = self.project_repo.get_category(200)

        assert category is None, category


    def test_get_category_returns_category(self):
        """Test get_category method returns a category if exists"""

        category = CategoryFactory.create()

        retrieved_category = self.project_repo.get_category(category.id)

        assert category == retrieved_category, retrieved_category


    def test_get_category_by(self):
        """Test get_category returns a category with the specified attribute"""

        category = CategoryFactory.create(name='My Cat', short_name='mycat')

        retrieved_category = self.project_repo.get_category_by(name=category.name)

        assert category == retrieved_category, retrieved_category


    def test_get_category_by_returns_none_if_no_category(self):
        """Test get_category returns None if no category matches the query"""

        CategoryFactory.create(name='My Project', short_name='mycategory')

        category = self.project_repo.get_by(name='no_name')

        assert category is None, category


    def get_all_returns_list_of_all_categories(self):
        """Test get_all_categories returns a list of all the existing categories"""

        categories = CategoryFactory.create_batch(3)

        retrieved_categories = self.project_repo.get_all_categories()

        assert isinstance(retrieved_categories, list)
        assert len(retrieved_categories) == len(categories), retrieved_categories
        for category in retrieved_categories:
            assert category in categories, category


    def test_filter_categories_by_no_matches(self):
        """Test filter_categories_by returns an empty list if no categories
        match the query"""

        CategoryFactory.create(name='My Project', short_name='mycategory')

        retrieved_categories = self.project_repo.filter_categories_by(name='no_name')

        assert isinstance(retrieved_categories, list)
        assert len(retrieved_categories) == 0, retrieved_categories


    def test_filter_categories_by_one_condition(self):
        """Test filter_categories_by returns a list of categories that meet
        the filtering condition"""

        CategoryFactory.create_batch(3, description='generic category')
        should_be_missing = CategoryFactory.create(description='other category')

        retrieved_categories = (self.project_repo
            .filter_categories_by(description='generic category'))

        assert len(retrieved_categories) == 3, retrieved_categories
        assert should_be_missing not in retrieved_categories, retrieved_categories


    def test_save_category(self):
        """Test save_category persist the category"""

        category = CategoryFactory.build()
        assert self.project_repo.get(category.id) is None

        self.project_repo.save_category(category)

        assert self.project_repo.get_category(category.id) == category, "Category not saved"


    def test_save_category_fails_if_integrity_error(self):
        """Test save_category raises a DBIntegrityError if the instance to be
       saved lacks a required value"""

        category = CategoryFactory.build(name=None)

        assert_raises(DBIntegrityError, self.project_repo.save_category, category)


    def test_save_category_only_saves_categories(self):
        """Test save_category raises a WrongObjectError when an object which is
        not a Category instance is saved"""

        bad_object = AppFactory.build()

        assert_raises(WrongObjectError, self.project_repo.save_category, bad_object)


    def test_update_category(self):
        """Test update_category persists the changes made to the category"""

        category = CategoryFactory.create(description='this is a category')
        category.description = 'the description has changed'

        self.project_repo.update_category(category)
        updated_category = self.project_repo.get_category(category.id)

        assert updated_category.description == 'the description has changed', updated_category


    def test_update_category_fails_if_integrity_error(self):
        """Test update raises a DBIntegrityError if the instance to be updated
        lacks a required value"""

        category = CategoryFactory.create()
        category.name = None

        assert_raises(DBIntegrityError, self.project_repo.update_category, category)


    def test_update_category_only_updates_categories(self):
        """Test update_category raises a WrongObjectError when an object which is
        not a Category instance is updated"""

        bad_object = AppFactory.build()

        assert_raises(WrongObjectError, self.project_repo.update_category, bad_object)


    def test_delete_category(self):
        """Test delete_category removes the category instance"""

        category = CategoryFactory.create()

        self.project_repo.delete_category(category)
        deleted = self.project_repo.get_category(category.id)

        assert deleted is None, deleted


    def test_delete_category_only_deletes_categories(self):
        """Test delete_category raises a WrongObjectError if is requested to
        delete other than a category"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.project_repo.delete_category, bad_object)
