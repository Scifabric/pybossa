# This file is part of PyBOSSA.
#
# PyBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBOSSA.  If not, see <http://www.gnu.org/licenses/>.

from StringIO import StringIO
from flaskext.wtf import Form, TextField, validators
from flaskext.babel import lazy_gettext
import pybossa.model as model
from pybossa.core import db
from pybossa.util import unicode_csv_reader
import json
import requests


class BulkImportException(Exception):
    pass


class BulkTaskCSVImportForm(Form):
    msg_required = lazy_gettext("You must provide a URL")
    msg_url = lazy_gettext("Oops! That's not a valid URL. You must provide a valid URL")
    csv_url = TextField(lazy_gettext('URL'),
                        [validators.Required(message=msg_required),
                         validators.URL(message=msg_url)])


class BulkTaskGDImportForm(Form):
    msg_required = lazy_gettext("You must provide a URL")
    msg_url = lazy_gettext("Oops! That's not a valid URL. You must provide a valid URL")
    googledocs_url = TextField(lazy_gettext('URL'),
                               [validators.Required(message=msg_required),
                                   validators.URL(message=msg_url)])


class BulkTaskEpiCollectPlusImportForm(Form):
    msg_required = lazy_gettext("You must provide an EpiCollect Plus project name")
    msg_form_required = lazy_gettext("You must provide a Form name for the project")
    epicollect_project = TextField(lazy_gettext('Project Name'),
                                   [validators.Required(message=msg_required)])
    epicollect_form = TextField(lazy_gettext('Form name'),
                                [validators.Required(message=msg_required)])


def import_csv_tasks(app, csvreader):
    headers = []
    fields = set(['state', 'quorum', 'calibration', 'priority_0',
                  'n_answers'])
    field_header_index = []
    empty = True

    for row in csvreader:
        print row
        if not headers:
            headers = row
            if len(headers) != len(set(headers)):
                msg = lazy_gettext('The file you uploaded has two headers with the same name.')
                raise BulkImportException(msg)
            field_headers = set(headers) & fields
            for field in field_headers:
                field_header_index.append(headers.index(field))
        else:
            info = {}
            task = model.Task(app=app)
            for idx, cell in enumerate(row):
                if idx in field_header_index:
                    setattr(task, headers[idx], cell)
                else:
                    info[headers[idx]] = cell
            task.info = info
            db.session.add(task)
            db.session.commit()
            empty = False
    if empty:
        raise BulkImportException(lazy_gettext('Oops! It looks like the file is empty.'))


def import_epicollect_tasks(app, data):
    for d in data:
        task = model.Task(app=app)
        task.info = d
        db.session.add(task)
    db.session.commit()

googledocs_urls = {
    'image': "https://docs.google.com/spreadsheet/ccc"
             "?key=0AsNlt0WgPAHwdHFEN29mZUF0czJWMUhIejF6dWZXdkE"
             "&usp=sharing",
    'sound': "https://docs.google.com/spreadsheet/ccc"
             "?key=0AsNlt0WgPAHwdEczcWduOXRUb1JUc1VGMmJtc2xXaXc"
             "&usp=sharing",
    'map': "https://docs.google.com/spreadsheet/ccc"
           "?key=0AsNlt0WgPAHwdGZnbjdwcnhKRVNlN1dGXy0tTnNWWXc"
           "&usp=sharing",
    'pdf': "https://docs.google.com/spreadsheet/ccc"
           "?key=0AsNlt0WgPAHwdEVVamc0R0hrcjlGdXRaUXlqRXlJMEE"
           "&usp=sharing"}


def get_data_url_for_csv(form):
    return form.csv_url.data

def get_data_url_for_gdocs(form):
    return ''.join([form.googledocs_url.data, '&output=csv'])

def get_data_url_for_epicollect(form):
    return 'http://plus.epicollect.net/%s/%s.json' % \
        (form.epicollect_project.data, form.epicollect_form.data)


def get_csv_data_from_request(app, r):
    if r.status_code == 403:
        msg = "Oops! It looks like you don't have permission to access" \
            " that file"
        raise BulkImportException(lazy_gettext(msg), 'error')
    if ((not 'text/plain' in r.headers['content-type']) and
       (not 'text/csv' in r.headers['content-type'])):
        msg = lazy_gettext("Oops! That file doesn't look like the right file.")
        raise BulkImportException(msg, 'error')

    csvcontent = StringIO(r.text)
    csvreader = unicode_csv_reader(csvcontent)
    return import_csv_tasks(app, csvreader)


def get_epicollect_data_from_request(app, r):
    if r.status_code == 403:
        msg = "Oops! It looks like you don't have permission to access" \
            " the EpiCollect Plus project"
        raise BulkImportException(lazy_gettext(msg), 'error')
    if not 'application/json' in r.headers['content-type']:
        msg = "Oops! That project and form do not look like the right one."
        raise BulkImportException(lazy_gettext(msg), 'error')
    return import_epicollect_tasks(app, json.loads(r.text))

def handle_import_from_csv(app, form):
    dataurl = get_data_url_for_csv(form)
    r = requests.get(dataurl)
    return get_csv_data_from_request(app, r)

def handle_import_from_gdocs(app, form):
    dataurl = get_data_url_for_gdocs(form)
    r = requests.get(dataurl)
    return get_csv_data_from_request(app, r)

def handle_import_from_epicollect(app, form):
    dataurl = get_data_url_for_epicollect(form)
    r = requests.get(dataurl)
    return get_epicollect_data_from_request(app, r)


importer_forms = [
    ('csv_url', handle_import_from_csv,
     'csvform', BulkTaskCSVImportForm, "csv"),        
    ('googledocs_url', handle_import_from_gdocs,
     'gdform', BulkTaskGDImportForm, "gdocs"),
    ('epicollect_project', handle_import_from_epicollect,
     'epiform', BulkTaskEpiCollectPlusImportForm, "epicollect")]
