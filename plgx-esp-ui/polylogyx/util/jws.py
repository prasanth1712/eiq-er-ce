import hashlib
import time
from datetime import datetime
import json
import base64
import string
import struct
import decimal
import hmac
import numbers
import sys
from  itsdangerous import Serializer,BadSignature,BadTimeSignature
from itsdangerous.signer import HMACAlgorithm
from itsdangerous.signer import NoneAlgorithm


class _CompactJSON(object):
    """Wrapper around json module that strips whitespace."""

    @staticmethod
    def loads(payload):
        return json.loads(payload)

    @staticmethod
    def dumps(obj, **kwargs):
        kwargs.setdefault("ensure_ascii", False)
        kwargs.setdefault("separators", (",", ":"))
        return json.dumps(obj, **kwargs)

def want_bytes(s, encoding="utf-8", errors="strict"):
    if isinstance(s, text_type):
        s = s.encode(encoding, errors)
    return s


def base64_encode(string):
    """Base64 encode a string of bytes or text. The resulting bytes are
    safe to use in URLs.
    """
    string = want_bytes(string)
    return base64.urlsafe_b64encode(string).rstrip(b"=")


def base64_decode(string):
    """Base64 decode a URL-safe string of bytes or text. The result is
    bytes.
    """
    string = want_bytes(string, encoding="ascii", errors="ignore")
    string += b"=" * (-len(string) % 4)

    try:
        return base64.urlsafe_b64decode(string)
    except (TypeError, ValueError):
        raise BadData("Invalid base64-encoded data")


# The alphabet used by base64.urlsafe_*
_base64_alphabet = (string.ascii_letters + string.digits + "-_=").encode("ascii")

_int64_struct = struct.Struct(">Q")
_int_to_bytes = _int64_struct.pack
_bytes_to_int = _int64_struct.unpack


def int_to_bytes(num):
    return _int_to_bytes(num).lstrip(b"\x00")


def bytes_to_int(bytestr):
    return _bytes_to_int(bytestr.rjust(8, b"\x00"))[0]


PY2 = sys.version_info[0] == 2

if PY2:
    from itertools import izip

    #text_type = unicode  # noqa: 821
else:
    izip = zip
    text_type = str

number_types = (numbers.Real, decimal.Decimal)


def _constant_time_compare(val1, val2):
    """Return ``True`` if the two strings are equal, ``False``
    otherwise.
    The time taken is independent of the number of characters that
    match. Do not use this function for anything else than comparision
    with known length targets.
    This is should be implemented in C in order to get it completely
    right.
    This is an alias of :func:`hmac.compare_digest` on Python>=2.7,3.3.
    """
    len_eq = len(val1) == len(val2)
    if len_eq:
        result = 0
        left = val1
    else:
        result = 1
        left = val2
    for x, y in izip(bytearray(left), bytearray(val2)):
        result |= x ^ y
    return result == 0


# Starting with 2.7/3.3 the standard library has a c-implementation for
# constant time string compares.
constant_time_compare = getattr(hmac, "compare_digest", _constant_time_compare)




class BadData(Exception):
    """Raised if bad data of any sort was encountered. This is the base
    for all exceptions that itsdangerous defines.
    .. versionadded:: 0.15
    """

    message = None

    def __init__(self, message):
        super(BadData, self).__init__(self, message)
        self.message = message

    def __str__(self):
        return text_type(self.message)

    if PY2:
        __unicode__ = __str__

        def __str__(self):
            return self.__unicode__().encode("utf-8")


class BadSignature(BadData):
    """Raised if a signature does not match."""

    def __init__(self, message, payload=None):
        BadData.__init__(self, message)

        #: The payload that failed the signature test. In some
        #: situations you might still want to inspect this, even if
        #: you know it was tampered with.
        #:
        #: .. versionadded:: 0.14
        self.payload = payload


