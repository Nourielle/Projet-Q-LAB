import os, base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM # type: ignore
from dotenv import load_dotenv # type: ignore
load_dotenv()

load_dotenv()
AES_KEY = os.getenv("AES_KEY")
if not AES_KEY:
    raise RuntimeError("AES_KEY manquante dans .env")

# convertir la clé base64 en bytes
key = base64.urlsafe_b64decode(AES_KEY)

def encrypt_bytes(plaintext: bytes, aad: bytes = None) -> tuple:
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # recommandé pour AES-GCM
    ciphertext = aesgcm.encrypt(nonce, plaintext, aad)
    return nonce, ciphertext

def decrypt_bytes(nonce: bytes, ciphertext: bytes, aad: bytes = None) -> bytes:
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, aad)
