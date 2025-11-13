import hashlib
import bcrypt


def _prepare_password(password: str) -> bytes:
    """
    Pre-hash password with SHA256 to avoid bcrypt's 72-byte limitation.
    This is a security best practice that:
    1. Removes bcrypt's 72-byte password limit
    2. Protects against null byte attacks
    3. Provides consistent input length to bcrypt
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest().encode("utf-8")


def bcrypt_pwd(password: str) -> str:
    """
    Hash password using SHA256 + bcrypt for maximum security.
    Returns the hash as a string for database storage.
    """
    prepared_password = _prepare_password(password)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(prepared_password, salt)
    return hashed.decode("utf-8")


def verify_pwd(hashed: str, normal: str) -> bool:
    """
    Verify password against hashed password.
    Args:
        hashed: The stored password hash (from database)
        normal: The plaintext password to verify
    Returns:
        True if password matches, False otherwise
    """
    prepared_password = _prepare_password(normal)
    return bcrypt.checkpw(prepared_password, hashed.encode("utf-8"))
