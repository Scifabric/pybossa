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

from pybossa.importers import BulkImportException
from pybossa.importers.dropbox import BulkTaskDropboxImport
from default import with_context


class TestBulkTaskDropboxImport(object):

    dropbox_file_data = ('{"bytes":286,'
        '"link":"https://www.dropbox.com/s/l2b77qvlrequ6gl/test.txt?dl=0",'
        '"name":"test.txt",'
        '"icon":"https://www.dropbox.com/static/images/icons64/page_white_text.png"}')

    @with_context
    def test_count_tasks_returns_0_if_no_files_to_import(self):
        form_data = {'files': []}
        number_of_tasks = BulkTaskDropboxImport(**form_data).count_tasks()

        assert number_of_tasks == 0, number_of_tasks

    @with_context
    def test_count_tasks_returns_1_if_1_file_to_import(self):
        form_data = {'files': [self.dropbox_file_data]}
        number_of_tasks = BulkTaskDropboxImport(**form_data).count_tasks()

        assert number_of_tasks == 1, number_of_tasks

    @with_context
    def test_tasks_return_emtpy_list_if_no_files_to_import(self):
        form_data = {'files': []}
        tasks = BulkTaskDropboxImport(**form_data).tasks()

        assert tasks == [], tasks

    @with_context
    def test_tasks_returns_list_with_1_file_data_if_1_file_to_import(self):
        form_data = {'files': [self.dropbox_file_data]}
        tasks = BulkTaskDropboxImport(**form_data).tasks()

        assert len(tasks) == 1, tasks

    @with_context
    def test_tasks_returns_tasks_with_fields_for_generic_files(self):
        #For generic file extensions: link, filename, link_raw
        form_data = {'files': [self.dropbox_file_data]}
        tasks = BulkTaskDropboxImport(**form_data).tasks()

        assert tasks[0]['info']['filename'] == "test.txt"
        assert tasks[0]['info']['link'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.txt?dl=0"
        assert tasks[0]['info']['link_raw'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.txt?raw=1"

    @with_context
    def test_tasks_attributes_for_image_files(self):
        #For image file extensions: link, filename, link_raw, url_m, url_b, title
        image_ext = ['png', 'jpg', 'jpeg', 'gif']
        file_data = ('{"bytes":286,'
        '"link":"https://www.dropbox.com/s/l2b77qvlrequ6gl/test.extension?dl=0",'
        '"name":"test.extension",'
        '"icon":"https://www.dropbox.com/static/images/icons64/page_white_text.extension"}')

        for ext in image_ext:
            data = file_data.replace('extension', ext)
            form_data = {'files': [data]}
            tasks = BulkTaskDropboxImport(**form_data).tasks()

            assert tasks[0]['info']['filename'] == "test.%s" % ext
            assert tasks[0]['info']['link'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.%s?dl=0" % ext
            assert tasks[0]['info']['link_raw'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.%s?raw=1" % ext
            assert tasks[0]['info']['url_m'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.%s?raw=1" % ext
            assert tasks[0]['info']['url_b'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.%s?raw=1" % ext
            assert tasks[0]['info']['title'] == "test.%s" % ext

    @with_context
    def test_tasks_attributes_for_pdf_files(self):
        #For pdf file extension: link, filename, link_raw, pdf_url
        pdf_file_data = ('{"bytes":286,'
        '"link":"https://www.dropbox.com/s/l2b77qvlrequ6gl/test.pdf?dl=0",'
        '"name":"test.pdf",'
        '"icon":"https://www.dropbox.com/static/images/icons64/page_white_text.png"}')

        form_data = {'files': [pdf_file_data]}
        tasks = BulkTaskDropboxImport(**form_data).tasks()

        assert tasks[0]['info']['filename'] == "test.pdf"
        assert tasks[0]['info']['link'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.pdf?dl=0"
        assert tasks[0]['info']['link_raw'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.pdf?raw=1"
        assert tasks[0]['info']['pdf_url'] == "https://dl.dropboxusercontent.com/s/l2b77qvlrequ6gl/test.pdf"

    @with_context
    def test_tasks_attributes_for_video_files(self):
        #For video file extension: link, filename, link_raw, video_url
        video_ext = ['mp4', 'm4v', 'ogg', 'ogv', 'webm', 'avi']
        file_data = ('{"bytes":286,'
        '"link":"https://www.dropbox.com/s/l2b77qvlrequ6gl/test.extension?dl=0",'
        '"name":"test.extension",'
        '"icon":"https://www.dropbox.com/static/images/icons64/page_white_text.png"}')

        for ext in video_ext:
            data = file_data.replace('extension', ext)
            form_data = {'files': [data]}
            tasks = BulkTaskDropboxImport(**form_data).tasks()

            assert tasks[0]['info']['filename'] == "test.%s" % ext
            assert tasks[0]['info']['link'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.%s?dl=0" % ext
            assert tasks[0]['info']['link_raw'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.%s?raw=1" % ext
            assert tasks[0]['info']['video_url'] == "https://dl.dropboxusercontent.com/s/l2b77qvlrequ6gl/test.%s" % ext

    @with_context
    def test_tasks_attributes_for_audio_files(self):
        #For audio file extension: link, filename, link_raw, audio_url
        audio_ext = ['mp4', 'm4a', 'mp3', 'ogg', 'oga', 'webm', 'wav']
        file_data = ('{"bytes":286,'
        '"link":"https://www.dropbox.com/s/l2b77qvlrequ6gl/test.extension?dl=0",'
        '"name":"test.extension",'
        '"icon":"https://www.dropbox.com/static/images/icons64/page_white_text.png"}')

        for ext in audio_ext:
            data = file_data.replace('extension', ext)
            form_data = {'files': [data]}
            tasks = BulkTaskDropboxImport(**form_data).tasks()

            assert tasks[0]['info']['filename'] == "test.%s" % ext
            assert tasks[0]['info']['link'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.%s?dl=0" % ext
            assert tasks[0]['info']['link_raw'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.%s?raw=1" % ext
            assert tasks[0]['info']['audio_url'] == "https://dl.dropboxusercontent.com/s/l2b77qvlrequ6gl/test.%s" % ext
