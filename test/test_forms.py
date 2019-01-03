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

from wtforms import ValidationError
from nose.tools import raises, assert_raises
from flask import current_app

from default import Test, db, with_context
from pybossa.forms.forms import (RegisterForm, LoginForm, EMAIL_MAX_LENGTH,
    USER_NAME_MAX_LENGTH, USER_FULLNAME_MAX_LENGTH, BulkTaskLocalCSVImportForm,
    RegisterFormWithUserPrefMetadata, UserPrefMetadataForm)
from pybossa.forms import validator
from pybossa.repositories import UserRepository
from factories import UserFactory
from mock import patch, MagicMock
from werkzeug.datastructures import MultiDict

user_repo = UserRepository(db)

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
            u = validator.Unique(user_repo.get_by, 'email_addr')
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

    @with_context
    @raises(ValidationError)
    def test_reserved_names_account_signin(self):
        """Test VALIDATOR ReservedName for account URLs"""
        form = RegisterForm()
        form.name.data = 'signin'
        val = validator.ReservedName('account', current_app)
        val(form, form.name)

    @with_context
    @raises(ValidationError)
    def test_reserved_names_project_published(self):
        """Test VALIDATOR ReservedName for project URLs"""
        form = RegisterForm()
        form.name.data = 'category'
        val = validator.ReservedName('project', current_app)
        val(form, form.name)

    @with_context
    @raises(ValidationError)
    def test_check_password_strength(self):
        """Test VALIDATOR CheckPasswordStrength for new user password"""
        form = RegisterForm()
        form.password.data = 'Abcd12345'
        u = validator.CheckPasswordStrength()
        u.__call__(form, form.password)

    @with_context
    @raises(ValidationError)
    def test_check_password_strength_custom_message(self):
        """Test VALIDATOR CheckPasswordStrength with custom message """
        form = RegisterForm()
        form.password.data = 'Abcd12345'
        u = validator.CheckPasswordStrength(message='custom message')
        u.__call__(form, form.password)

    @with_context
    def test_check_password_strength_no_policy(self):
        """Test VALIDATOR CheckPasswordStrength with no password policy """
        form = RegisterForm()
        form.password.data = 'Abcd12345'
        u = validator.CheckPasswordStrength(uppercase=None,
                lowercase=None, numeric=None, special=None)
        u.__call__(form, form.password)


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
        error_message = "User name must be between 3 and %s characters long" % USER_NAME_MAX_LENGTH

        assert not form.validate()
        assert error_message in form.errors['name'], form.errors

    @with_context
    def test_register_name_allowed_chars(self):
        self.fill_in_data['name'] = '$#&amp;\/|'
        form = RegisterForm(**self.fill_in_data)

        assert not form.validate()
        assert "$#&\\/| and space symbols are forbidden" in form.errors['name'], form.errors

    @with_context
    def test_register_name_reserved_name(self):
        self.fill_in_data['name'] = 'signin'

        form = RegisterForm(**self.fill_in_data)

        assert not form.validate()
        assert 'This name is used by the system.' in form.errors['name'], form.errors

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
        error_message = "Email must be between 3 and %s characters long" % EMAIL_MAX_LENGTH

        assert not form.validate()
        assert error_message in form.errors['email_addr'], form.errors

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
        error_message = "Full name must be between 3 and %s characters long" % USER_FULLNAME_MAX_LENGTH

        assert not form.validate()
        assert error_message in form.errors['fullname'], form.errors

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

    @with_context
    def test_register_password_valid_password(self):
        self.fill_in_data['password'] = self.fill_in_data['confirm'] = 'Abcd12345!'
        form = RegisterForm(**self.fill_in_data)
        assert form.validate()

