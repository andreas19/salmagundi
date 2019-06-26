"""Cryptography module.

.. versionadded:: 0.5.0

This module provides data encryption and decryption in four versions.

All versions use AES in CBC mode, PKCS#7 padding, and
HMAC-SHA256 as message authentication code.

Key lengths in bits:

=======  ===  ====
Version  AES  HMAC
=======  ===  ====
   1     128   128
   2     128   256
   3     192   256
   4     256   256
=======  ===  ====

To derive a key from a password PBKDF2HMAC-SHA256 with a 128 bit salt
and 100,000 iterations is used.

The initialization vector for ``CBC``, the keys, and the salt are
created with :func:`os.urandom`.
"""

import os
from enum import Enum

from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import CBC
from cryptography.hazmat.primitives.hmac import HMAC
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.padding import PKCS7

from .utils import check_type

_MAC_HASH = _KDF_HASH = SHA256()
_IV_LEN = AES.block_size // 8  # 16 bytes
_MAC_LEN = _MAC_HASH.digest_size  # 32 bytes
_SALT_LEN = 16  # bytes
_ITERATIONS = 100000
_VERSION_LEN = 1  # byte

_backend = default_backend()


class Version(Enum):
    """Version enum.

    .. versionadded:: 0.8.0
    """

    V1 = (b'\x8a', 16, 16)        #: version 1
    V2 = (b'\x8b', 16, _MAC_LEN)  #: version 2
    V3 = (b'\x8c', 24, _MAC_LEN)  #: version 3
    V4 = (b'\x8d', 32, _MAC_LEN)  #: version 4

    def __new__(cls, version_byte, enc_key_len, mac_key_len):
        """Create new Version."""
        obj = object.__new__(cls)
        obj._value_ = version_byte
        obj._enc_key_len = enc_key_len  # bytes
        obj._mac_key_len = mac_key_len  # bytes
        return obj

    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)


class DecryptError(Exception):
    """Raised if data could not be decrypted."""


def _verify(data, mac_key):
    h = HMAC(mac_key, _MAC_HASH, _backend)
    h.update(data[:-_MAC_LEN])
    try:
        h.verify(data[-_MAC_LEN:])
        return True
    except InvalidSignature:
        return False


def _encrypt(enc_key, mac_key, salt, data, version):
    iv = os.urandom(_IV_LEN)
    padder = PKCS7(AES.block_size).padder()
    padded_data = padder.update(data) + padder.finalize()
    encryptor = Cipher(AES(enc_key), CBC(iv), _backend).encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    all_data = b''.join((version.value, salt, iv, ciphertext))
    h = HMAC(mac_key, _MAC_HASH, _backend)
    h.update(all_data)
    hmac = h.finalize()
    return all_data + hmac


def _decrypt(enc_key, mac_key, salt, data):
    if not _verify(data, mac_key):
        raise DecryptError('signature could not be verified') from None
    pos = _VERSION_LEN + len(salt) + _IV_LEN
    iv = data[_VERSION_LEN + len(salt):pos]
    decryptor = Cipher(AES(enc_key), CBC(iv), _backend).decryptor()
    try:
        padded_plaintext = (decryptor.update(data[pos:-_MAC_LEN]) +
                            decryptor.finalize())
        unpadder = PKCS7(AES.block_size).unpadder()
        return unpadder.update(padded_plaintext) + unpadder.finalize()
    except ValueError:
        raise DecryptError('data could not be decrypted') from None


def _check_data(data, with_salt):
    if not len(data):
        return None, None
    try:
        version = Version(data[:_VERSION_LEN])
    except ValueError:
        return None, None
    min_len = _VERSION_LEN + 2 * _IV_LEN + _MAC_LEN
    if with_salt:
        min_len += _SALT_LEN
        salt_len = _SALT_LEN
    else:
        salt_len = 0
    if len(data) < min_len:
        return None, None
    return version, data[_VERSION_LEN:_VERSION_LEN + salt_len]


def create_secret_key(*, version=Version.V1):
    """Create a secret key.

    It can be used with the ``*_with_key()`` functions:

    - :func:`encrypt_with_key`
    - :func:`decrypt_with_key`
    - :func:`verify_with_key`

    :return: secret key
    :rytpe: bytes

    .. versionchanged:: 0.8.0
       Add parameter ``version``
    """
    return os.urandom(version._enc_key_len + version._mac_key_len)


def _derive_keys(password, salt, version):
    key = PBKDF2HMAC(_KDF_HASH,
                     length=version._enc_key_len + version._mac_key_len,
                     salt=salt, iterations=_ITERATIONS,
                     backend=_backend).derive(password)
    return key[:version._enc_key_len], key[version._enc_key_len:]


