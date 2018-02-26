import io
import os
import re
from tempfile import NamedTemporaryFile
from urlparse import urlparse
import boto
from flask import current_app as app
from werkzeug.utils import secure_filename
import magic
from werkzeug.exceptions import BadRequest, InternalServerError
from pybossa.uploader.s3_connection import CustomConnection

allowed_mime_types = ['application/pdf',
                      'text/csv',
                      'text/richtext',
                      'text/tab-separated-values',
                      'text/xml',
                      'text/plain',
                      'application/oda',
                      'text/html',
                      'application/xml',
                      'image/jpeg',
                      'image/png',
                      'image/bmp',
                      'image/x-ms-bmp',
                      'image/gif']


def check_type(filename):
    mime_type = magic.from_file(filename, mime=True)
    if mime_type not in allowed_mime_types:
        raise BadRequest('File type not supported: {}'.format(mime_type))


def validate_directory(directory_name):
    invalid_chars = '[^\w\/]'
    if re.search(invalid_chars, directory_name):
        raise RuntimeError('Invalid character in directory name')


def tmp_file_from_string(string):
    """
    Create a temporary file with the given content
    """
    tmp_file = NamedTemporaryFile(delete=False)
    try:
        with io.open(tmp_file.name, 'w', encoding='utf8') as fp:
            fp.write(string)
    except Exception as e:
        os.unlink(tmp_file.name)
        raise e
    return tmp_file


def s3_upload_from_string(s3_bucket, string, filename, headers=None,
                          directory="", file_type_check=True,
                          return_key_only=False):
    """
    Upload a string to s3
    """
    tmp_file = tmp_file_from_string(string)
    return s3_upload_tmp_file(
            s3_bucket, tmp_file, filename, headers, directory, file_type_check,
            return_key_only)


def s3_upload_file_storage(s3_bucket, source_file, directory='',
                           file_type_check=True, return_key_only=False):
    """
    Upload a werzkeug FileStorage content to s3
    """
    filename = source_file.filename
    headers = {'Content-Type': source_file.content_type}
    tmp_file = NamedTemporaryFile(delete=False)
    source_file.save(tmp_file.name)
    return s3_upload_tmp_file(
            s3_bucket, tmp_file, filename, headers, directory, file_type_check,
            return_key_only)


def s3_upload_tmp_file(s3_bucket, tmp_file, filename,
                       headers, directory='', file_type_check=True,
                       return_key_only=False):
    """
    Upload the content of a temporary file to s3 and delete the file
    """
    try:
        if file_type_check:
            check_type(tmp_file.name)
        url = s3_upload_file(s3_bucket,
                             tmp_file.name,
                             filename,
                             headers,
                             directory,
                             return_key_only)
    finally:
        os.unlink(tmp_file.name)
    return url


def form_upload_directory(directory, filename):
    validate_directory(directory)
    app_dir = app.config.get('S3_UPLOAD_DIRECTORY')
    parts = [app_dir, directory, filename]
    return "/".join(part for part in parts if part)


def create_connection():
    kwargs = app.config.get('S3_CONN_KWARGS', {})
    return CustomConnection(**kwargs)


def s3_upload_file(s3_bucket, source_file_name, target_file_name,
                   headers, directory="", return_key_only=False):
    """
    Upload a file-type object to S3
    :param s3_bucket: AWS S3 bucket name
    :param source_file_name: name in local file system of the file to upload
    :param target_file_name: file name as should appear in S3
    :param headers: a dictionary of headers to set on the S3 object
    :param directory: path in S3 where the object needs to be stored
    :param return_key_only: return key name instead of full url
    """
    filename = secure_filename(target_file_name)
    upload_key = form_upload_directory(directory, filename)
    conn = create_connection()
    bucket = conn.get_bucket(s3_bucket, validate=False)

    key = bucket.new_key(upload_key)
    key.set_contents_from_filename(
        source_file_name, headers=headers,
        policy='bucket-owner-full-control')

    if return_key_only:
        return key.name
    url = key.generate_url(0, query_auth=False)
    return url.split('?')[0]


def get_s3_bucket_key(s3_bucket, s3_url):
    conn = create_connection()
    bucket = conn.get_bucket(s3_bucket, validate=False)
    obj = urlparse(s3_url)
    path = obj.path
    key = bucket.get_key(path, validate=False)
    return bucket, key


def get_file_from_s3(s3_bucket, s3_url):
    temp_file = NamedTemporaryFile()
    _, key = get_s3_bucket_key(s3_bucket, s3_url)
    key.get_contents_to_filename(temp_file.name)
    return temp_file


def delete_file_from_s3(s3_bucket, s3_url):
    try:
        bucket, key = get_s3_bucket_key(s3_bucket, s3_url)
        bucket.delete_key(key.name, version_id=key.version_id)
    except boto.exception.S3ResponseError:
        app.logger.exception('S3: unable to delete file {0}'.format(s3_url))
