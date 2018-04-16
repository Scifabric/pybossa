from flask import request
from pybossa.contributions_guard import ContributionsGuard
from pybossa.core import signer
from pybossa.cookies import CookieHandler
from pybossa.password_manager import ProjectPasswdManager


def get_pwd_manager(project):
    timeout = project.info.get('timeout')
    cookie_timeout = max(timeout, ContributionsGuard.STAMP_TTL)
    cookie_handler = CookieHandler(request, signer, cookie_timeout)
    pwd_manager = ProjectPasswdManager(cookie_handler)
    return pwd_manager
