"""Password hashing.

Only the hash is ever stored or returned; the plaintext password is used once,
in memory, and then discarded.
"""

import bcrypt

# bcrypt truncates anything past 72 bytes, so the schema caps the password
# length rather than letting a longer password be silently shortened.
MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    """Hash a plaintext password with a per-password random salt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
