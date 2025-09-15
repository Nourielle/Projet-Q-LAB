import os, time
import sounddevice as sd
import wavio

FS = 16000
DUR = 1.0  # 1 seconde

def record_one(outpath):
    print("🎤 Parle...")
    audio = sd.rec(int(DUR*FS), samplerate=FS, channels=1, dtype='int16')
    sd.wait()
    wavio.write(outpath, audio, FS, sampwidth=2)
    print("✅ Enregistré :", outpath)

if __name__ == "__main__":
    os.makedirs("data/keyword", exist_ok=True)
    os.makedirs("data/other", exist_ok=True)

    # ENREGISTRE LE MOT-CLÉ (ex: "note")
    for i in range(20):
        input(f"[KEYWORD] Entrée puis dis le mot #{i+1}")
        record_one(f"data/keyword/kw_{i:02d}.wav")
        time.sleep(0.3)

    # ENREGISTRE SANS LE MOT (paroles normales/bruit)
    for i in range(20):
        input(f"[OTHER] Entrée puis parle SANS le mot #{i+1}")
        record_one(f"data/other/oth_{i:02d}.wav")
        time.sleep(0.3)
