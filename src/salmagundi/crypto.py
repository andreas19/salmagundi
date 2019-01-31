"""Cryptography module.

.. versionadded:: 0.5.0

This module uses ``AES`` in ``CBC`` mode with a 128-bit key and ``PKCS7``
padding for encryption. The authentication is done with ``HMAC`` using
``SHA256``. To derive a key from a password ``PBKDF2HMAC`` is used with
``SHA256``, a 128-bit key, a salt of equal size and 100.000 iterations.
The ``IV`` for ``CBC``, the keys, and the  the salt are created
cryptographically secure with :func:`os.urandom`.
"""

import os

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

_SALT_SIZE = 16
_KEY_SIZE = 32
_IV_SIZE = 16
_MAC_SIZE = 32
_ITERATIONS = 100000
_VERSION_1 = b'\x8a'


class DecryptError(Exception):
    """Raised if data could not be decrypted."""


def _keys(password, salt, backend):
    key = PBKDF2HMAC(SHA256(), length=_KEY_SIZE,
                     salt=salt, iterations=_ITERATIONS,
                     backend=backend).derive(password)
    return key[:_KEY_SIZE // 2], key[_KEY_SIZE // 2:]


def _verify(data, sig_key, backend):
    h = HMAC(sig_key, SHA256(), backend)
    h.update(data[:-_MAC_SIZE])
    try:
        h.verify(data[-_MAC_SIZE:])
        return True
    except InvalidSignature:
        return False


def _encrypt(enc_key, sig_key, salt, data, backend):
    iv = os.urandom(_IV_SIZE)
    padder = PKCS7(AES.block_size).padder()
    padded_data = padder.update(data) + padder.finalize()
    encryptor = Cipher(AES(enc_key), CBC(iv), backend).encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    all_data = b''.join((_VERSION_1, salt, iv, ciphertext))
    h = HMAC(sig_key, SHA256(), backend)
    h.update(all_data)
    hmac = h.finalize()
    return all_data + hmac


def _decrypt(enc_key, sig_key, salt, data, backend):
    if not _verify(data, sig_key, backend):
        raise DecryptError('signature could not be verified') from None
    pos = len(_VERSION_1) + len(salt) + _IV_SIZE
    iv = data[len(_VERSION_1) + len(salt):pos]
    decryptor = Cipher(AES(enc_key), CBC(iv), backend).decryptor()
    try:
        padded_plaintext = (decryptor.update(data[pos:-_MAC_SIZE]) +
                            decryptor.finalize())
        unpadder = PKCS7(AES.block_size).unpadder()
        return unpadder.update(padded_plaintext) + unpadder.finalize()
    except ValueError:
        raise DecryptError('data could not be decrypted') from None


def create_secret_key():
    """Create a secret key.

    It can be used with the ``*_with_key()`` functions:

    - :func:`encrypt_with_key`
    - :func:`decrypt_with_key`
    - :func:`verify_with_key`

    :return: secret key
    :rytpe: bytes
    """
    return os.urandom(_KEY_SIZE)


def encrypt_with_password(password, data):
    """Encrypt data using a password.

    The data will be encrypted with a key derived from the
    password and signed.

    :param bytes password: the password
    :param bytes data: the data to encrypt
    :return: encrypted data
    :rtype: bytes
    :raises TypeError: if ``password`` or ``data`` are not ``bytes``
    """
    check_type(password, bytes, 'password')
    check_type(data, bytes, 'data')
    backend = default_backend()
    salt = os.urandom(_SALT_SIZE)
    enc_key, sig_key = _keys(password, salt, backend)
    return _encrypt(enc_key, sig_key, salt, data, backend)


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
    if not data.startswith(_VERSION_1):
        raise DecryptError('unknown version')
    backend = default_backend()
    salt = data[len(_VERSION_1):len(_VERSION_1) + _SALT_SIZE]
    enc_key, sig_key = _keys(password, salt, backend)
    return _decrypt(enc_key, sig_key, salt, data, backend)


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
    backend = default_backend()
    salt = data[len(_VERSION_1):len(_VERSION_1) + _SALT_SIZE]
    _, sig_key = _keys(password, salt, backend)
    return _verify(data, sig_key, backend)


def _check_key_size(key):
    if len(key) != _KEY_SIZE:
        raise ValueError('incorrect secret key size')


def encrypt_with_key(key, data):
    """Encrypt data using a secret key.

    :param bytes key: the secret key
    :param bytes data: the data to encrypt
    :return: encrypted data
    :rtype: bytes
    :raises TypeError: if ``key`` or ``data`` are not ``bytes``
    :raises ValueError: if size of ``key`` is not correct
    """
    check_type(key, bytes, 'secret key')
    check_type(data, bytes, 'data')
    _check_key_size(key)
    enc_key, sig_key = key[:_KEY_SIZE // 2], key[_KEY_SIZE // 2:]
    return _encrypt(enc_key, sig_key, b'', data, default_backend())


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
    _check_key_size(key)
    enc_key, sig_key = key[:_KEY_SIZE // 2], key[_KEY_SIZE // 2:]
    return _decrypt(enc_key, sig_key, b'', data, default_backend())


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
    _check_key_size(key)
    return _verify(data, key[_KEY_SIZE // 2:], default_backend())
