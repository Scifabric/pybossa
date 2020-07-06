"""
Utilities to encode and decode zlib and base64 data.
"""
# Portions borrowed from:
# http://stackoverflow.com/questions/1089662/python-inflate-and-deflate-implementations
import base64
import zlib
from typing import Union


def decode_base64_and_inflate(b64string: Union[str, bytes]) -> bytes:
    """Turn a base64-encoded zlib-compressed blob
    back in to the original bytes.
    The opposite of :func:`deflate_and_base64_encode`.
    """
    if type(b64string) is bytes:
        b64string = b64string.decode('utf-8')
    decoded_data = base64.b64decode(b64string)
    return zlib.decompress(decoded_data, -15)


def deflate_and_base64_encode(string_val: Union[str, bytes]) -> bytes:
    """zlib-compress and base64-encode some data.
    The opposite of :func:`decode_base64_and_inflate`.
    """
    if type(string_val) is str:
        string_val = string_val.encode('utf-8')
    zlibbed_str = zlib.compress(string_val)
    compressed_string = zlibbed_str[2:-4]
    return base64.b64encode(compressed_string)


def decode_saml_xml(data: bytes) -> bytes:
    """Decodes some base64-encoded and possibly zipped string
    into an XML string.
    """
    decoded = base64.b64decode(data)
    # Is it XML yet?
    if decoded.strip().startswith(b'<'):
        return decoded

    # Try decode and inflate
    decoded = zlib.decompress(decoded, -15)
    # Is it XML yet?
    if decoded.strip().startswith(b'<'):
        return decoded

    raise ValueError("Does not look like an XML string!")
