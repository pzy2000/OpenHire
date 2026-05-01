"""Workspace-scoped authentication helpers for the Admin surface."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from loguru import logger


ADMIN_SESSION_COOKIE = "openhire_admin_session"
ADMIN_CSRF_HEADER = "X-OpenHire-CSRF"
ADMIN_SESSION_DAYS = 7
PASSWORD_MIN_LENGTH = 8
USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,64}$")
PBKDF2_ITERATIONS = 260_000


class AuthError(ValueError):
    """Raised when an auth operation cannot be completed."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_iso(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(text: str) -> bytes:
    padded = text + "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _hash_password(password: str, *, salt: bytes | None = None) -> dict[str, Any]:
    resolved_salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        resolved_salt,
        PBKDF2_ITERATIONS,
    )
    return {
        "algorithm": "pbkdf2_sha256",
        "iterations": PBKDF2_ITERATIONS,
        "salt": _b64(resolved_salt),
        "hash": _b64(digest),
    }


def _verify_password(password: str, stored: dict[str, Any]) -> bool:
    try:
        iterations = int(stored.get("iterations") or 0)
        salt = _unb64(str(stored.get("salt") or ""))
        expected = _unb64(str(stored.get("hash") or ""))
    except Exception:
        return False
    if iterations <= 0 or not salt or not expected:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(digest, expected)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def csrf_token_for_session_token(token: str) -> str:
    """Derive a CSRF token from the opaque session token."""

    return hmac.new(
        token.encode("utf-8"),
        b"openhire-admin-csrf-v1",
        hashlib.sha256,
    ).hexdigest()


def validate_username(username: str) -> str:
    normalized = str(username or "").strip()
    if not USERNAME_RE.fullmatch(normalized):
        raise AuthError("Username must be 3-64 characters using letters, numbers, dots, underscores, or hyphens.")
    return normalized


def validate_password(password: str) -> str:
    normalized = str(password or "")
    if len(normalized) < PASSWORD_MIN_LENGTH:
        raise AuthError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters.")
    return normalized


def _public_user(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row.get("id") or ""),
        "username": str(row.get("username") or ""),
        "createdAt": str(row.get("created_at") or ""),
        "updatedAt": str(row.get("updated_at") or ""),
        "lastLoginAt": str(row.get("last_login_at") or ""),
    }


