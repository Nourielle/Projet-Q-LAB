import speech_recognition as sr
import os
import sys

def transcrire_audio(fichier_audio):
    recognizer = sr.Recognizer()

    with sr.AudioFile(fichier_audio) as source:
        audio_data = recognizer.record(source)

    try:
        texte = recognizer.recognize_google(audio_data, language="fr-FR")
        print(f"✅ Transcription réussie :\n{texte}")
        return texte

    except sr.UnknownValueError:
        print("❌ Impossible de comprendre l'audio.")
        return None
    except sr.RequestError as e:
        print(f"❌ Erreur de connexion à l'API Google : {e}")
        return None

def sauvegarder_transcription(texte, fichier_audio):
    # Crée le dossier "retranscriptions" s'il n'existe pas
    dossier_retranscriptions = "retranscriptions"
    os.makedirs(dossier_retranscriptions, exist_ok=True)

    # Nom de base du fichier audio sans le chemin
    nom_audio = os.path.basename(fichier_audio)
    base, _ = os.path.splitext(nom_audio)

    # Crée le nom du fichier texte
    nom_fichier_txt = base + "_retranscription.txt"

    # Chemin complet du fichier texte dans le bon dossier
    chemin_txt = os.path.join(dossier_retranscriptions, nom_fichier_txt)

    # Sauvegarde
    with open(chemin_txt, "w", encoding="utf-8") as f:
        f.write(texte)

    print(f"💾 Transcription sauvegardée dans : {chemin_txt}")

def main():
    if len(sys.argv) < 2:
        print("Utilisation : python retranscription.py chemin/vers/fichier.wav")
        sys.exit(1)

    fichier_audio = sys.argv[1]

    if not os.path.isfile(fichier_audio):
        print("❌ Fichier audio introuvable :", fichier_audio)
        sys.exit(1)

    texte = transcrire_audio(fichier_audio)

    if texte:
        sauvegarder_transcription(texte, fichier_audio)

if __name__ == "__main__":
    main()
