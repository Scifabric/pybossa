from default import with_context, with_context_settings
from pybossa import otp
from flask import current_app

@with_context
def test_create_otp():
    user_email = 'test@test.com'
    secret = str(otp.generate_otp_secret(user_email))
    assert otp.retrieve_user_otp_secret(user_email) == secret, ('', secret)


@with_context
def test_get_otp_no_email():
    user_email = 'not@here.com'
    assert otp.retrieve_user_otp_secret(user_email) is None


@with_context
def test_create_token():
    user_email = 'test@test.com'
    token = otp.generate_url_token(user_email)
    assert otp.retrieve_email_for_token(token) == user_email


@with_context
def test_get_token_no_email():
    assert otp.retrieve_email_for_token('not@here.com') is None


@with_context
def test_expire_token():
    user_email = 'test@test.com'
    token = otp.generate_url_token(user_email)
    otp.expire_token(token)
    assert otp.retrieve_email_for_token(token) is None


@with_context_settings(ENABLE_TWO_FACTOR_AUTH=True)
def test_otp_enabled():
    user_email = 'test@test.com'
    assert otp.is_enabled(user_email, current_app.config) is True

@with_context_settings(ENABLE_TWO_FACTOR_AUTH=False)
def test_otp_disabled():
    user_email = 'test@test.com'
    assert otp.is_enabled(user_email, current_app.config) is False

@with_context_settings(ENABLE_TWO_FACTOR_AUTH=True, BYPASS_TWO_FACTOR_AUTH=["test@test.com"])
def test_otp_enabled_user_bypass():
    user_email = 'test@test.com'
    assert otp.is_enabled(user_email, current_app.config) is False

@with_context_settings(ENABLE_TWO_FACTOR_AUTH=False, BYPASS_TWO_FACTOR_AUTH=["test@test.com"])
def test_otp_disabled_user_bypass():
    user_email = 'test@test.com'
    assert otp.is_enabled(user_email, current_app.config) is False

@with_context_settings(ENABLE_TWO_FACTOR_AUTH=True, BYPASS_TWO_FACTOR_AUTH=["test2@test.com"])
def test_otp_enabled_user_no_bypass():
    user_email = 'test@test.com'
    assert otp.is_enabled(user_email, current_app.config) is True

@with_context_settings(ENABLE_TWO_FACTOR_AUTH=False, BYPASS_TWO_FACTOR_AUTH=["test2@test.com"])
def test_otp_disabled_user_no_bypass():
    user_email = 'test@test.com'
    assert otp.is_enabled(user_email, current_app.config) is False
