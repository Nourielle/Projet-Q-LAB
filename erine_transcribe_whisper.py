import os, time, struct, wave
from datetime import datetime
import numpy as np
import pvporcupine
from pvrecorder import PvRecorder
import pytz

# --- chiffrement AES-GCM ---
from aes_utils import encrypt_bytes
import base64, json

# --- transcription Whisper ---
from erine_transcribe_whisper import transcribe_wav  # faster-whisper offline

# ===== PARAMÈTRES =====
ACCESS_KEY    = "8MXQw8p2RpVti4zKvxfaEqtunUR4FEFPm+71hVgY5WyeEygRPLz67w=="   # <-- mets TA vraie clé
KEYWORDS      = ["computer", "terminator"]     # index 0 = start, index 1 = stop
SENSITIVITY   = 0.9                      # 0..1 (plus haut = + sensible)
DEVICE_INDEX  = -1                       # -1 auto; sinon un index précis
SAVE_DIR      = "enregistrements"
SHOW_VOLUME   = True                     # afficher le volume live
COOLDOWN_SEC  = 1.0                      # petite pause après stop
MAX_RECORD_S  = 300                      # sécurité: stop auto à 5 min
# ======================

def ensure_dir(p): os.makedirs(p, exist_ok=True)
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

def encrypt_file_to_json_aes(input_path: str) -> str:
    """Chiffre un fichier (bytes) avec AES-GCM → écrit <fichier>.aes.json et retourne ce chemin."""
    with open(input_path, "rb") as f:
        plain = f.read()
    nonce, cipher = encrypt_bytes(plain)
    out_path = input_path + ".aes.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "alg": "AES-256-GCM",
            "nonce": base64.urlsafe_b64encode(nonce).decode(),
            "ciphertext": base64.urlsafe_b64encode(cipher).decode()
        }, f, indent=2)
    return out_path

def main():
    ensure_dir(SAVE_DIR)

    porcu = pvporcupine.create(
        access_key=ACCESS_KEY,
        keywords=KEYWORDS,
        sensitivities=[SENSITIVITY]*len(KEYWORDS)
    )
    sr = porcu.sample_rate
    fl = porcu.frame_length

    rec = PvRecorder(device_index=DEVICE_INDEX, frame_length=fl)
    print(f"🎧 Écoute: {KEYWORDS} | sens={SENSITIVITY} | device={DEVICE_INDEX} | sr={sr} | frame={fl}")
    rec.start()

    recording = False
    buf = bytearray()
    rec_start_ts = 0.0

    try:
        while True:
            # lire un frame int16 (longueur exacte = fl)
            pcm = rec.read()  # list[int16]
            if SHOW_VOLUME:
                vol = np.sqrt(np.mean(np.array(pcm, dtype=np.float32)**2))/32768.0
                print(f"Volume: {vol:.3f}    ", end="\r")

            # Pendant l'enregistrement, on ajoute chaque frame au buffer
            if recording:
                # packer la liste d'int16 en bytes pour WAV
                buf.extend(struct.pack("h"*len(pcm), *pcm))

            # Détection du mot-clé
            result = porcu.process(pcm)   # -1 = rien, sinon index du mot

            # START si "computer" (index 0)
            if not recording and result == 0:
                recording = True
                buf.clear()
                rec_start_ts = time.time()
                print(f"\n▶️  Start REC (mot: {KEYWORDS[0]})")

            # STOP si "terminator" (index 1)
            if recording and result == 1:
                # 1) écrire le wav
                fname = os.path.join(SAVE_DIR, paris_filename())
                write_wav_int16(bytes(buf), sr, fname)
                dur = time.time() - rec_start_ts
                print(f"⏹️  Stop REC (mot: {KEYWORDS[1]}) | durée ~{dur:.1f}s")
                print(f"✅ Sauvé: {fname}")

                # 2) Transcription Whisper
                txt = transcribe_wav(fname)
                base, _ = os.path.splitext(fname)
                txt_path = base + ".txt"
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(txt)
                print(f"📝 Transcription: {txt if txt else '(vide)'}")
                print(f"✅ Transcription sauvegardée → {txt_path}")

                # 3) 🔐 CHIFFRAGE AES-GCM (audio + transcription)
                enc_audio = encrypt_file_to_json_aes(fname)
                print(f"🔐 Audio chiffré → {enc_audio}")
                enc_txt = encrypt_file_to_json_aes(txt_path)
                print(f"🔐 Transcription chiffrée → {enc_txt}")

                # 4) (option) supprimer les fichiers en clair
                # os.remove(fname)
                # os.remove(txt_path)
                # print("🧹 Fichiers en clair supprimés")

                # reset état + petit cooldown
                recording = False
                buf.clear()
                time.sleep(COOLDOWN_SEC)

            # Sécurité: stop auto si dépasse temps max
            if recording and (time.time() - rec_start_ts) > MAX_RECORD_S:
                fname = os.path.join(SAVE_DIR, paris_filename())
                write_wav_int16(bytes(buf), sr, fname)
                print(f"\n⏹️  Stop auto après {MAX_RECORD_S}s → {fname}")

                # transcription
                txt = transcribe_wav(fname)
                base, _ = os.path.splitext(fname)
                txt_path = base + ".txt"
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(txt)
                print(f"📝 Transcription (auto): {txt if txt else '(vide)'}")

                # chiffrement AES
                enc_audio = encrypt_file_to_json_aes(fname)
                print(f"🔐 Audio chiffré (auto) → {enc_audio}")
                enc_txt = encrypt_file_to_json_aes(txt_path)
                print(f"🔐 Transcription chiffrée (auto) → {enc_txt}")

                # (option) suppression clair
                # os.remove(fname); os.remove(txt_path)

                recording = False
                buf.clear()
                time.sleep(COOLDOWN_SEC)

    except KeyboardInterrupt:
        print("\n👋 Bye")
    finally:
        try: rec.stop()
        except: pass
        rec.delete()
        porcu.delete()

if __name__ == "__main__":
    main()
