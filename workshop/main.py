from speech_recognition import listen_for_keyword, transcribe_once
from crypto_utils import load_key, encrypt_message, decrypt_message
from storage import save_message, load_messages
from caméra_utils import record_video, take_photo

ACTIVATION_WORD = "merci"   # Active caméra + chiffrement
PHOTO_WORD = "photo"        # Prendre une photo
UNLOCK_CODE = "3"           # Déchiffre les messages (saisi au clavier)
STOP_WORD = "stop"  # Mot pour arrêter l'enregistrement

def main():
    print("=== Simulation lunettes intelligentes ===")
    key = load_key() 

    while True:
        print("Micro actif. Dites un mot de passe :")
        text = transcribe_once()

        if ACTIVATION_WORD in text:
            print("Activation vidéo et chiffrement !")
            record_video(filename="capture.avi", duration=3600)
            while True:
                print("Dites votre message, tapez le chiffre pour déchiffrer ou dites 'stop' pour arrêter.")
                msg = transcribe_once()
                if STOP_WORD in msg:
                    print("⏹️ Arrêt de l'enregistrement et sortie du mode chiffrement.")
                    break
                user_input = input("Pour déchiffrer, tapez le chiffre : ")
                if user_input == UNLOCK_CODE:
                    print("🔓 Déchiffrement des messages :")
                    for token in load_messages():
                        try:
                            print("-", decrypt_message(token, key))
                        except Exception as e:
                            print("Erreur de déchiffrement :", e)
                    print("Fin du mode chiffrement.\n")
                    break
                else:
                    token = encrypt_message(msg, key)
                    save_message(token)
                    print("Message chiffré et enregistré.")

        elif PHOTO_WORD in text:
            print("Prise de photo !")
            take_photo(filename="photo.jpg")

if __name__ == "__main__":
    main()