class BadTimeSignature(BadSignature):
    """Raised if a time-based signature is invalid. This is a subclass
    of :class:`BadSignature`.
    """

    def __init__(self, message, payload=None, date_signed=None):
        BadSignature.__init__(self, message, payload)

        #: If the signature expired this exposes the date of when the
        #: signature was created. This can be helpful in order to
        #: tell the user how long a link has been gone stale.
        #:
        #: .. versionadded:: 0.14
        self.date_signed = date_signed


class SignatureExpired(BadTimeSignature):
    """Raised if a signature timestamp is older than ``max_age``. This
    is a subclass of :exc:`BadTimeSignature`.
    """


class BadHeader(BadSignature):
    """Raised if a signed header is invalid in some form. This only
    happens for serializers that have a header that goes with the
    signature.
    .. versionadded:: 0.24
    """

    def __init__(self, message, payload=None, header=None, original_error=None):
        BadSignature.__init__(self, message, payload)

        #: If the header is actually available but just malformed it
        #: might be stored here.
        self.header = header

        #: If available, the error that indicates why the payload was
        #: not valid. This might be ``None``.
        self.original_error = original_error


class BadPayload(BadData):
    """Raised if a payload is invalid. This could happen if the payload
    is loaded despite an invalid signature, or if there is a mismatch
    between the serializer and deserializer. The original exception
    that occurred during loading is stored on as :attr:`original_error`.
    .. versionadded:: 0.15
    """

    def __init__(self, message, original_error=None):
        BadData.__init__(self, message)

        #: If available, the error that indicates why the payload was
        #: not valid. This might be ``None``.
        self.original_error = original_error

class JSONWebSignatureSerializer(Serializer):
    """This serializer implements JSON Web Signature (JWS) support. Only
    supports the JWS Compact Serialization.
    """

    jws_algorithms = {
        "HS256": HMACAlgorithm(hashlib.sha256),
        "HS384": HMACAlgorithm(hashlib.sha384),
        "HS512": HMACAlgorithm(hashlib.sha512),
        "none": NoneAlgorithm(),
    }

    #: The default algorithm to use for signature generation
    default_algorithm = "HS512"

    default_serializer = _CompactJSON

    def __init__(
        self,
        secret_key,
        salt=None,
        serializer=None,
        serializer_kwargs=None,
        signer=None,
        signer_kwargs=None,
        algorithm_name=None,
    ):
        Serializer.__init__(
            self,
            secret_key=secret_key,
            salt=salt,
            serializer=serializer,
            serializer_kwargs=serializer_kwargs,
            signer=signer,
            signer_kwargs=signer_kwargs,
        )
        if algorithm_name is None:
            algorithm_name = self.default_algorithm
        self.algorithm_name = algorithm_name
        self.algorithm = self.make_algorithm(algorithm_name)

    def load_payload(self, payload, serializer=None, return_header=False):
        payload = want_bytes(payload)
        if b"." not in payload:
            raise BadPayload('No "." found in value')
        base64d_header, base64d_payload = payload.split(b".", 1)
        try:
            json_header = base64_decode(base64d_header)
        except Exception as e:
            raise BadHeader(
                "Could not base64 decode the header because of an exception",
                original_error=e,
            )
        try:
            json_payload = base64_decode(base64d_payload)
        except Exception as e:
            raise BadPayload(
                "Could not base64 decode the payload because of an exception",
                original_error=e,
            )
        try:
            header = Serializer.load_payload(self, json_header, serializer=json)
        except BadData as e:
            raise BadHeader(
                "Could not unserialize header because it was malformed",
                original_error=e,
            )
        if not isinstance(header, dict):
            raise BadHeader("Header payload is not a JSON object", header=header)
        payload = Serializer.load_payload(self, json_payload, serializer=serializer)
        if return_header:
            return payload, header
        return payload

    def dump_payload(self, header, obj):
        base64d_header = base64_encode(
            self.serializer.dumps(header, **self.serializer_kwargs)
        )
        base64d_payload = base64_encode(
            self.serializer.dumps(obj, **self.serializer_kwargs)
        )
        return base64d_header + b"." + base64d_payload

    def make_algorithm(self, algorithm_name):
        try:
            return self.jws_algorithms[algorithm_name]
        except KeyError:
            raise NotImplementedError("Algorithm not supported")

    def make_signer(self, salt=None, algorithm=None):
        if salt is None:
            salt = self.salt
        key_derivation = "none" if salt is None else None
        if algorithm is None:
            algorithm = self.algorithm
        return self.signer(
            self.secret_key,
            salt=salt,
            sep=".",
            key_derivation=key_derivation,
            algorithm=algorithm,
        )

    def make_header(self, header_fields):
        header = header_fields.copy() if header_fields else {}
        header["alg"] = self.algorithm_name
        return header

    def dumps(self, obj, salt=None, header_fields=None):
        """Like :meth:`.Serializer.dumps` but creates a JSON Web
        Signature. It also allows for specifying additional fields to be
        included in the JWS header.
        """
        header = self.make_header(header_fields)
        signer = self.make_signer(salt, self.algorithm)
        return signer.sign(self.dump_payload(header, obj))

    def loads(self, s, salt=None, return_header=False):
        """Reverse of :meth:`dumps`. If requested via ``return_header``
        it will return a tuple of payload and header.
        """
        payload, header = self.load_payload(
            self.make_signer(salt, self.algorithm).unsign(want_bytes(s)),
            return_header=True,
        )
        if header.get("alg") != self.algorithm_name:
            raise BadHeader("Algorithm mismatch", header=header, payload=payload)
        if return_header:
            return payload, header
        return payload

    def loads_unsafe(self, s, salt=None, return_header=False):
        kwargs = {"return_header": return_header}
        return self._loads_unsafe_impl(s, salt, kwargs, kwargs)


