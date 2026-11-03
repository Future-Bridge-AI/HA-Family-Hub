"""Per-environment credential store for the seed tool.

Passwords are generated once per environment and reused forever, so resets keep the same
logins (the family member signs in with the same details after a reset). The file lives in the
gitignored secrets directory: the directory is mode 0700 and the file is written 0600.
"""
from __future__ import annotations

import json
import os
import re
import secrets
from typing import Any, Optional

ADMIN_USERNAME = "fhtools"


class CredentialStore:
    """Credentials for one environment, stored in ``credentials-<env>.json``."""

    def __init__(self, secrets_dir: str, env_key: str) -> None:
        self.secrets_dir = secrets_dir
        self.path = os.path.join(secrets_dir, "credentials-%s.json" % env_key)
        self._data: dict[str, Any] = {}
        self._loaded_text: Optional[str] = None
        self._load()

    def _load(self) -> None:
        try:
            with open(self.path, encoding="utf-8") as handle:
                text = handle.read()
        except FileNotFoundError:
            return
        self._loaded_text = text
        self._data = json.loads(text)

    def exists(self) -> bool:
        """True when an admin password was already generated for this environment."""
        return bool(self._data.get("admin", {}).get("password"))

    def admin(self) -> dict[str, str]:
        """Return ``{"username", "password"}`` for the tool's own admin, creating it once."""
        admin = self._data.get("admin")
        if not admin or not admin.get("password"):
            admin = {"username": ADMIN_USERNAME, "password": secrets.token_urlsafe(24)}
            self._data["admin"] = admin
            self.save()
        return dict(admin)

    def member(self, first_name: str) -> dict[str, str]:
        """Return credentials for a family member's account, creating them once."""
        members = self._data.setdefault("members", {})
        entry = members.get(first_name)
        if not entry or not entry.get("password"):
            username = re.sub(r"[^a-z0-9]+", "", first_name.lower()) or "member"
            entry = {"username": username, "password": secrets.token_urlsafe(24)}
            members[first_name] = entry
            self.save()
        return dict(entry)

    def save(self) -> None:
        """Write the file (0600, inside a 0700 directory); unchanged content is not rewritten."""
        text = json.dumps(self._data, indent=2, sort_keys=True) + "\n"
        if text == self._loaded_text:
            return
        os.makedirs(self.secrets_dir, mode=0o700, exist_ok=True)
        os.chmod(self.secrets_dir, 0o700)
        fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            os.fchmod(fd, 0o600)
            handle.write(text)
        self._loaded_text = text
