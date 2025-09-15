import time
import sounddevice as sd
import wavio 

def record_seconds(duration=10, fs=16000, ch=1, prefix="hotword"):
    print(f"🎬 REC {duration}s…")
    audio = sd.rec(int(duration*fs), samplerate=fs, channels=ch, dtype='int16')
    sd.wait()
    fname = f"{prefix}_{time.strftime('%Y%m%d_%H%M%S')}.wav"
    wavio.write(fname, audio, fs, sampwidth=2)
    print(f"✅ Sauvé: {fname}")
    return fname

if __name__ == "__main__":
    record_seconds(5)
