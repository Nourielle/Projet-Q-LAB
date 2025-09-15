import sounddevice as sd, numpy as np, librosa
from joblib import load
from recorder import record_seconds

FS = 16000
N_MFCC = 13
DUR = 1.0        # on analyse des fenêtres de 1 seconde
THRESH = 0.70    # seuil de détection (augmente si trop sensible)

scaler = load("scaler.pkl")
clf = load("clf.pkl")

def extract_vec(sig):
    mfcc = librosa.feature.mfcc(y=sig, sr=FS, n_mfcc=N_MFCC)
    return np.concatenate([mfcc.mean(axis=1), mfcc.std(axis=1)])

print("🎧 Écoute en cours... (dis ton mot)")
while True:
    # enregistre 1 seconde
    audio = sd.rec(int(DUR*FS), samplerate=FS, channels=1, dtype='int16')
    sd.wait()
    # normalise en float [-1,1]
    sig = audio.flatten().astype(np.float32)/32768.0

    feat = extract_vec(sig)
    feat_s = scaler.transform([feat])
    proba = clf.predict_proba(feat_s)[0,1]
    print(f"Proba mot: {proba:.2f}", end="\r")

    if proba >= THRESH:
        print("\n🚨 Mot détecté → enregistrement 10s")
        record_seconds(10)
