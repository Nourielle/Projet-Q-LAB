import speech_recognition as sr
import os
import sys

from aes_utils import encrypt_bytes
import base64
import json


def transcrire_audio(fichier_audio):
    recognizer = sr.Recognizer()

    with sr.AudioFile(fichier_audio) as source:
        audio_data = recognizer.record(source)

    try:
        texte = recognizer.recognize_google(audio_data, language="fr-FR")
        print(f"Transcription réussie")
        return texte

    except sr.UnknownValueError:
        print("ERREUR : Impossible de comprendre l'audio.")
        return None
    except sr.RequestError as e:
        print(f"ERREUR : Connexion à l'API Google : {e}")
        return None


def sauvegarder_transcription(texte, fichier_audio):
    dossier_retranscriptions = "retranscriptions"
    os.makedirs(dossier_retranscriptions, exist_ok=True)

    nom_audio = os.path.basename(fichier_audio)
    base, _ = os.path.splitext(nom_audio)
    nom_fichier_txt = base + "_retranscription.txt"
    chemin_txt = os.path.join(dossier_retranscriptions, nom_fichier_txt)

    with open(chemin_txt, "w", encoding="utf-8") as f:
        f.write(texte)

    print(f"Transcription sauvegardée dans : {chemin_txt}")
    return chemin_txt


def chiffrer_transcription(texte, fichier_audio):
    dossier_chiffre = "retranscriptions chiffrées"
    os.makedirs(dossier_chiffre, exist_ok=True)

    nom_audio = os.path.basename(fichier_audio)
    base, _ = os.path.splitext(nom_audio)
    nom_fichier_chiffre = base + "_retranscription.aes.json"
    chemin_chiffre = os.path.join(dossier_chiffre, nom_fichier_chiffre)

    nonce, ciphertext = encrypt_bytes(texte.encode("utf-8"))
    bundle = {
        "nonce": base64.urlsafe_b64encode(nonce).decode("utf-8"),
        "ciphertext": base64.urlsafe_b64encode(ciphertext).decode("utf-8")
    }

    with open(chemin_chiffre, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2)

    print(f"Transcription chiffrée sauvegardée dans : {chemin_chiffre}")


def main():
    if len(sys.argv) < 2:
        print("Utilisation : python retranscription.py chemin/vers/fichier.wav")
        sys.exit(1)

    fichier_audio = sys.argv[1]

    if not os.path.isfile(fichier_audio):
        print("ERREUR : Fichier audio introuvable :", fichier_audio)
        sys.exit(1)

    texte = transcrire_audio(fichier_audio)

    if texte:
        #sauvegarder_transcription(texte, fichier_audio)
        chiffrer_transcription(texte, fichier_audio)


if __name__ == "__main__":
    main()
