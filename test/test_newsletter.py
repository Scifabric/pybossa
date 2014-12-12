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

import json
import StringIO

from default import db, Fixtures, with_context
from helper import web
from mock import patch, Mock
from flask import Response, redirect
from itsdangerous import BadSignature
from collections import namedtuple
from pybossa.core import signer
from pybossa.util import unicode_csv_reader
from pybossa.util import get_user_signup_method
from pybossa.ckan import Ckan
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError
from werkzeug.exceptions import NotFound
from pybossa.model.app import App
from pybossa.model.category import Category
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.model.user import User
from pybossa.jobs import send_mail, import_tasks
from factories import AppFactory, CategoryFactory, TaskFactory, TaskRunFactory


FakeRequest = namedtuple('FakeRequest', ['text', 'status_code', 'headers'])


class TestNewsletter(web.Helper):
    #pkg_json_not_found = {
    #    "help": "Return ...",
    #    "success": False,
    #    "error": {
    #        "message": "Not found",
    #        "__type": "Not Found Error"}}

    @with_context
    @patch('pybossa.view.account.newsletter', autospec=True)
    def test_new_user_gets_newsletter(self, newsletter):
        """Test NEWSLETTER new user works."""
        newsletter.app = True
        res = self.register()
        dom = BeautifulSoup(res.data)
        err_msg = "There should be a newsletter page."
        assert dom.find(id='newsletter') is not None, err_msg
        assert dom.find(id='signmeup') is not None, err_msg
        assert dom.find(id='notinterested') is not None, err_msg