def encrypt_with_password(password, data, *, version=Version.V1):
    """Encrypt data using a password.

    The data will be encrypted with a key derived from the
    password and signed.

    :param bytes password: the password
    :param bytes data: the data to encrypt
    :return: encrypted data
    :rtype: bytes
    :raises TypeError: if ``password`` or ``data`` are not ``bytes``

    .. versionchanged:: 0.8.0
       Add parameter ``version``
    """
    check_type(password, bytes, 'password')
    check_type(data, bytes, 'data')
    salt = os.urandom(_SALT_LEN)
    enc_key, mac_key = _derive_keys(password, salt, version)
    return _encrypt(enc_key, mac_key, salt, data, version)


def decrypt_with_password(password, data):
    """Decrypt data using a password.

    The data must have been encrypted with :func:`encrypt_with_password`.

    :param bytes password: the password
    :param bytes data: the encrypted data
    :return: decrypted data
    :rtype: bytes
    :raises TypeError: if ``password`` or ``data`` are not ``bytes``
    :raises DecryptError: if data could not be decrypted
    """
    check_type(password, bytes, 'password')
    check_type(data, bytes, 'data')
    version, salt = _check_data(data, True)
    if not version:
        raise DecryptError('unknown version or not enough data')
    enc_key, mac_key = _derive_keys(password, salt, version)
    return _decrypt(enc_key, mac_key, salt, data)


def verify_with_password(password, data):
    """Verify the encrypted data.

    This function verifies the authenticity and the integrity of the data
    with the key derived from the password. This is also done during decryption.

    The data must have been encrypted with :func:`encrypt_with_password`.

    :param bytes password: the password
    :param bytes data: the encrypted data
    :return: ``True`` if password, authenticity and integrity are okay
    :rtype: bool
    :raises TypeError: if ``password`` or ``data`` are not ``bytes``
    """
    check_type(password, bytes, 'password')
    check_type(data, bytes, 'data')
    version, salt = _check_data(data, True)
    if not version:
        return False
    _, mac_key = _derive_keys(password, salt, version)
    return _verify(data, mac_key)


def _check_key_size(key, version):
    if len(key) != version._enc_key_len + version._mac_key_len:
        raise ValueError('incorrect secret key size')


def encrypt_with_key(key, data, *, version=Version.V1):
    """Encrypt data using a secret key.

    :param bytes key: the secret key
    :param bytes data: the data to encrypt
    :return: encrypted data
    :rtype: bytes
    :raises TypeError: if ``key`` or ``data`` are not ``bytes``
    :raises ValueError: if size of ``key`` is not correct

    .. versionchanged:: 0.8.0
       Add parameter ``version``
    """
    check_type(key, bytes, 'secret key')
    check_type(data, bytes, 'data')
    _check_key_size(key, version)
    enc_key, mac_key = key[:version._enc_key_len], key[version._enc_key_len:]
    return _encrypt(enc_key, mac_key, b'', data, version)


def decrypt_with_key(key, data):
    """Decrypt data using a secret key.

    The data must have been encrypted with :func:`encrypt_with_key`.

    :param bytes key: the secret key
    :param bytes data: the encrypted data
    :return: decrypted data
    :rtype: bytes
    :raises TypeError: if ``key`` or ``data`` are not ``bytes``
    :raises ValueError: if size of ``key`` is not correct
    :raises DecryptError: if data could not be decrypted
    """
    check_type(key, bytes, 'secret key')
    check_type(data, bytes, 'data')
    version, salt = _check_data(data, False)
    if not version:
        raise DecryptError('unknown version or not enough data')
    _check_key_size(key, version)
    enc_key, mac_key = key[:version._enc_key_len], key[version._enc_key_len:]
    return _decrypt(enc_key, mac_key, salt, data)


def verify_with_key(key, data):
    """Verify the encrypted data.

    This function verifies the authenticity and the integrity of the data
    with the given key. This is also done during decryption.

    The data must have been encrypted with :func:`encrypt_with_key`.

    :param bytes key: the secret key
    :param bytes data: the encrypted data
    :return: ``True`` if secret key, authenticity and integrity are okay
    :rtype: bool
    :raises TypeError: if ``key`` or ``data`` are not ``bytes``
    :raises ValueError: if size of ``key`` is not correct
    """
    check_type(key, bytes, 'secret key')
    check_type(data, bytes, 'data')
    version, _ = _check_data(data, False)
    if not version:
        return False
    _check_key_size(key, version)
    return _verify(data, key[version._enc_key_len:])
