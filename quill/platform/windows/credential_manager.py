from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from dataclasses import dataclass

_IS_WINDOWS = sys.platform == "win32"
_CRED_TYPE_GENERIC = 1
_CRED_PERSIST_LOCAL_MACHINE = 2


@dataclass(frozen=True, slots=True)
class StoredCredential:
    target_name: str
    user_name: str
    secret: str


if _IS_WINDOWS:
    _LPBYTE = ctypes.POINTER(ctypes.c_ubyte)

    class _FILETIME(ctypes.Structure):
        _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]

    class _CREDENTIALW(ctypes.Structure):
        _fields_ = [
            ("Flags", wintypes.DWORD),
            ("Type", wintypes.DWORD),
            ("TargetName", wintypes.LPWSTR),
            ("Comment", wintypes.LPWSTR),
            ("LastWritten", _FILETIME),
            ("CredentialBlobSize", wintypes.DWORD),
            ("CredentialBlob", _LPBYTE),
            ("Persist", wintypes.DWORD),
            ("AttributeCount", wintypes.DWORD),
            ("Attributes", ctypes.c_void_p),
            ("TargetAlias", wintypes.LPWSTR),
            ("UserName", wintypes.LPWSTR),
        ]

    _PCREDENTIALW = ctypes.POINTER(_CREDENTIALW)
    _advapi32 = ctypes.windll.advapi32
    _cred_free = _advapi32.CredFree
    _cred_free.argtypes = [ctypes.c_void_p]
    _cred_free.restype = None

    _cred_write = _advapi32.CredWriteW
    _cred_write.argtypes = [_PCREDENTIALW, wintypes.DWORD]
    _cred_write.restype = wintypes.BOOL

    _cred_read = _advapi32.CredReadW
    _cred_read.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(_PCREDENTIALW),
    ]
    _cred_read.restype = wintypes.BOOL

    _cred_delete = _advapi32.CredDeleteW
    _cred_delete.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    _cred_delete.restype = wintypes.BOOL


def credential_manager_available() -> bool:
    return _IS_WINDOWS


def load_generic_credential(target_name: str) -> StoredCredential | None:
    _require_windows()
    credential_ptr = _PCREDENTIALW()
    ok = _cred_read(target_name, _CRED_TYPE_GENERIC, 0, ctypes.byref(credential_ptr))
    if not ok:
        return None
    try:
        credential = credential_ptr.contents
        blob_size = int(credential.CredentialBlobSize)
        if blob_size <= 0:
            return StoredCredential(
                target_name=target_name,
                user_name=str(credential.UserName or ""),
                secret="",
            )
        blob = ctypes.string_at(credential.CredentialBlob, blob_size)
        return StoredCredential(
            target_name=str(credential.TargetName or target_name),
            user_name=str(credential.UserName or ""),
            secret=blob.decode("utf-8"),
        )
    finally:
        _cred_free(credential_ptr)


def save_generic_credential(
    target_name: str,
    secret: str,
    *,
    user_name: str = "quill-user",
) -> None:
    _require_windows()
    encoded = secret.encode("utf-8")
    blob = ctypes.create_string_buffer(encoded)
    credential = _CREDENTIALW()
    credential.Flags = 0
    credential.Type = _CRED_TYPE_GENERIC
    credential.TargetName = target_name
    credential.Comment = "QUILL secure secret"
    credential.CredentialBlobSize = len(encoded)
    credential.CredentialBlob = ctypes.cast(blob, _LPBYTE)
    credential.Persist = _CRED_PERSIST_LOCAL_MACHINE
    credential.AttributeCount = 0
    credential.Attributes = None
    credential.TargetAlias = None
    credential.UserName = user_name
    ok = _cred_write(ctypes.byref(credential), 0)
    if not ok:
        raise OSError(ctypes.GetLastError(), "CredWriteW failed")


def delete_generic_credential(target_name: str) -> bool:
    _require_windows()
    ok = _cred_delete(target_name, _CRED_TYPE_GENERIC, 0)
    return bool(ok)


def _require_windows() -> None:
    if not _IS_WINDOWS:
        raise RuntimeError("Windows Credential Manager is unavailable on this platform.")