class TimedJSONWebSignatureSerializer(JSONWebSignatureSerializer):
    """Works like the regular :class:`JSONWebSignatureSerializer` but
    also records the time of the signing and can be used to expire
    signatures.
    JWS currently does not specify this behavior but it mentions a
    possible extension like this in the spec. Expiry date is encoded
    into the header similar to what's specified in `draft-ietf-oauth
    -json-web-token <http://self-issued.info/docs/draft-ietf-oauth-json
    -web-token.html#expDef>`_.
    """

    DEFAULT_EXPIRES_IN = 3600

    def __init__(self, secret_key, expires_in=None, **kwargs):
        JSONWebSignatureSerializer.__init__(self, secret_key, **kwargs)
        if expires_in is None:
            expires_in = self.DEFAULT_EXPIRES_IN
        self.expires_in = expires_in

    def make_header(self, header_fields):
        header = JSONWebSignatureSerializer.make_header(self, header_fields)
        iat = self.now()
        exp = iat + self.expires_in
        header["iat"] = iat
        header["exp"] = exp
        return header

    def loads(self, s, salt=None, return_header=False):
        payload, header = JSONWebSignatureSerializer.loads(
            self, s, salt, return_header=True
        )

        if "exp" not in header:
            raise BadSignature("Missing expiry date", payload=payload)

        int_date_error = BadHeader("Expiry date is not an IntDate", payload=payload)
        try:
            header["exp"] = int(header["exp"])
        except ValueError:
            raise int_date_error
        if header["exp"] < 0:
            raise int_date_error

        if header["exp"] < self.now():
            raise SignatureExpired(
                "Signature expired",
                payload=payload,
                date_signed=self.get_issue_date(header),
            )

        if return_header:
            return payload, header
        return payload

    def get_issue_date(self, header):
        rv = header.get("iat")

        return datetime.utcfromtimestamp(int(rv))

    def now(self):
        return int(time.time())
