import os

SAVE_FILE = "messages.enc"

def save_message(token: bytes):
    """Sauvegarde un message chiffré dans le fichier."""
    with open(SAVE_FILE, "ab") as f:
        f.write(token + b"\n")

def load_messages():
    """Charge tous les messages chiffrés depuis le fichier."""
    if not os.path.exists(SAVE_FILE):
        return []
    with open(SAVE_FILE, "rb") as f:
        return [line.strip() for line in f.readlines()]