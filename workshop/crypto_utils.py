from cryptography.fernet import Fernet
import os

KEY_FILE = "secret.key"

def generate_key():
    """
    Génère une nouvelle clé et la sauvegarde dans un fichier.
    À lancer une seule fois au début du projet.
    """
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    return key

def load_key():
    """
    Charge la clé depuis le fichier (ou en génère une nouvelle si absent).
    """
    if not os.path.exists(KEY_FILE):
        return generate_key()
    with open(KEY_FILE, "rb") as f:
        return f.read()

def encrypt_message(message: str, key: bytes) -> bytes:
    """
    Chiffre un message texte et retourne le token chiffré (bytes).
    """
    cipher = Fernet(key)
    return cipher.encrypt(message.encode())

def decrypt_message(token: bytes, key: bytes) -> str:
    """
    Déchiffre un token (bytes) et retourne le texte original (str).
    """
    cipher = Fernet(key)
    return cipher.decrypt(token).decode()