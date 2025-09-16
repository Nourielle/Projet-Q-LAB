import pvporcupine
import pyaudio
import wave
import struct
from datetime import datetime
import pytz 
import os 
import subprocess



def record_audio(filename, duration=10, sample_rate=16000):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=sample_rate,
                    input=True,
                    frames_per_buffer=512)

    print(f"Enregistrement de {duration} secondes en cours...")
    frames = []

    for _ in range(0, int(sample_rate / 512 * duration)):
        data = stream.read(512)
        frames.append(data)

    print("Enregistrement terminé.")
    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(filename, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()


def detect_keyword():
    # Initialisation de Porcupine avec le mot-clé intégré "picovoice"
    porcupine = pvporcupine.create(
        access_key="uBpKa3Nmidsl97vIjlL5yui5zDr2beiZ01v3tjeuDe6ZsMPV636ttg==",
        keywords=["computer"]
    )
    pa = pyaudio.PyAudio()

    stream = pa.open(rate=porcupine.sample_rate,
                     channels=1,
                     format=pyaudio.paInt16,
                     input=True,
                     frames_per_buffer=porcupine.frame_length)

    print("Écoute en cours... Dis le mot-clé pour déclencher l'enregistrement.") 

    try:
        detected = False
        # Écoute jusqu’à détection
        while not detected:
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                print("Mot-clé détecté !")
                detected = True

    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        porcupine.delete()

    # Lancer l'enregistrement une fois le mot-clé détecté
    # === Création du dossier "enregistrements" s'il n'existe pas ===
    dossier = "enregistrements"
    os.makedirs(dossier, exist_ok=True)

    # Obtenir la date/heure actuelle à Paris 
    paris_tz = pytz.timezone("Europe/Paris")
    now = datetime.now(paris_tz)

    # Créer le nom de fichier
    nom_fichier = now.strftime("%Y-%m-%d_%H-%M-%S") + ".wav"

    # Chemin complet : enregistrements/2025-09-16_14-03-22.wav
    chemin_complet = os.path.join(dossier, nom_fichier)

    # Lancer l'enregistrement 
    record_audio(chemin_complet, duration=10)

    # Lancer la transcription automatiquement 
    subprocess.run(["python", "retranscription.py", chemin_complet])


if __name__ == "__main__":
    detect_keyword()