class TestBulkTaskLocalCSVForm(Test):

    def setUp(self):
        super(TestBulkTaskLocalCSVForm, self).setUp()
        self.form_data = {'csv_filename': 'sample.csv'}

    @with_context
    @patch('pybossa.forms.forms.request')
    def test_import_request_with_no_file_returns_none(self, mock_request):
        from flask import flash
        mock_request.method = 'POST'
        mock_request.files = dict(somekey='somevalue')
        form = BulkTaskLocalCSVImportForm(**self.form_data)
        return_value = form.get_import_data()
        assert return_value['type'] is 'localCSV' and return_value['csv_filename'] is None

    @with_context
    @patch('pybossa.forms.forms.request')
    def test_import_blank_local_csv_file_returns_none(self, mock_request):
        mock_request.method = 'POST'
        mock_file = MagicMock()
        mock_file.filename = ''
        mock_request.files = dict(file=mock_file)
        form = BulkTaskLocalCSVImportForm(**self.form_data)
        return_value = form.get_import_data()
        assert return_value['type'] is 'localCSV' and return_value['csv_filename'] is None

    @with_context
    @patch('pybossa.forms.forms.request')
    def test_import_invalid_local_csv_file_ext_returns_none(self, mock_request):
        mock_request.method = 'POST'
        mock_file = MagicMock()
        mock_file.filename = 'sample.txt'
        mock_request.files = dict(file=mock_file)
        form = BulkTaskLocalCSVImportForm(**self.form_data)
        return_value = form.get_import_data()
        assert return_value['type'] is 'localCSV' and return_value['csv_filename'] is None

    @with_context
    @patch('pybossa.forms.forms.request')
    @patch('pybossa.forms.forms.current_user')
    def test_import_upload_path_works(self, mock_user, mock_request):
        mock_user.id = 1
        mock_request.method = 'POST'
        mock_file = MagicMock()
        mock_file.filename = 'sample.csv'
        mock_request.files = dict(file=mock_file)
        form = BulkTaskLocalCSVImportForm(**self.form_data)
        return_value = form.get_import_data()
        assert return_value['type'] is 'localCSV', return_value
        assert 'user_1/sample.csv' in return_value['csv_filename'], return_value

    @with_context
    @patch('pybossa.forms.forms.uploader')
    @patch('pybossa.forms.forms.request')
    @patch('pybossa.forms.forms.current_user')
    def test_import_upload_path_ioerror(self, mock_user, mock_request,
                                        mock_uploader):
        mock_user.id = 1
        mock_request.method = 'POST'
        mock_file = MagicMock()
        mock_file.filename = 'sample.csv'
        mock_request.files = dict(file=mock_file)
        form = BulkTaskLocalCSVImportForm(**self.form_data)
        assert_raises(IOError, form.get_import_data)


class TestRegisterFormWithUserPrefMetadata(Test):

    def setUp(self):
        super(TestRegisterFormWithUserPrefMetadata, self).setUp()
        self.fill_in_data = {'fullname': 'Tyrion Lannister', 'name': 'mylion',
                             'email_addr': 'tyrion@casterly.rock',
                             'password':'secret', 'confirm':'secret',
                             'user_type': 'Researcher'}

        self.fields = ['fullname', 'name', 'email_addr', 'password', 'confirm',
                  'languages', 'locations', 'work_hours_from', 'work_hours_to',
                  'timezone', 'user_type', 'review']

        self.upref_mdata_valid_choices = dict(languages=[("en", "en"), ("sp", "sp")],
                                    locations=[("us", "us"), ("uk", "uk")],
                                    timezones=[("", ""), ("ACT", "Australia Central Time")],
                                    user_types=[("Researcher", "Researcher"), ("Analyst", "Analyst")])

    @with_context
    def test_register_form_with_upref_mdata_contains_fields(self):
        form = RegisterFormWithUserPrefMetadata()

        for field in self.fields:
            assert form.__contains__(field), 'Field %s is not in form' %field

    @with_context
    def test_register_form_with_upref_mdata_validates_with_valid_fields(self):
        import pybossa.core
        pybossa.core.upref_mdata_choices = self.upref_mdata_valid_choices

        form_data = dict(languages="en", locations="uk",
                        user_type="Researcher", timezone="")
        form = UserPrefMetadataForm(MultiDict(form_data))
        form.set_upref_mdata_choices()
        assert form.validate()

    @with_context
    def test_register_form_with_upref_mdata_with_invalid_language(self):
        import pybossa.core
        pybossa.core.upref_mdata_choices = self.upref_mdata_valid_choices

        form_data = dict(languages="somelang", locations="uk",
                        user_type="Researcher", timezone="")
        form = UserPrefMetadataForm(MultiDict(form_data))
        form.set_upref_mdata_choices()
        assert not form.validate()

    @with_context
    def test_register_form_with_upref_mdata_with_invalid_preferences(self):
        import pybossa.core
        pybossa.core.upref_mdata_choices = self.upref_mdata_valid_choices

        form_data = dict(languages="somelang", locations="someloc",
                        user_type="someutype", timezone="ZZZ")
        form = UserPrefMetadataForm(MultiDict(form_data))
        form.set_upref_mdata_choices()
        assert not form.validate()
        expected_form_errors = {
                        'work_hours_to':
                            ['Work Hours From, Work Hours To, and Timezone must be filled out for submission'],
                        'locations':
                            ["'someloc' is not a valid choice for this field"],
                        'user_type':
                            ['Not a valid choice'],
                        'languages':
                            ["'somelang' is not a valid choice for this field"],
                        'work_hours_from':
                            ['Work Hours From, Work Hours To, and Timezone must be filled out for submission'],
                        'timezone':
                            ['Not a valid choice', 'Work Hours From, Work Hours To, and Timezone must be filled out for submission']
                        }
        assert form.errors == expected_form_errors
