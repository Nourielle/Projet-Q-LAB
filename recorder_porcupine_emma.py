# coding: utf-8 
import os
import time
import struct
import wave
from datetime import datetime
import pytz

import pvporcupine
from pvrecorder import PvRecorder

import keyboard
import subprocess

# 


# Constantes
ACCESS_KEY = "uBpKa3Nmidsl97vIjlL5yui5zDr2beiZ01v3tjeuDe6ZsMPV636ttg=="  # Ta clé Porcupine
KEYWORDS = ["computer", "terminator"]
SENSITIVITY = 0.9
SAVE_DIR = "enregistrements"
MAX_RECORD_S = 300  # 5 minutes max


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def paris_now():
    return datetime.now(pytz.timezone("Europe/Paris"))


def paris_filename():
    return paris_now().strftime("%Y-%m-%d_%H-%M-%S") + ".wav"


def write_wav_int16(mono_int16_bytes: bytes, sample_rate: int, out_path: str):
    with wave.open(out_path, "wb") as wf:
        wf.setnchannels(1)           # mono
        wf.setsampwidth(2)           # int16 = 2 bytes
        wf.setframerate(sample_rate)
        wf.writeframes(mono_int16_bytes)


def detect_keyword():
    ensure_dir(SAVE_DIR)

    porcupine = pvporcupine.create(
        access_key=ACCESS_KEY,
        keywords=KEYWORDS,
        sensitivities=[SENSITIVITY]*len(KEYWORDS)
    )

    sample_rate = porcupine.sample_rate
    frame_length = porcupine.frame_length

    recorder = PvRecorder(frame_length=frame_length)
    recorder.start()

    print(f"Écoute en cours... Dis '{KEYWORDS[0]}' pour démarrer, '{KEYWORDS[1]}' pour arrêter.")
    print("Appuie sur [ESPACE] pour quitter.\n")

    recording = False
    audio_buffer = bytearray()
    record_start_time = 0

    try:
        while not keyboard.is_pressed("space"):
            pcm = recorder.read()  # list[int16]

            keyword_index = porcupine.process(pcm)  # -1 if nothing detected

            if recording:
                # Ajouter l'audio au buffer
                audio_buffer.extend(struct.pack("h"*len(pcm), *pcm))

                # Vérifier durée max
                elapsed = time.time() - record_start_time
                if elapsed > MAX_RECORD_S:
                    print(f"\n⏹️ Enregistrement arrêté automatiquement après {MAX_RECORD_S} secondes.")
                    # Sauvegarder fichier
                    filename = os.path.join(SAVE_DIR, paris_filename())
                    write_wav_int16(bytes(audio_buffer), sample_rate, filename)
                    print(f"✅ Enregistrement sauvegardé : {filename}")

                    # Lancer la transcription
                    subprocess.run(["python", "retranscription.py", filename])

                    recording = False
                    audio_buffer.clear()
                    print("Retour à l'écoute...\n")
                    continue

            if not recording and keyword_index == 0:
                # Démarrer enregistrement
                recording = True
                audio_buffer.clear()
                record_start_time = time.time()
                print("▶️ Mot-clé détecté : démarrage de l'enregistrement...")

            elif recording and keyword_index == 1:
                # Arrêter enregistrement
                recording = False
                filename = os.path.join(SAVE_DIR, paris_filename())
                write_wav_int16(bytes(audio_buffer), sample_rate, filename)
                print(f"⏹️ Mot-clé détecté : arrêt de l'enregistrement.")
                print(f"✅ Enregistrement sauvegardé : {filename}")

                # Lancer la transcription
                subprocess.run(["python", "retranscription.py", filename])

                audio_buffer.clear()
                print("Retour à l'écoute...\n")

    except KeyboardInterrupt:
        print("\nProgramme arrêté manuellement.")

    finally:
        recorder.stop()
        recorder.delete()
        porcupine.delete()


if __name__ == "__main__":
    detect_keyword()
