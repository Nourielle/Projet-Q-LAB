import queue, sounddevice as sd, json
from vosk import Model, KaldiRecognizer

# Charger modèle français Vosk (à adapter selon ton dossier modèle)
model = Model("models/vosk-model-small-fr-0.22")
samplerate = 16000
q = queue.Queue()

def audio_callback(indata, frames, time, status):
    """
    Callback appelé à chaque bloc audio reçu.
    Met les données audio dans la file q.
    """
    q.put(bytes(indata))

def listen_for_keyword(secret="merci"):
    """
    Attend que le mot secret soit prononcé.
    Retourne True dès qu'il est détecté.
    """
    rec = KaldiRecognizer(model, samplerate)
    with sd.RawInputStream(samplerate=samplerate, blocksize=8000,
                           dtype='int16', channels=1, callback=audio_callback):
        print("🎤 En attente du mot secret...")
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                text = res.get("text", "").lower()
                if secret in text:
                    print("✅ Mot secret détecté !")
                    return True

def transcribe_once():
    """
    Transcrit une phrase et retourne le texte.
    """
    rec = KaldiRecognizer(model, samplerate)
    with sd.RawInputStream(samplerate=samplerate, blocksize=8000,
                           dtype='int16', channels=1, callback=audio_callback):
        print("🎤 Parle maintenant...")
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                text = res.get("text", "").lower()
                return text
