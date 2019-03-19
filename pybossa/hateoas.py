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
"""Hateoas module for PYBOSSA."""
from flask import url_for


class Hateoas(object):

    """Hateoas class."""

    def link(self, rel, title, href):
        """Return hateoas link."""
        return "<link rel='%s' title='%s' href='%s'/>" % (rel, title, href)

    def create_link(self, item_id, title, rel='self'):
        """Create hateoas link."""
        # title = item.__class__.__name__.lower()
        method = ".api_%s" % title
        href = url_for(method, oid=item_id, _external=True)
        return self.link(rel, title, href)

    def create_links(self, item):
        """Create Hateoas links."""
        cls = item.__class__.__name__.lower()
        links = []
        if cls == 'result':
            link = self. create_link(item.id, title='result')
            if item.project_id is not None:
                links.append(self.create_link(item.project_id, title='project',
                                              rel='parent'))
            if item.task_id is not None:
                links.append(self.create_link(item.task_id, title='task',
                                              rel='parent'))
            return links, link
        elif cls == 'taskrun':
            link = self.create_link(item.id, title='taskrun')
            if item.project_id is not None:
                links.append(self.create_link(item.project_id,
                                              title='project', rel='parent'))
            if item.task_id is not None:
                links.append(self.create_link(item.task_id,
                                              title='task', rel='parent'))
            return links, link
        elif cls == 'task':
            link = self.create_link(item.id, title='task')
            if item.project_id is not None:
                links = [self.create_link(item.project_id,
                                          title='project', rel='parent')]
            return links, link
        elif cls == 'category':
            return None, self.create_link(item.id, title='category')
        elif cls == 'project':
            link = self.create_link(item.id, title='project')
            if item.category_id is not None:
                links.append(self.create_link(item.category_id,
                                              title='category', rel='category'))
            return links, link
        elif cls == 'user':
            link = self.create_link(item.id, title='user')
            # TODO: add the projects created by the user as the
            # links with rel=? (maybe 'project'??)
            return None, link
        elif cls == 'blogpost':
            link = self.create_link(item.id, title='blogpost')
            if item.project_id is not None:
                links = [self.create_link(item.project_id,
                                          title='project', rel='parent')]
            return links, link
        elif cls == 'announcement':
            return None, self.create_link(item.id, title='announcement')
        elif cls == 'helpingmaterial':
            link = self.create_link(item.id, title='helpingmaterial')
            if item.project_id is not None:
                links = [self.create_link(item.project_id,
                                          title='project', rel='parent')]
            return links, link
        elif cls == 'projectstats':
            link = self.create_link(item.id, title='projectstats')
            if item.project_id is not None:
                links = [self.create_link(item.project_id,
                                          title='project', rel='parent')]
            return links, link
        else:  # pragma: no cover
            return False, False

    def remove_links(self, item):
        """Remove HATEOAS link and links from item."""
        if item.get('link'):
            item.pop('link')
        if item.get('links'):
            item.pop('links')
        return item
