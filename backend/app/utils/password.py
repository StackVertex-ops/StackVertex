"""Password Utility Functions.

Funktionen zur Generierung sicherer Passwörter.
"""

import secrets
import string


def generate_secure_password(length: int = 16) -> str:
    """Generiert ein sicheres, zufälliges Passwort.

    Das Passwort enthält:
    - Kleinbuchstaben (a-z)
    - Großbuchstaben (A-Z)
    - Ziffern (0-9)
    - Sonderzeichen (!@#$%^&*()_+-=[]{}|;:,.<>?)

    Args:
        length: Länge des Passworts (min 8, default 16)

    Returns:
        Sicheres Passwort als String

    Raises:
        ValueError: Wenn length < 8
    """
    if length < 8:
        raise ValueError("Password length must be at least 8 characters")

    # Zeichensätze definieren
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    # Kombiniere alle Zeichen
    all_chars = lowercase + uppercase + digits + special

    # Stelle sicher, dass mindestens ein Zeichen von jedem Typ enthalten ist
    password_chars = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special),
    ]

    # Fülle den Rest mit zufälligen Zeichen auf
    password_chars.extend(secrets.choice(all_chars) for _ in range(length - 4))

    # Mische die Zeichen (Fisher-Yates shuffle via secrets)
    for i in range(len(password_chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        password_chars[i], password_chars[j] = password_chars[j], password_chars[i]

    return ''.join(password_chars)
