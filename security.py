"""Authentication, authorization, password hashing and encryption."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from config import (
    ENCRYPTION_KEY_FILE,
    LOCKOUT_MINUTES,
    LOGIN_MAX_ATTEMPTS,
    PASSWORD_MIN_LENGTH,
)
from database import DatabaseManager
from logger import get_logger


log = get_logger("security")

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "Haroun@123"
DEFAULT_ADMIN_FULL_NAME = "Haroun Administrator"


def now_utc() -> datetime:
    """Return the current UTC date and time."""
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class AuthResult:
    success: bool
    message: str
    user: dict[str, Any] | None = None


class PasswordManager:
    """Password validation, hashing and verification."""

    ITERATIONS = 240_000

    @staticmethod
    def validate_strength(password: str) -> None:
        if len(password) < PASSWORD_MIN_LENGTH:
            raise ValueError(
                f"Password must contain at least "
                f"{PASSWORD_MIN_LENGTH} characters"
            )

        if not any(character.isupper() for character in password):
            raise ValueError(
                "Password requires at least one uppercase letter"
            )

        if not any(character.islower() for character in password):
            raise ValueError(
                "Password requires at least one lowercase letter"
            )

        if not any(character.isdigit() for character in password):
            raise ValueError(
                "Password requires at least one number"
            )

    @classmethod
    def hash_password(
        cls,
        password: str,
        salt: bytes | None = None,
    ) -> tuple[str, str]:
        cls.validate_strength(password)

        password_salt = salt or os.urandom(16)

        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            password_salt,
            cls.ITERATIONS,
        )

        password_hash = base64.b64encode(digest).decode("utf-8")
        salt_text = base64.b64encode(password_salt).decode("utf-8")

        return password_hash, salt_text

    @classmethod
    def verify_password(
        cls,
        password: str,
        expected_hash: str,
        salt_b64: str,
    ) -> bool:
        try:
            salt = base64.b64decode(salt_b64)

            digest = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt,
                cls.ITERATIONS,
            )

            actual_hash = base64.b64encode(digest).decode("utf-8")

            return hmac.compare_digest(
                actual_hash,
                expected_hash,
            )

        except Exception:
            return False


class SecurityManager:
    """Manage users, login, permissions and security auditing."""

    def __init__(self, database: DatabaseManager):
        self.db = database

    def bootstrap_admin(self) -> None:
        """
        Create the default administrator only when it does not exist.

        This function is safe to run whenever the application starts.
        """

        existing_admin = self.db.get_user_by_username(
            DEFAULT_ADMIN_USERNAME
        )

        if existing_admin is not None:
            log.info(
                "Default administrator already exists: %s",
                DEFAULT_ADMIN_USERNAME,
            )
            return

        password_hash, salt = PasswordManager.hash_password(
            DEFAULT_ADMIN_PASSWORD
        )

        try:
            user_id = self.db.create_user(
                DEFAULT_ADMIN_USERNAME,
                password_hash,
                salt,
                DEFAULT_ADMIN_FULL_NAME,
                "admin",
                "ar",
            )

            self.audit(
                event_type="BOOTSTRAP_ADMIN",
                message=(
                    f"Default administrator created: "
                    f"{DEFAULT_ADMIN_USERNAME}"
                ),
                severity="WARNING",
                user_id=user_id,
            )

            log.info(
                "Default administrator created successfully"
            )

        except Exception:
            # حماية إضافية إذا حاولت نسختان من البرنامج
            # إنشاء الحساب في نفس اللحظة.
            existing_admin = self.db.get_user_by_username(
                DEFAULT_ADMIN_USERNAME
            )

            if existing_admin is not None:
                log.info(
                    "Administrator already created by another process"
                )
                return

            raise

    def create_user(
        self,
        username: str,
        password: str,
        full_name: str,
        role: str = "user",
        preferred_language: str = "ar",
    ) -> int:
        username = username.strip().lower()
        role = role.strip().lower()

        if not username:
            raise ValueError("Username is required")

        if any(character.isspace() for character in username):
            raise ValueError(
                "Username cannot contain spaces"
            )

        if role not in {"admin", "user", "viewer"}:
            raise ValueError(
                "Role must be admin, user, or viewer"
            )

        if self.db.get_user_by_username(username):
            raise ValueError(
                "Username already exists"
            )

        password_hash, salt = PasswordManager.hash_password(
            password
        )

        user_id = self.db.create_user(
            username,
            password_hash,
            salt,
            full_name.strip(),
            role,
            preferred_language,
        )

        self.audit(
            event_type="CREATE_USER",
            message=f"Created user: {username}",
            user_id=user_id,
        )

        return user_id

    def authenticate(
        self,
        username: str,
        password: str,
    ) -> AuthResult:
        username = username.strip().lower()

        user = self.db.get_user_by_username(username)

        if not user:
            self.audit(
                event_type="LOGIN_FAILED",
                message=f"Unknown username: {username}",
                severity="WARNING",
            )

            return AuthResult(
                success=False,
                message="Invalid username or password",
            )

        user_id = int(user["id"])

        if not bool(user["is_active"]):
            return AuthResult(
                success=False,
                message="Account is disabled",
            )

        locked_until = user.get("locked_until")

        if locked_until:
            try:
                locked_time = datetime.fromisoformat(
                    locked_until
                )

                if locked_time.tzinfo is None:
                    locked_time = locked_time.replace(
                        tzinfo=timezone.utc
                    )

                if locked_time > now_utc():
                    return AuthResult(
                        success=False,
                        message=(
                            "Account locked until "
                            f"{locked_time.isoformat(timespec='minutes')}"
                        ),
                    )

            except (TypeError, ValueError):
                log.warning(
                    "Invalid locked_until value for user %s",
                    username,
                )

        password_is_correct = (
            PasswordManager.verify_password(
                password,
                user["password_hash"],
                user["salt"],
            )
        )

        if not password_is_correct:
            attempts = int(
                user.get("failed_attempts") or 0
            ) + 1

            lock_time: str | None = None

            if attempts >= LOGIN_MAX_ATTEMPTS:
                lock_time = (
                    now_utc()
                    + timedelta(minutes=LOCKOUT_MINUTES)
                ).isoformat(timespec="seconds")

            self.db.update_login_state(
                user_id,
                attempts,
                lock_time,
                False,
            )

            self.audit(
                event_type="LOGIN_FAILED",
                message=f"Wrong password for {username}",
                severity="WARNING",
                user_id=user_id,
            )

            if lock_time:
                return AuthResult(
                    success=False,
                    message=(
                        f"Account locked for "
                        f"{LOCKOUT_MINUTES} minutes"
                    ),
                )

            return AuthResult(
                success=False,
                message="Invalid username or password",
            )

        self.db.update_login_state(
            user_id,
            success=True,
        )

        clean_user = {
            key: value
            for key, value in user.items()
            if key not in {
                "password_hash",
                "salt",
            }
        }

        self.audit(
            event_type="LOGIN_SUCCESS",
            message=f"User {username} logged in",
            user_id=user_id,
        )

        return AuthResult(
            success=True,
            message="Login successful",
            user=clean_user,
        )

    def authenticate_face(
        self,
        user_id: int,
        matched_person: dict[str, Any] | None,
    ) -> AuthResult:
        user = self.db.get_user(user_id)

        if not user or not matched_person:
            return AuthResult(
                success=False,
                message="Face not recognized",
            )

        linked_user_id = int(
            matched_person.get("linked_user_id") or 0
        )

        if linked_user_id != int(user_id):
            self.audit(
                event_type="FACE_UNLOCK_FAILED",
                message=(
                    f"Face did not match user "
                    f"{user['username']}"
                ),
                severity="WARNING",
                user_id=user_id,
            )

            return AuthResult(
                success=False,
                message=(
                    "Face does not belong to this account"
                ),
            )

        clean_user = {
            key: value
            for key, value in user.items()
            if key not in {
                "password_hash",
                "salt",
            }
        }

        self.db.update_login_state(
            user_id,
            success=True,
        )

        self.audit(
            event_type="FACE_UNLOCK_SUCCESS",
            message=(
                f"Face unlock for {user['username']}"
            ),
            user_id=user_id,
        )

        return AuthResult(
            success=True,
            message="Face unlock successful",
            user=clean_user,
        )

    def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
    ) -> None:
        user = self.db.get_user(user_id)

        if not user:
            raise ValueError("User was not found")

        old_password_is_correct = (
            PasswordManager.verify_password(
                old_password,
                user["password_hash"],
                user["salt"],
            )
        )

        if not old_password_is_correct:
            raise ValueError(
                "Current password is incorrect"
            )

        password_hash, salt = (
            PasswordManager.hash_password(
                new_password
            )
        )

        self.db.update_password(
            user_id,
            password_hash,
            salt,
        )

        self.audit(
            event_type="PASSWORD_CHANGED",
            message="Password changed",
            user_id=user_id,
        )

    def require_role(
        self,
        user: dict[str, Any] | None,
        *roles: str,
    ) -> None:
        if not user:
            raise PermissionError(
                "Authentication is required"
            )

        if user.get("role") not in roles:
            raise PermissionError(
                "You do not have permission for this action"
            )

    def audit(
        self,
        event_type: str,
        message: str,
        severity: str = "INFO",
        user_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        log.info(
            "%s | %s",
            event_type,
            message,
        )

        return self.db.add_security_log(
            event_type,
            message,
            severity,
            user_id,
            metadata,
        )


class DataProtector:
    """Encrypt and decrypt sensitive text."""

    def __init__(
        self,
        key_file: Path = ENCRYPTION_KEY_FILE,
    ):
        self.key_file = key_file
        self._fernet = None

        try:
            from cryptography.fernet import Fernet

            key_file.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            if not key_file.exists():
                key_file.write_bytes(
                    Fernet.generate_key()
                )

            encryption_key = (
                key_file.read_bytes().strip()
            )

            self._fernet = Fernet(
                encryption_key
            )

        except Exception as exc:
            log.warning(
                "Encryption unavailable: %s",
                exc,
            )

    @property
    def available(self) -> bool:
        return self._fernet is not None

    def encrypt_text(self, text: str) -> str:
        if not self._fernet:
            raise RuntimeError(
                "Install cryptography to enable encryption"
            )

        encrypted = self._fernet.encrypt(
            text.encode("utf-8")
        )

        return encrypted.decode("utf-8")

    def decrypt_text(self, token: str) -> str:
        if not self._fernet:
            raise RuntimeError(
                "Install cryptography to enable encryption"
            )

        decrypted = self._fernet.decrypt(
            token.encode("utf-8")
        )

        return decrypted.decode("utf-8")