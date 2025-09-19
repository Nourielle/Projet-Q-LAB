import sys, json, base64
from aes_utils import decrypt_bytes

# décrypte le fichier donné (écrire le chemin et le nom du fichier entre "", 
# idem pour le nom sous lequel enregistrer le fichier) 

if len(sys.argv) != 3:
    print("Usage: python aes_decrypt.py <fichier.aes.json> <sortie>")
    sys.exit(1)

src, dst = sys.argv[1], sys.argv[2]
with open(src, "r", encoding="utf-8") as f:
    bundle = json.load(f)

nonce = base64.urlsafe_b64decode(bundle["nonce"])
ciphertext = base64.urlsafe_b64decode(bundle["ciphertext"])

plain = decrypt_bytes(nonce, ciphertext)
with open(dst, "wb") as f:
    f.write(plain)

print(f"✅ Déchiffré → {dst}")
