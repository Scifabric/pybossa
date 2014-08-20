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

from pybossa.forms.forms import RegisterForm
from default import Test, db, with_context
from pybossa.model.user import User
from pybossa.forms import validator
from pybossa.view.account import LoginForm
from factories import UserFactory
from wtforms import ValidationError
from nose.tools import raises
from mock import patch


class TestValidator(Test):
    def setUp(self):
        super(TestValidator, self).setUp()
        with self.flask_app.app_context():
            self.create()

    @raises(ValidationError)
    def test_unique(self):
        """Test VALIDATOR Unique works."""
        with self.flask_app.test_request_context('/'):
            f = LoginForm()
            f.email.data = self.email_addr
            u = validator.Unique(db.session, User,
                                         User.email_addr)
            u.__call__(f, f.email)

    @raises(ValidationError)
    def test_not_allowed_chars(self):
        """Test VALIDATOR NotAllowedChars works."""
        with self.flask_app.test_request_context('/'):
            f = LoginForm()
            f.email.data = self.email_addr + "$"
            u = validator.NotAllowedChars()
            u.__call__(f, f.email)

    @raises(ValidationError)
    def test_comma_separated_integers(self):
        """Test VALIDATOR CommaSeparatedIntegers works."""
        with self.flask_app.test_request_context('/'):
            f = LoginForm()
            f.email.data = '1 2 3'
            u = validator.CommaSeparatedIntegers()
            u.__call__(f, f.email)



class TestRegisterForm(Test):

    def setUp(self):
        super(TestRegisterForm, self).setUp()
        self.fill_in_data = {'fullname': 'Tyrion Lannister', 'name': 'mylion',
                             'email_addr': 'tyrion@casterly.rock',
                             'password':'secret', 'confirm':'secret'}

    fields = ['fullname', 'name', 'email_addr', 'password', 'confirm']

    @with_context
    def test_register_form_contains_fields(self):
        form = RegisterForm()

        for field in self.fields:
            assert form.__contains__(field), 'Field %s is not in form' %field

    @with_context
    def test_register_form_validates_with_valid_fields(self):
        form = RegisterForm(**self.fill_in_data)

        assert form.validate()

    @with_context
    def test_register_form_unique_name(self):
        form = RegisterForm(**self.fill_in_data)
        user = UserFactory.create(name='mylion')

        assert not form.validate()
        assert "The user name is already taken" in form.errors['name'], form.errors

    @with_context
    def test_register_name_length(self):
        self.fill_in_data['name'] = 'a'
        form = RegisterForm(**self.fill_in_data)

        assert not form.validate()
        assert "User name must be between 3 and 35 characters long" in form.errors['name'], form.errors

    @with_context
    def test_register_name_allowed_chars(self):
        self.fill_in_data['name'] = '$#&amp;\/|'
        form = RegisterForm(**self.fill_in_data)

        assert not form.validate()
        assert "$#&\\/| and space symbols are forbidden" in form.errors['name'], form.errors

    @with_context
    def test_register_form_unique_email(self):
        form = RegisterForm(**self.fill_in_data)
        user = UserFactory.create(email_addr='tyrion@casterly.rock')

        assert not form.validate()
        assert "Email is already taken" in form.errors['email_addr'], form.errors

    @with_context
    def test_register_email_length(self):
        self.fill_in_data['email_addr'] = ''
        form = RegisterForm(**self.fill_in_data)

        assert not form.validate()
        assert "Email must be between 3 and 35 characters long" in form.errors['email_addr'], form.errors

    @with_context
    def test_register_email_valid_format(self):
        self.fill_in_data['email_addr'] = 'notanemail'
        form = RegisterForm(**self.fill_in_data)

        assert not form.validate()
        assert "Invalid email address." in form.errors['email_addr'], form.errors

    @with_context
    def test_register_fullname_length(self):
        self.fill_in_data['fullname'] = 'a'
        form = RegisterForm(**self.fill_in_data)

        assert not form.validate()
        assert "Full name must be between 3 and 35 characters long" in form.errors['fullname'], form.errors

    @with_context
    def test_register_password_required(self):
        self.fill_in_data['password'] = ''
        form = RegisterForm(**self.fill_in_data)

        assert not form.validate()
        assert "Password cannot be empty" in form.errors['password'], form.errors

    @with_context
    def test_register_password_missmatch(self):
        self.fill_in_data['confirm'] = 'badpasswd'
        form = RegisterForm(**self.fill_in_data)

        assert not form.validate()
        assert "Passwords must match" in form.errors['password'], form.errors
