import boto
from flask import current_app as app
from werkzeug.utils import secure_filename
import magic
from tempfile import NamedTemporaryFile
import os
from werkzeug.exceptions import BadRequest, InternalServerError
import re
import io


allowed_mime_types = ['application/pdf',
                      'text/csv',
                      'text/richtext',
                      'text/tab-separated-values',
                      'text/xml',
                      'text/plain',
                      'application/oda',
                      'text/html',
                      'application/xml']


def check_type(filename):
    mime_type = magic.from_file(filename, mime=True)
    if mime_type not in allowed_mime_types:
        raise BadRequest("File Type Not Supported")


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


def s3_upload_from_string(string, filename, headers=None, directory=""):
    """
    Upload a string to s3
    """
    tmp_file = tmp_file_from_string(string)
    return s3_upload_tmp_file(tmp_file, filename, headers, directory)


def s3_upload_file_storage(source_file, directory=""):
    """
    Upload a werzkeug FileStorage content to s3
    """
    filename = source_file.filename
    headers = {"Content-Type": source_file.content_type}
    tmp_file = NamedTemporaryFile(delete=False)
    source_file.save(tmp_file.name)
    return s3_upload_tmp_file(tmp_file, filename, headers, directory)


def s3_upload_tmp_file(tmp_file, filename, headers, directory=""):
    """
    Upload the content of a temporary file to s3 and delete the file
    """
    try:
        check_type(tmp_file.name)
        with io.open(tmp_file.name, encoding="utf8") as fp:
            url = s3_upload_file(fp, filename, headers, directory)
    finally:
        os.unlink(tmp_file.name)
    return url


def form_upload_directory(directory, filename):
    validate_directory(directory)
    app_dir = app.config.get("S3_UPLOAD_DIRECTORY")
    parts = [app_dir, directory, filename]
    return "/".join(part for part in parts if part)


def s3_upload_file(fp, filename, headers, directory=""):
    """
    Upload a file-type object to s3
    """
    if "S3_BUCKET" not in app.config:
        raise InternalServerError("S3 bucket not configured")

    filename = secure_filename(filename)
    upload_key = form_upload_directory(directory, filename)
    conn = boto.connect_s3(app.config.get("S3_KEY"),
                           app.config.get("S3_SECRET"))
    bucket = conn.get_bucket(app.config["S3_BUCKET"])

    key = bucket.new_key(upload_key)
    key.set_contents_from_file(fp, headers=headers)

    return key.generate_url(0).split('?', 1)[0]
