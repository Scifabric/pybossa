"""
Functions and classes that deal with signing data and making digests.
"""
import base64
import hashlib
import logging
from typing import ClassVar, Sequence, Tuple, Union
from urllib.parse import urlencode

import OpenSSL.crypto

from flask_saml2.types import X509, PKey, XmlNode

from .utils import certificate_to_string
from .xml_templates import XmlTemplate

logger = logging.getLogger(__name__)


class Digester:
    """Base class for all the digest methods.
    SAML2 digest methods have an identifier in the form of a URL,
    and must produce a text digest.

    Subclasses should set the :attr:`uri` attribute
    and provide a :meth:`make_digest` method.

    Implemented digest methods: :class:`Sha1Digester`, :class:`Sha256Digester`.

    Example:

    .. code-block:: python

        >>> from flask_saml2.signing import Sha1Digester
        >>> digester = Sha1Digester()
        >>> digester(b'Hello, world!')
        'lDpwLQbzRZmu4fjajvn3KWAx1pk='
    """
    #: The URI identifing this digest method
    uri: ClassVar[str]

    def __call__(self, data: bytes) -> str:
        """Make a hex digest of some binary data.
        """
        return base64.b64encode(self.make_digest(data)).decode('utf-8')

    def make_digest(self, data: bytes) -> bytes:
        """Make a binary digest of some binary data using this digest method.
        """
        raise NotImplementedError


class Sha1Digester(Digester):
    uri = 'http://www.w3.org/2000/09/xmldsig#sha1'

    def make_digest(self, data: bytes) -> bytes:
        return hashlib.sha1(data).digest()


class Sha256Digester(Digester):
    uri = 'http://www.w3.org/2001/04/xmlenc#sha256'

    def make_digest(self, data: bytes) -> bytes:
        return hashlib.sha256(data).digest()


class Signer:
    """
    Sign some data with a particular algorithm. Each Signer may take different
    constructor arguments, but each will have a uri attribute and will sign
    data when called.

    Implemented signers: :class:`RsaSha1Signer`.

    Example:

    .. code-block:: python

        >>> from flask_saml2.signing import RsaSha1Signer
        >>> from flask_saml2.utils import private_key_from_file
        >>> key = private_key_from_file('tests/keys/sample/idp-private-key.pem')
        >>> signer = RsaSha1Signer(private_key)
        >>> signer(b'Hello, world!')
        'Yplg1oQDPLiozAWoY9ykgQ4eicojNnU+KjRrwGp67jHM5FGkQZ71Pk1Bgo631WA5B1hopQByRh/elqtEEN+vRA=='
    """
    #: The URI identifing this signing method
    uri: ClassVar[str]

    def __call__(self, data: bytes) -> str:
        """Sign some binary data and return the string output."""
        raise NotImplementedError


class RsaSha1Signer(Signer):
    uri = 'http://www.w3.org/2000/09/xmldsig#rsa-sha1'

    def __init__(self, key: Union[X509, PKey]):
        self.key = key

    def __call__(self, data: bytes):
        data = OpenSSL.crypto.sign(self.key, data, "sha1")
        return base64.b64encode(data).decode('ascii')


class RsaSha256Signer(Signer):
    uri = 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha256'

    def __init__(self, key: Union[X509, PKey]):
        self.key = key

    def __call__(self, data: bytes):
        data = OpenSSL.crypto.sign(self.key, data, "sha256")
        return base64.b64encode(data).decode('ascii')


class SignedInfoTemplate(XmlTemplate):
    """A ``<SignedInfo>`` node, such as:

    .. code-block:: xml

        <ds:SignedInfo xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
            <ds:CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"></ds:CanonicalizationMethod>
            <ds:SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"></ds:SignatureMethod>
            <ds:Reference URI="#${REFERENCE_URI}">
                <ds:Transforms>
                    <ds:Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"></ds:Transform>
                    <ds:Transform Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"></ds:Transform>
                </ds:Transforms>
                <ds:DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"></ds:DigestMethod>
                <ds:DigestValue>${SUBJECT_DIGEST}</ds:DigestValue>
            </ds:Reference>
        </ds:SignedInfo>
    """
    namespace = 'ds'

    def generate_xml(self):
        return self.element('SignedInfo', children=[
            self._get_canon_method(),
            self._get_signature_method(),
            self._get_reference(),
        ])

    def _get_canon_method(self):
        return self.element('CanonicalizationMethod', attrs={
            'Algorithm': 'http://www.w3.org/2001/10/xml-exc-c14n#'})

    def _get_signature_method(self):
        return self.element('SignatureMethod', attrs={
            'Algorithm': self.params['SIGNER'].uri})

    def _get_reference(self):
        return self.element('Reference', attrs={
            'URI': '#' + self.params['REFERENCE_URI']
        }, children=[
            self._get_tranforms(),
            self.element('DigestMethod', attrs={
                'Algorithm': self.params['DIGESTER'].uri,
            }),
            self.element('DigestValue', text=self.params['SUBJECT_DIGEST'])
        ])

    def _get_tranforms(self):
        return self.element('Transforms', children=[
            self.element('Transform', attrs={
                'Algorithm': 'http://www.w3.org/2000/09/xmldsig#enveloped-signature'
            }),
            self.element('Transform', attrs={
                'Algorithm': 'http://www.w3.org/2001/10/xml-exc-c14n#'
            }),
        ])

    """
    """


