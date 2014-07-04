# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
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

from flask.ext.login import UserMixin

from pybossa.core import signer



class User(object, UserMixin):
    '''A registered user of the PyBossa system'''

    def __init__(self, id, name, fullname, email_addr, privacy_mode=True):
        self.id = id
        self.name = name
        self.fullname = fullname
        self.email_addr = email_addr
        self.privacy_mode = privacy_mode
        self.admin = False


    # ## Relationships
    # task_runs = relationship(TaskRun, backref='user')
    # apps = relationship(App, backref='owner')
    # blogposts = relationship(Blogpost, backref='owner')


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

