import speech_recognition as sr
import os
import sys

def transcrire_audio(fichier_audio):
    recognizer = sr.Recognizer()

    with sr.AudioFile(fichier_audio) as source:
        audio_data = recognizer.record(source)

    try:
        # Utilisation du moteur Google Speech Recognition
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
    base, _ = os.path.splitext(fichier_audio)
    fichier_txt = base + "_retranscription.txt"

    with open(fichier_txt, "w", encoding="utf-8") as f:
        f.write(texte)

    print(f"💾 Transcription sauvegardée dans : {fichier_txt}")

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




