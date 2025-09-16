import time, os
import numpy as np
import pvporcupine
from pvrecorder import PvRecorder
import sounddevice as sd
import wavio
from datetime import datetime
import pytz

# ===== PARAMÈTRES =====
ACCESS_KEY   = "8MXQw8p2RpVti4zKvxfaEqtunUR4FEFPm+71hVgY5WyeEygRPLz67w=="  # <-- remplace par TA clé
KEYWORDS     = ["computer"]           # ou "computer", "bumblebee"
SENSITIVITY  = 0.9                     # 0..1 (plus grand = plus sensible)
DEVICE_INDEX = -1                      # -1 = auto; ou un index précis
RECORD_SEC   = 10                      # durée d'enregistrement après mot
COOLDOWN_SEC = 5.0                     # temps mini entre deux triggers
SAVE_DIR     = "enregistrements"
SHOW_VOLUME  = True                    # voir le volume en temps réel
# ======================

def ensure_dir(p): os.makedirs(p, exist_ok=True)

def paris_filename():
    tz = pytz.timezone("Europe/Paris")
    return datetime.now(tz).strftime("%Y-%m-%d_%H-%M-%S") + ".wav"

def record_after_trigger(seconds=RECORD_SEC, fs=16000):
    print(f"🎬 Enregistrement {seconds}s…")
    audio = sd.rec(int(seconds*fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    fname = os.path.join(SAVE_DIR, paris_filename())
    wavio.write(fname, audio, fs, sampwidth=2)
    print(f"✅ Sauvé: {fname}")

def main():
    ensure_dir(SAVE_DIR)

    porcu = pvporcupine.create(
        access_key=ACCESS_KEY,
        keywords=KEYWORDS,
        sensitivities=[SENSITIVITY]*len(KEYWORDS)
    )

    rec = PvRecorder(device_index=DEVICE_INDEX, frame_length=porcu.frame_length)
    print(f"🎧 Écoute: {KEYWORDS} | sens={SENSITIVITY} | device={DEVICE_INDEX} | frame={porcu.frame_length}")
    rec.start()

    last_fire = 0.0
    try:
        while True:
            pcm = rec.read()  # int16 de taille frame_length
            if SHOW_VOLUME:
                vol = np.sqrt(np.mean(np.array(pcm, dtype=np.float32)**2))/32768.0
                print(f"Volume: {vol:.3f}    ", end="\r")

            result = porcu.process(pcm)
            if result >= 0:
                now = time.time()
                if now - last_fire >= COOLDOWN_SEC:
                    word = KEYWORDS[result]
                    print(f"\n🚨 Mot détecté: {word}")
                    record_after_trigger()
                    last_fire = now
    except KeyboardInterrupt:
        print("\n👋 Bye")
    finally:
        try: rec.stop()
        except: pass
        rec.delete()
        porcu.delete()

if __name__ == "__main__":
    main()