class AdminAuthStore:
    """Persist Admin users and sessions under ``workspace/openhire/users.json``."""

    def __init__(self, workspace: Path) -> None:
        self._dir = workspace / "openhire"
        self._file = self._dir / "users.json"

    @property
    def path(self) -> Path:
        return self._file

    def _default_state(self) -> dict[str, Any]:
        return {"version": 1, "users": {}, "sessions": {}}

    def load(self) -> dict[str, Any]:
        if not self._file.exists():
            return self._default_state()
        try:
            data = json.loads(self._file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load Admin auth store: {}", exc)
            return self._default_state()
        if not isinstance(data, dict):
            return self._default_state()
        users = data.get("users") if isinstance(data.get("users"), dict) else {}
        sessions = data.get("sessions") if isinstance(data.get("sessions"), dict) else {}
        return {
            "version": 1,
            "users": {str(key): value for key, value in users.items() if isinstance(value, dict)},
            "sessions": {str(key): value for key, value in sessions.items() if isinstance(value, dict)},
        }

    def save(self, data: dict[str, Any]) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        tmp = self._file.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self._file)

    def _load_pruned(self) -> dict[str, Any]:
        data = self.load()
        sessions = data.get("sessions", {})
        now = _now()
        pruned = {
            key: row
            for key, row in sessions.items()
            if (_parse_iso(row.get("expires_at")) or now) > now
        }
        if len(pruned) != len(sessions):
            data["sessions"] = pruned
            self.save(data)
        return data

    def has_users(self) -> bool:
        return bool(self.load().get("users"))

    def needs_bootstrap(self) -> bool:
        return not self.has_users()

    def list_users(self) -> list[dict[str, Any]]:
        users = self.load().get("users", {})
        return sorted(
            (_public_user(row) for row in users.values()),
            key=lambda item: item.get("createdAt") or "",
        )

    def create_user(self, username: str, password: str, *, bootstrap_only: bool = False) -> dict[str, Any]:
        normalized_username = validate_username(username)
        normalized_password = validate_password(password)
        data = self.load()
        users: dict[str, dict[str, Any]] = data["users"]
        if bootstrap_only and users:
            raise AuthError("Initial administrator has already been created.")
        wanted = normalized_username.casefold()
        if any(str(row.get("username") or "").casefold() == wanted for row in users.values()):
            raise AuthError("Username already exists.")
        now = _now_iso()
        user_id = secrets.token_urlsafe(12)
        users[user_id] = {
            "id": user_id,
            "username": normalized_username,
            "password": _hash_password(normalized_password),
            "created_at": now,
            "updated_at": now,
            "last_login_at": "",
        }
        self.save(data)
        return _public_user(users[user_id])

    def authenticate(self, username: str, password: str) -> dict[str, Any] | None:
        normalized_username = str(username or "").strip().casefold()
        data = self.load()
        users: dict[str, dict[str, Any]] = data["users"]
        for user_id, row in users.items():
            if str(row.get("username") or "").casefold() != normalized_username:
                continue
            stored_password = row.get("password") if isinstance(row.get("password"), dict) else {}
            if not _verify_password(str(password or ""), stored_password):
                return None
            row["last_login_at"] = _now_iso()
            row["updated_at"] = row.get("updated_at") or row["last_login_at"]
            users[user_id] = row
            self.save(data)
            return _public_user(row)
        return None

    def create_session(self, user_id: str, *, lifetime: timedelta | None = None) -> tuple[str, dict[str, Any]]:
        data = self._load_pruned()
        users: dict[str, dict[str, Any]] = data["users"]
        row = users.get(user_id)
        if row is None:
            raise AuthError("User not found.")
        token = secrets.token_urlsafe(32)
        issued_at = _now_iso()
        row["last_login_at"] = issued_at
        row["updated_at"] = row.get("updated_at") or issued_at
        users[user_id] = row
        expires_at = _now() + (lifetime or timedelta(days=ADMIN_SESSION_DAYS))
        data["sessions"][_token_hash(token)] = {
            "user_id": user_id,
            "created_at": issued_at,
            "expires_at": expires_at.isoformat(timespec="seconds").replace("+00:00", "Z"),
        }
        self.save(data)
        return token, _public_user(row)

    def session_for_token(self, token: str | None) -> dict[str, Any] | None:
        if not token:
            return None
        data = self._load_pruned()
        session = data.get("sessions", {}).get(_token_hash(str(token)))
        if not isinstance(session, dict):
            return None
        user_id = str(session.get("user_id") or "")
        user = data.get("users", {}).get(user_id)
        if not isinstance(user, dict):
            return None
        expires_at = _parse_iso(session.get("expires_at"))
        if expires_at is None or expires_at <= _now():
            return None
        return {
            "token": str(token),
            "csrfToken": csrf_token_for_session_token(str(token)),
            "expiresAt": expires_at.isoformat(timespec="seconds").replace("+00:00", "Z"),
            "user": _public_user(user),
        }

    def delete_session(self, token: str | None) -> None:
        if not token:
            return
        data = self.load()
        sessions = data.get("sessions", {})
        if sessions.pop(_token_hash(str(token)), None) is not None:
            data["sessions"] = sessions
            self.save(data)

    def delete_user(self, user_id: str, *, current_user_id: str) -> dict[str, Any]:
        normalized_id = str(user_id or "").strip()
        data = self.load()
        users: dict[str, dict[str, Any]] = data["users"]
        if normalized_id == current_user_id:
            raise AuthError("You cannot delete your own account.")
        if normalized_id not in users:
            raise KeyError(normalized_id)
        if len(users) <= 1:
            raise AuthError("Cannot delete the last administrator.")
        users.pop(normalized_id)
        data["sessions"] = {
            key: row
            for key, row in data.get("sessions", {}).items()
            if str(row.get("user_id") or "") != normalized_id
        }
        self.save(data)
        return {"deleted": True, "userId": normalized_id}
