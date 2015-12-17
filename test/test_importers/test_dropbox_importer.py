# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
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

import string
from pybossa.importers import BulkImportException
from pybossa.importers.dropbox import _BulkTaskDropboxImport


class Test_BulkTaskDropboxImport(object):

    dropbox_file_data = (u'{"bytes":286,'
        u'"link":"https://www.dropbox.com/s/l2b77qvlrequ6gl/test.txt?dl=0",'
        u'"name":"test.txt",'
        u'"icon":"https://www.dropbox.com/static/images/icons64/page_white_text.png"}')
    importer = _BulkTaskDropboxImport()

    def test_count_tasks_returns_0_if_no_files_to_import(self):
        form_data = {'files': [], 'type': 'dropbox'}
        number_of_tasks = self.importer.count_tasks(**form_data)

        assert number_of_tasks == 0, number_of_tasks

    def test_count_tasks_returns_1_if_1_file_to_import(self):
        form_data = {'files': [self.dropbox_file_data],
                     'type': 'dropbox'}
        number_of_tasks = self.importer.count_tasks(**form_data)

        assert number_of_tasks == 1, number_of_tasks

    def test_tasks_return_emtpy_list_if_no_files_to_import(self):
        form_data = {'files': [], 'type': 'dropbox'}
        tasks = self.importer.tasks(**form_data)

        assert tasks == [], tasks

    def test_tasks_returns_list_with_1_file_data_if_1_file_to_import(self):
        form_data = {'files': [self.dropbox_file_data],
                     'type': 'dropbox'}
        tasks = self.importer.tasks(**form_data)

        assert len(tasks) == 1, tasks

    def test_tasks_returns_tasks_with_fields_for_generic_files(self):
        #For generic file extensions: link, filename, link_raw
        form_data = {'files': [self.dropbox_file_data],
                     'type': 'dropbox'}
        tasks = self.importer.tasks(**form_data)

        assert tasks[0]['info']['filename'] == "test.txt"
        assert tasks[0]['info']['link'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.txt?dl=0"
        assert tasks[0]['info']['link_raw'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.txt?raw=1"

    def test_tasks_attributes_for_png_image_files(self):
        #For image file extensions: link, filename, link_raw, url_m, url_b, title
        png_file_data = (u'{"bytes":286,'
        u'"link":"https://www.dropbox.com/s/l2b77qvlrequ6gl/test.png?dl=0",'
        u'"name":"test.png",'
        u'"icon":"https://www.dropbox.com/static/images/icons64/page_white_text.png"}')

        form_data = {'files': [png_file_data],
                     'type': 'dropbox'}
        tasks = self.importer.tasks(**form_data)

        assert tasks[0]['info']['filename'] == "test.png"
        assert tasks[0]['info']['link'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.png?dl=0"
        assert tasks[0]['info']['link_raw'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.png?raw=1"
        assert tasks[0]['info']['url_m'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.png?raw=1"
        assert tasks[0]['info']['url_b'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.png?raw=1"
        assert tasks[0]['info']['title'] == "test.png"

    def test_tasks_attributes_for_jpg_image_files(self):
        #For image file extensions: link, filename, link_raw, url_m, url_b, title
        jpg_file_data = (u'{"bytes":286,'
        u'"link":"https://www.dropbox.com/s/l2b77qvlrequ6gl/test.jpg?dl=0",'
        u'"name":"test.jpg",'
        u'"icon":"https://www.dropbox.com/static/images/icons64/page_white_text.png"}')

        form_data = {'files': [jpg_file_data],
                     'type': 'dropbox'}
        tasks = self.importer.tasks(**form_data)

        assert tasks[0]['info']['filename'] == "test.jpg"
        assert tasks[0]['info']['link'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.jpg?dl=0"
        assert tasks[0]['info']['link_raw'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.jpg?raw=1"
        assert tasks[0]['info']['url_m'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.jpg?raw=1"
        assert tasks[0]['info']['url_b'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.jpg?raw=1"
        assert tasks[0]['info']['title'] == "test.jpg"

    def test_tasks_attributes_for_jpeg_image_files(self):
        #For image file extensions: link, filename, link_raw, url_m, url_b, title
        jpeg_file_data = (u'{"bytes":286,'
        u'"link":"https://www.dropbox.com/s/l2b77qvlrequ6gl/test.jpeg?dl=0",'
        u'"name":"test.jpeg",'
        u'"icon":"https://www.dropbox.com/static/images/icons64/page_white_text.png"}')

        form_data = {'files': [jpeg_file_data],
                     'type': 'dropbox'}
        tasks = self.importer.tasks(**form_data)

        assert tasks[0]['info']['filename'] == "test.jpeg"
        assert tasks[0]['info']['link'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.jpeg?dl=0"
        assert tasks[0]['info']['link_raw'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.jpeg?raw=1"
        assert tasks[0]['info']['url_m'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.jpeg?raw=1"
        assert tasks[0]['info']['url_b'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.jpeg?raw=1"
        assert tasks[0]['info']['title'] == "test.jpeg"

    def test_tasks_attributes_for_gif_image_files(self):
        #For image file extensions: link, filename, link_raw, url_m, url_b, title
        gif_file_data = (u'{"bytes":286,'
        u'"link":"https://www.dropbox.com/s/l2b77qvlrequ6gl/test.gif?dl=0",'
        u'"name":"test.gif",'
        u'"icon":"https://www.dropbox.com/static/images/icons64/page_white_text.png"}')

        form_data = {'files': [gif_file_data],
                     'type': 'dropbox'}
        tasks = self.importer.tasks(**form_data)

        assert tasks[0]['info']['filename'] == "test.gif"
        assert tasks[0]['info']['link'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.gif?dl=0"
        assert tasks[0]['info']['link_raw'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.gif?raw=1"
        assert tasks[0]['info']['url_m'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.gif?raw=1"
        assert tasks[0]['info']['url_b'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.gif?raw=1"
        assert tasks[0]['info']['title'] == "test.gif"

    def test_tasks_attributes_for_pdf_files(self):
        #For pdf file extension: link, filename, link_raw, pdf_url
        pdf_file_data = (u'{"bytes":286,'
        u'"link":"https://www.dropbox.com/s/l2b77qvlrequ6gl/test.pdf?dl=0",'
        u'"name":"test.pdf",'
        u'"icon":"https://www.dropbox.com/static/images/icons64/page_white_text.png"}')

        form_data = {'files': [pdf_file_data],
                     'type': 'dropbox'}
        tasks = self.importer.tasks(**form_data)

        assert tasks[0]['info']['filename'] == "test.pdf"
        assert tasks[0]['info']['link'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.pdf?dl=0"
        assert tasks[0]['info']['link_raw'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.pdf?raw=1"
        assert tasks[0]['info']['pdf_url'] == "https://dl.dropboxusercontent.com/s/l2b77qvlrequ6gl/test.pdf"

    def test_tasks_attributes_for_video_files(self):
        #For video file extension: link, filename, link_raw, video_url
        video_ext = ['mp4', 'm4v', 'ogg', 'ogv', 'webm', 'avi']
        file_data = (u'{"bytes":286,'
        u'"link":"https://www.dropbox.com/s/l2b77qvlrequ6gl/test.extension?dl=0",'
        u'"name":"test.extension",'
        u'"icon":"https://www.dropbox.com/static/images/icons64/page_white_text.png"}')

        for ext in video_ext:
            data = string.replace(file_data,'extension', ext)
            form_data = {'files': [data],
                         'type': 'dropbox'}
            tasks = self.importer.tasks(**form_data)

            assert tasks[0]['info']['filename'] == "test.%s" % ext
            assert tasks[0]['info']['link'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.%s?dl=0" % ext
            assert tasks[0]['info']['link_raw'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.%s?raw=1" % ext
            assert tasks[0]['info']['video_url'] == "https://dl.dropboxusercontent.com/s/l2b77qvlrequ6gl/test.%s" % ext

    def test_tasks_attributes_for_audio_files(self):
        #For audio file extension: link, filename, link_raw, audio_url
        audio_ext = ['mp4', 'm4a', 'mp3', 'ogg', 'oga', 'webm', 'wav']
        file_data = (u'{"bytes":286,'
        u'"link":"https://www.dropbox.com/s/l2b77qvlrequ6gl/test.extension?dl=0",'
        u'"name":"test.extension",'
        u'"icon":"https://www.dropbox.com/static/images/icons64/page_white_text.png"}')

        for ext in audio_ext:
            data = string.replace(file_data,'extension', ext)
            form_data = {'files': [data],
                         'type': 'dropbox'}
            tasks = self.importer.tasks(**form_data)

            assert tasks[0]['info']['filename'] == "test.%s" % ext
            assert tasks[0]['info']['link'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.%s?dl=0" % ext
            assert tasks[0]['info']['link_raw'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.%s?raw=1" % ext
            assert tasks[0]['info']['audio_url'] == "https://dl.dropboxusercontent.com/s/l2b77qvlrequ6gl/test.%s" % ext
