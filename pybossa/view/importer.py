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
from flask.ext.babel import lazy_gettext, gettext
from pybossa.util import unicode_csv_reader
import json
import requests


importers = []


def register_importer(cls):
    importers.append(cls)
    return cls


def enabled_importers(enabled_importer_names=None):
    if enabled_importer_names is None:
        return importers
    check = lambda i: i.template_id in enabled_importer_names
    return filter(check, importers)


class BulkImportException(Exception):
    pass


googledocs_urls = {
    'spreadsheet': None,
    'image': "https://docs.google.com/spreadsheet/ccc"
             "?key=0AsNlt0WgPAHwdHFEN29mZUF0czJWMUhIejF6dWZXdkE"
             "&usp=sharing",
    'sound': "https://docs.google.com/spreadsheet/ccc"
             "?key=0AsNlt0WgPAHwdEczcWduOXRUb1JUc1VGMmJtc2xXaXc"
             "&usp=sharing",
    'video': "https://docs.google.com/spreadsheet/ccc"
             "?key=0AsNlt0WgPAHwdGZ2UGhxSTJjQl9YNVhfUVhGRUdoRWc"
             "&usp=sharing",
    'map': "https://docs.google.com/spreadsheet/ccc"
           "?key=0AsNlt0WgPAHwdGZnbjdwcnhKRVNlN1dGXy0tTnNWWXc"
           "&usp=sharing",
    'pdf': "https://docs.google.com/spreadsheet/ccc"
           "?key=0AsNlt0WgPAHwdEVVamc0R0hrcjlGdXRaUXlqRXlJMEE"
           "&usp=sharing"}


class BulkTaskImportForm(Form):
    template_id = None
    form_id = None
    form_detector = None
    tasks = None
    get_data_url = None

    def __init__(self, *args, **kwargs):
        super(BulkTaskImportForm, self).__init__(*args, **kwargs)

    def import_csv_tasks(self, csvreader):
        headers = []
        fields = set(['state', 'quorum', 'calibration', 'priority_0',
                      'n_answers'])
        field_header_index = []

        for row in csvreader:
            if not headers:
                headers = row
                if len(headers) != len(set(headers)):
                    msg = gettext('The file you uploaded has '
                                  'two headers with the same name.')
                    raise BulkImportException(msg)
                field_headers = set(headers) & fields
                for field in field_headers:
                    field_header_index.append(headers.index(field))
            else:
                task_data = {"info": {}}
                for idx, cell in enumerate(row):
                    if idx in field_header_index:
                        task_data[headers[idx]] = cell
                    else:
                        task_data["info"][headers[idx]] = cell
                yield task_data

    def get_csv_data_from_request(self, r):
        if r.status_code == 403:
            msg = "Oops! It looks like you don't have permission to access" \
                " that file"
            raise BulkImportException(gettext(msg), 'error')
        if ((not 'text/plain' in r.headers['content-type']) and
                (not 'text/csv' in r.headers['content-type'])):
            msg = gettext("Oops! That file doesn't look like the right file.")
            raise BulkImportException(msg, 'error')

        csvcontent = StringIO(r.text)
        csvreader = unicode_csv_reader(csvcontent)
        return self.import_csv_tasks(csvreader)

    @property
    def variants(self):
        return [self.template_id]


@register_importer
class BulkTaskCSVImportForm(BulkTaskImportForm):
    msg_required = lazy_gettext("You must provide a URL")
    msg_url = lazy_gettext("Oops! That's not a valid URL. "
                           "You must provide a valid URL")
    csv_url = TextField(lazy_gettext('URL'),
                        [validators.Required(message=msg_required),
                         validators.URL(message=msg_url)])
    template_id = "csv"
    form_id = "csvform"
    form_detector = "csv_url"

    def get_data_url(self, form):
        return form.csv_url.data

    def tasks(self, form):
        dataurl = self.get_data_url(form)
        r = requests.get(dataurl)
        return self.get_csv_data_from_request(r)


@register_importer
class BulkTaskGDImportForm(BulkTaskImportForm):
    msg_required = lazy_gettext("You must provide a URL")
    msg_url = lazy_gettext("Oops! That's not a valid URL. "
                           "You must provide a valid URL")
    googledocs_url = TextField(lazy_gettext('URL'),
                               [validators.Required(message=msg_required),
                                   validators.URL(message=msg_url)])
    template_id = "gdocs"
    form_id = "gdform"
    form_detector = "googledocs_url"

    def get_data_url(self, form):
        return ''.join([form.googledocs_url.data, '&output=csv'])

    def tasks(self, form):
        dataurl = self.get_data_url(form)
        r = requests.get(dataurl)
        return self.get_csv_data_from_request(r)

    @property
    def variants(self):
        return [("-".join([self.template_id, mode]))
                for mode in googledocs_urls.keys()]


@register_importer
class BulkTaskEpiCollectPlusImportForm(BulkTaskImportForm):
    msg_required = lazy_gettext("You must provide an EpiCollect Plus "
                                "project name")
    msg_form_required = lazy_gettext("You must provide a Form name "
                                     "for the project")
    epicollect_project = TextField(lazy_gettext('Project Name'),
                                   [validators.Required(message=msg_required)])
    epicollect_form = TextField(lazy_gettext('Form name'),
                                [validators.Required(message=msg_required)])
    template_id = "epicollect"
    form_id = "epiform"
    form_detector = "epicollect_project"

    def import_epicollect_tasks(self, data):
        for d in data:
            yield {"info": d}

    def get_data_url(self, form):
        return 'http://plus.epicollect.net/%s/%s.json' % \
            (form.epicollect_project.data, form.epicollect_form.data)

    def get_epicollect_data_from_request(self, r):
        if r.status_code == 403:
            msg = "Oops! It looks like you don't have permission to access" \
                " the EpiCollect Plus project"
            raise BulkImportException(gettext(msg), 'error')
        if not 'application/json' in r.headers['content-type']:
            msg = "Oops! That project and form do not look like the right one."
            raise BulkImportException(gettext(msg), 'error')
        return self.import_epicollect_tasks(json.loads(r.text))

    def tasks(self, form):
        dataurl = self.get_data_url(form)
        r = requests.get(dataurl)
        return self.get_epicollect_data_from_request(r)
