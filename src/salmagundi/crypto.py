"""Crypto module.

.. versionadded:: 0.5.0
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

_SALT_SIZE = 16
_KEY_SIZE = 32
_IV_SIZE = 16
_MAC_SIZE = 32
_ITERATIONS = 100000
_VERSION_1 = b'\x80'


class DecryptError(Exception):
    """Raised if data could not be decrypted."""


def _check_bytes(name, value):
    if not isinstance(value, bytes):
        raise TypeError('%r must be bytes' % name)


def _keys(password, salt, backend):
    key = PBKDF2HMAC(SHA256(), length=_KEY_SIZE,
                     salt=salt, iterations=_ITERATIONS,
                     backend=backend).derive(password)
    return key[:_KEY_SIZE // 2], key[_KEY_SIZE // 2:]


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
    _check_bytes('password', password)
    _check_bytes('data', data)
    backend = default_backend()
    salt = os.urandom(_SALT_SIZE)
    enc_key, sig_key = _keys(password, salt, backend)
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
    _check_bytes('password', password)
    _check_bytes('data', data)
    if not data.startswith(_VERSION_1):
        raise DecryptError('unknown version')
    backend = default_backend()
    salt = data[len(_VERSION_1):len(_VERSION_1) + _SALT_SIZE]
    enc_key, sig_key = _keys(password, salt, backend)
    h = HMAC(sig_key, SHA256(), backend)
    h.update(data[:-_MAC_SIZE])
    try:
        h.verify(data[-_MAC_SIZE:])
    except InvalidSignature:
        raise DecryptError('signature could not be verified') from None
    pos = len(_VERSION_1) + _SALT_SIZE + _IV_SIZE
    iv = data[len(_VERSION_1) + _SALT_SIZE:pos]
    decryptor = Cipher(AES(enc_key), CBC(iv), backend).decryptor()
    try:
        padded_plaintext = (decryptor.update(data[pos:-_MAC_SIZE]) +
                            decryptor.finalize())
        unpadder = PKCS7(AES.block_size).unpadder()
        return unpadder.update(padded_plaintext) + unpadder.finalize()
    except ValueError:
        raise DecryptError('data could not be decrypted') from None
