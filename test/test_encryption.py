# -*- coding: utf-8 -*-
from pybossa.encryption import AESWithGCM


class TestAes(object):

    def setUp(self):
        iv_length = 12
        tag_length = 16
        secret = bytearray('very secret', 'ascii')
        self.aes = AESWithGCM(secret, iv_length, tag_length)

    def test_aes(self):
        text = 'testing simple encrytion'
        encrypted = self.aes.encrypt(text)
        assert encrypted != text
        decrypted = self.aes.decrypt(encrypted)
        assert decrypted == text

    def test_aes_2(self):
        original = 'this is a test string I plan to encrypt'
        encrypted = 'DMj4/yC2pgzgAg76TApmk7zVZlaG0B47KASCnS/TqH6fQpA9UaHjmGLHqCfvGVVQcSivX76Oy349QivZjOJ2yfXZRb0='
        secret = bytearray('this is my super secret key', 'ascii')
        aes = AESWithGCM(secret)
        assert aes.decrypt(encrypted) == original

    def test_aes_unicode(self):
        text = u'∀ z ∈ ℂ, ζ(z) = 0 ⇒ ((z ∈ -2ℕ) ∨ (Re(z) = -½))'
        encrypted = self.aes.encrypt(text.encode('utf-8'))
        decrypted = self.aes.decrypt(encrypted).decode('utf-8')
        assert text == decrypted
