import boto
from flask import current_app as app
from werkzeug.utils import secure_filename
import magic
from tempfile import NamedTemporaryFile
import os
from werkzeug.exceptions import BadRequest, InternalServerError
import re
import io
from urlparse import urlparse
import tempfile

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
        raise BadRequest("File type not supported: {}".format(mime_type))


def validate_directory(directory_name):
    invalid_chars = "[^\w\/]"
    if re.search(invalid_chars, directory_name):
        raise RuntimeError("Invalid character in directory name")


def tmp_file_from_string(string):
    """
    Create a temporary file with the given content
    """
    tmp_file = NamedTemporaryFile(delete=False)
    try:
        with io.open(tmp_file.name, "w", encoding="utf8") as fp:
            fp.write(string)
    except Exception as e:
        os.unlink(tmp_file.name)
        raise e
    return tmp_file


def s3_upload_from_string(s3_bucket, string, filename, headers=None, directory="", file_type_check=True):
    """
    Upload a string to s3
    """
    tmp_file = tmp_file_from_string(string)
    return s3_upload_tmp_file(
            s3_bucket, tmp_file, filename, headers, directory, file_type_check)


def s3_upload_file_storage(s3_bucket, source_file, directory="", public=False, file_type_check=True):
    """
    Upload a werzkeug FileStorage content to s3
    """
    filename = source_file.filename
    headers = {"Content-Type": source_file.content_type}
    tmp_file = NamedTemporaryFile(delete=False)
    source_file.save(tmp_file.name)
    return s3_upload_tmp_file(
            s3_bucket, tmp_file, filename, headers, directory, public, file_type_check)


def s3_upload_tmp_file(s3_bucket, tmp_file, filename,
                       headers, directory="", public=False, file_type_check=True):
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
                             public)
    finally:
        os.unlink(tmp_file.name)
    return url


def form_upload_directory(directory, filename):
    validate_directory(directory)
    app_dir = app.config.get("S3_UPLOAD_DIRECTORY")
    parts = [app_dir, directory, filename]
    return "/".join(part for part in parts if part)


def s3_upload_file(s3_bucket, source_file_name, target_file_name,
                   headers, directory="", public=False):
    """
    Upload a file-type object to S3
    :param s3_bucket: AWS S3 bucket name
    :param source_file_name: name in local file system of the file to upload
    :param target_file_name: file name as should appear in S3
    :param headers: a dictionary of headers to set on the S3 object
    :param directory: path in S3 where the object needs to be stored
    :param public: should the S3 object be publicly accessible
    """
    filename = secure_filename(target_file_name)
    upload_key = form_upload_directory(directory, filename)
    conn = boto.connect_s3()
    bucket = conn.get_bucket(s3_bucket)

    key = bucket.new_key(upload_key)
    key.set_contents_from_filename(
        source_file_name, headers=headers,
        policy="bucket-owner-full-control")

    if public:
        key.make_public()

    return key.generate_url(0).split('?', 1)[0]

def get_s3_bucket_key(s3_bucket, s3_url):
    conn = boto.connect_s3()
    bucket = conn.get_bucket(s3_bucket, validate=False)
    obj = urlparse(s3_url)
    path = obj.path
    key = bucket.get_key(path)
    return bucket, key

def get_file_from_s3(s3_bucket, s3_url):
    temp_file = tempfile.NamedTemporaryFile()
    _ , key = get_s3_bucket_key(s3_bucket, s3_url)
    key.get_contents_to_filename(temp_file.name)
    return temp_file

def delete_file_from_s3(s3_bucket, s3_url):
    try:
        bucket,key = get_s3_bucket_key(s3_bucket, s3_url)
        bucket.delete_key(key.name, version_id=key.version_id)
    except S3ResponseError as e:
        app.logger.exception('S3: unable to delete file {0}'.format(s3_url))
