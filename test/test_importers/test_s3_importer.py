# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2016 Scifabric LTD.
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

from pybossa.importers.s3 import BulkTaskS3Import
from default import with_context


class TestBulkTaskS3Import(object):

    form_data = {
        'files': ['myfile.png'],
        'bucket': 'mybucket'
    }

    @with_context
    def test_count_tasks_returns_0_if_no_files_to_import(self):
        form_data = {
            'files': [],
            'bucket': 'mybucket'
        }
        number_of_tasks = BulkTaskS3Import(**form_data).count_tasks()

        assert number_of_tasks == 0, number_of_tasks

    @with_context
    def test_count_tasks_returns_1_if_1_file_to_import(self):
        form_data = {
            'files': ['myfile.png'],
            'bucket': 'mybucket'
        }
        number_of_tasks = BulkTaskS3Import(**form_data).count_tasks()

        assert number_of_tasks == 1, number_of_tasks

    @with_context
    def test_tasks_return_emtpy_list_if_no_files_to_import(self):
        form_data = {
            'files': [],
            'bucket': 'mybucket'
        }
        tasks = BulkTaskS3Import(**form_data).tasks()

        assert tasks == [], tasks

    @with_context
    def test_tasks_returns_list_with_1_file_data_if_1_file_to_import(self):
        form_data = {
            'files': ['myfile.png'],
            'bucket': 'mybucket'
        }
        tasks = BulkTaskS3Import(**form_data).tasks()

        assert len(tasks) == 1, tasks

    @with_context
    def test_tasks_returns_tasks_with_fields_for_generic_files(self):
        #For generic file extensions: link, filename, url
        form_data = {
            'files': ['myfile.png'],
            'bucket': 'mybucket'
        }
        tasks = BulkTaskS3Import(**form_data).tasks()

        assert tasks[0]['info']['filename'] == "myfile.png"
        assert tasks[0]['info']['link'] == "https://mybucket.s3.amazonaws.com/myfile.png"
        assert tasks[0]['info']['url'] == "https://mybucket.s3.amazonaws.com/myfile.png"

    @with_context
    def test_tasks_attributes_for_image_files(self):
        #For image file extensions: link, filename, url, url_m, url_b, title
        image_ext = ['png', 'jpg', 'jpeg', 'gif']
        file_data = 'myfile.extension'

        for ext in image_ext:
            data = file_data.replace('extension', ext)
            form_data = {
                'files': [data],
                'bucket': 'mybucket'
            }
            tasks = BulkTaskS3Import(**form_data).tasks()

            assert tasks[0]['info']['filename'] == "myfile.%s" % ext
            assert tasks[0]['info']['link'] == "https://mybucket.s3.amazonaws.com/myfile.%s" % ext
            assert tasks[0]['info']['url'] == "https://mybucket.s3.amazonaws.com/myfile.%s" % ext
            assert tasks[0]['info']['url_m'] == "https://mybucket.s3.amazonaws.com/myfile.%s" % ext
            assert tasks[0]['info']['url_b'] == "https://mybucket.s3.amazonaws.com/myfile.%s" % ext
            assert tasks[0]['info']['title'] == "myfile.%s" % ext

    @with_context
    def test_tasks_attributes_for_pdf_files(self):
        #For pdf file extension: link, filename, url, pdf_url
        pdf_file_data = 'mypdf.pdf'

        form_data = {
            'files': [pdf_file_data],
            'bucket': 'mybucket'
        }
        tasks = BulkTaskS3Import(**form_data).tasks()

        assert tasks[0]['info']['filename'] == "mypdf.pdf"
        assert tasks[0]['info']['link'] == "https://mybucket.s3.amazonaws.com/mypdf.pdf"
        assert tasks[0]['info']['url'] == "https://mybucket.s3.amazonaws.com/mypdf.pdf"
        assert tasks[0]['info']['pdf_url'] == "https://mybucket.s3.amazonaws.com/mypdf.pdf"

    @with_context
    def test_tasks_attributes_for_video_files(self):
        #For video file extension: link, filename, url, video_url
        video_ext = ['mp4', 'm4v', 'ogg', 'ogv', 'webm', 'avi']
        file_data = 'myfile.extension'

        for ext in video_ext:
            data = file_data.replace('extension', ext)
            form_data = {
                'files': [data],
                'bucket': 'mybucket'
            }
            tasks = BulkTaskS3Import(**form_data).tasks()

            assert tasks[0]['info']['filename'] == "myfile.%s" % ext
            assert tasks[0]['info']['link'] == "https://mybucket.s3.amazonaws.com/myfile.%s" % ext
            assert tasks[0]['info']['url'] == "https://mybucket.s3.amazonaws.com/myfile.%s" % ext
            assert tasks[0]['info']['video_url'] == "https://mybucket.s3.amazonaws.com/myfile.%s" % ext

    @with_context
    def test_tasks_attributes_for_audio_files(self):
        #For audio file extension: link, filename, url, audio_url
        audio_ext = ['mp4', 'm4a', 'mp3', 'ogg', 'oga', 'webm', 'wav']
        file_data = 'myfile.extension'

        for ext in audio_ext:
            data = file_data.replace('extension', ext)
            form_data = {
                'files': [data],
                'bucket': 'mybucket'
            }
            tasks = BulkTaskS3Import(**form_data).tasks()

            assert tasks[0]['info']['filename'] == "myfile.%s" % ext
            assert tasks[0]['info']['link'] == "https://mybucket.s3.amazonaws.com/myfile.%s" % ext
            assert tasks[0]['info']['url'] == "https://mybucket.s3.amazonaws.com/myfile.%s" % ext
            assert tasks[0]['info']['audio_url'] == "https://mybucket.s3.amazonaws.com/myfile.%s" % ext