class SignatureTemplate(XmlTemplate):
    """
    A ``<Signature>`` node, such as:

    .. code-block:: xml

        <ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
            ${SIGNED_INFO}
            <ds:SignatureValue>${RSA_SIGNATURE}</ds:SignatureValue>
            <ds:KeyInfo>
                <ds:X509Data>
                    <ds:X509Certificate>${CERTIFICATE}</ds:X509Certificate>
                </ds:X509Data>
            </ds:KeyInfo>
        </ds:Signature>
    """
    namespace = 'ds'

    @classmethod
    def sign(
        cls,
        subject: str,
        certificate: X509,
        digester: Digester,
        signer: Signer,
        reference_uri: str,
    ):
        """Create a :class:`SignatureTemplate` by signing a ``subject`` string.

        :param subject: The string to sign.
            This is usually the canonical string representation
            of the XML node this ``<Signature>`` verifies.
        :param certificate: The certificate to sign the data with
        :param digester: The algorithm used to make the digest
        :param signer: The algorithm used to sign the data
        :param reference_uri: The ID of the element that is signed

        See also: :meth:`SignableTemplate.sign`
        """
        logger.debug('SignatureTemplate.sign - Begin.')
        logger.debug('Subject: ' + subject)

        # Hash the subject.
        subject_digest = digester(subject.encode('utf-8'))
        logger.debug('Subject digest: {}'.format(subject_digest))

        # Create signed_info.
        signed_info = SignedInfoTemplate({
            'REFERENCE_URI': reference_uri,
            'SUBJECT_DIGEST': subject_digest,
            'DIGESTER': digester,
            'SIGNER': signer,
        })

        signature = signer(signed_info.get_xml_string().encode('utf-8'))
        logger.debug('Signature: {}'.format(signature))

        return cls({
            'SIGNATURE': signature,
            'SIGNED_INFO': signed_info,
            'CERTIFICATE': certificate_to_string(certificate),
        })

    def generate_xml(self):
        return self.element('Signature', children=[
            self.params['SIGNED_INFO'].xml,
            self._get_signature_value(),
            self._get_key_info(),
        ])

    def _get_signature_value(self):
        return self.element('SignatureValue', text=self.params['SIGNATURE'])

    def _get_key_info(self):
        return self.element('KeyInfo', children=[
            self.element('X509Data', children=[
                self.element('X509Certificate', text=self.params['CERTIFICATE'])
            ])
        ])


class SignableTemplate(XmlTemplate):
    """
    An :class:`XmlTemplate` that supports being signed,
    by adding an :class:`\\<Signauture\\> <SignatureTemplate>` element.
    """
    #: The element index where the signature should be inserted
    signature_index = 1

    #: The parameter that contains the element ID
    #:
    #: See :meth:`get_id` and :meth:`sign`
    id_parameter: str

    def sign(
        self,
        certificate: X509,
        digester: Digester,
        signer: Signer,
    ) -> XmlNode:
        """Cryptographically sign this template by inserting a
        :class:`\\<Signature\\> <SignatureTemplate>` element.

        The ID of the node to sign is fetched from :meth:`get_id`.

        :param certificate: The certificate to sign the data with
        :param digester: The algorithm used to make the digest
        :param signer: The algorithm used to sign the data
        """
        signature = self.make_signature(certificate, digester, signer)
        self.add_signature(signature)

    def make_signature(
        self,
        certificate: X509,
        digester: Digester,
        signer: Signer,
    ) -> SignatureTemplate:
        """
        Create XML ``<Signature>`` node for the ``subject`` text.
        """
        subject = self.get_xml_string()
        return SignatureTemplate.sign(subject, certificate, digester, signer, self.get_id())

    def add_signature(self, signature: SignatureTemplate):
        """Insert a :class:`\\<Signature\\> <SignatureTemplate>` into this node.
        """
        self.xml.insert(self.signature_index, signature.xml)

    def get_id(self) -> str:
        """Get the ID of the root node, required to :meth:`sign` this node.
        By default, grabs the ID from the parameter named in :attr:`id_parameter`.
        """
        return self.params[self.id_parameter]


def sign_query_parameters(
    signer: Signer,
    bits: Sequence[Tuple[str, str]],
) -> str:
    """
    Sign the bits of a query string.

    .. code-block:: python

        >>> signer = ...  # A Signer instance
        >>> bits = [('Foo', '1'), ('Bar', '2')]
        >>> sign_query_parameters(signer, bits)
        "Foo=1&Bar=2&SigAlg=...&Signature=..."
    """
    bits = list(bits)

    # Add the signature algorithm parameter
    bits.append(('SigAlg', signer.uri))

    # Sign the encoded query string
    data = urlencode(bits, encoding='utf-8').encode('utf-8')
    bits.append(('Signature', signer(data)))

    return urlencode(bits, encoding='utf-8')
