import os
import time
import struct
import wave
import threading
from datetime import datetime
import base64
import json
import subprocess

import pytz
import pvporcupine
from pvrecorder import PvRecorder
import keyboard

import cv2

from aes_utils import encrypt_bytes


# =========================
# ======  CONFIG  =========
# =========================

ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY") or "QGobPJP9Rzl7HaJdOhzn3Gs3RW7aWyLQVHtUh+NOfeI2+SffLM+eqQ=="  # remplace si besoin

# Wakewords:
AUDIO_START_WORD = "computer"
VIDEO_START_WORD = "jarvis"
STOP_WORD        = "alexa"

SENSITIVITY = 0.9

# Dossiers
AUDIO_SAVE_DIR = "enregistrements"
ENCRYPTED_SAVE_DIR = "enregistrements_chiffres"   
VIDEO_SAVE_DIR = "videos"

# Limites
MAX_AUDIO_RECORD_S = 300   # 5 minutes max pour l'audio

# Vid�o
VIDEO_FPS = 20
VIDEO_FOURCC = "mp4v"      # .mp4
VIDEO_RESOLUTION = None    # None = auto depuis la cam�ra (sinon tuple (1280, 720))
DRAW_GREEN_RECT = True     # garde le rectangle vert


# =========================
# ======  UTILS  ==========
# =========================

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def paris_now():
    return datetime.now(pytz.timezone("Europe/Paris"))

def ts_name(prefix: str, ext: str):
    return f"{prefix}_{paris_now().strftime('%Y-%m-%d_%H-%M-%S')}.{ext}"

def write_wav_int16(mono_int16_bytes: bytes, sample_rate: int, out_path: str):
    with wave.open(out_path, "wb") as wf:
        wf.setnchannels(1)           # mono
        wf.setsampwidth(2)           # int16 = 2 bytes
        wf.setframerate(sample_rate)
        wf.writeframes(mono_int16_bytes)

def run_transcription(wav_path: str):
    """
    Lance la transcription avec le script dispo.
    Essaie d'abord 'retranscription_emma.py', sinon 'retranscription.py'.
    """
    candidate = None
    if os.path.exists("retranscription_emma.py"):
        candidate = ["python", "retranscription_emma.py", wav_path]
    elif os.path.exists("retranscription.py"):
        candidate = ["python", "retranscription.py", wav_path]

    if candidate:
        try:
            subprocess.Popen(candidate)  # non bloquant
        except Exception as e:
            print(f"[WARN] Impossible de lancer la transcription : {e}")
    else:
        print("[INFO] Aucun script de transcription trouv� (retranscription_emma.py / retranscription.py).")

def encrypt_wav_to_json(wav_path: str, out_dir: str):
    """
    Lit un WAV, chiffre son contenu et �crit un JSON (nonce + ciphertext, base64 urlsafe).
    """
    ensure_dir(out_dir)
    with open(wav_path, "rb") as f:
        contenu_audio = f.read()

    nonce, ciphertext = encrypt_bytes(contenu_audio)
    bundle = {
        "nonce": base64.urlsafe_b64encode(nonce).decode("utf-8"),
        "ciphertext": base64.urlsafe_b64encode(ciphertext).decode("utf-8")
    }
    name_only = os.path.basename(wav_path)
    out_path = os.path.join(out_dir, name_only + ".aes.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2)
    return out_path


# =========================
# ===  VIDEO RECORDER  ====
# =========================

class VideoRecorder:
    def __init__(self, save_dir=VIDEO_SAVE_DIR, fps=VIDEO_FPS, fourcc=VIDEO_FOURCC,
                 resolution=VIDEO_RESOLUTION, draw_green_rect=DRAW_GREEN_RECT):
        self.save_dir = save_dir
        self.fps = fps
        self.fourcc = fourcc
        self.resolution = resolution
        self.draw_green_rect = draw_green_rect

        self._stop_evt = threading.Event()
        self._thread = None
        self._writer = None
        self._cap = None
        self._outfile = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return  # d�j� en cours

        ensure_dir(self.save_dir)
        filename = os.path.join(self.save_dir, ts_name("video", "mp4"))
        self._outfile = filename

        self._stop_evt.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print(f"[VIDEO] Enregistrement d�marr� ? {filename}")

    def stop(self):
        if not self._thread:
            return
        self._stop_evt.set()
        self._thread.join(timeout=5.0)
        self._thread = None
        print("[VIDEO] Enregistrement arr�t�.")

    def _run(self):
        self._cap = cv2.VideoCapture(0)
        if not self._cap.isOpened():
            print("[VIDEO][ERROR] Impossible d'ouvrir la cam�ra.")
            return

        # R�solution
        if self.resolution:
            w, h = self.resolution
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        else:
            w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Writer
        fourcc = cv2.VideoWriter_fourcc(*self.fourcc)
        self._writer = cv2.VideoWriter(self._outfile, fourcc, self.fps, (w, h))

        rect = (int(0.05 * w), int(0.05 * h), int(0.9 * w), int(0.9 * h))  # x, y, w, h

        while not self._stop_evt.is_set():
            ret, frame = self._cap.read()
            if not ret:
                break

            if self.draw_green_rect:
                x, y, ww, hh = rect
                cv2.rectangle(frame, (x, y), (x + ww, y + hh), (0, 255, 0), 2)

            self._writer.write(frame)

        try:
            if self._writer:
                self._writer.release()
        except Exception:
            pass
        try:
            if self._cap:
                self._cap.release()
        except Exception:
            pass


# =========================
# ======  FUSION  =========
# =========================

def main():
    ensure_dir(AUDIO_SAVE_DIR)
    ensure_dir(ENCRYPTED_SAVE_DIR)
    ensure_dir(VIDEO_SAVE_DIR)

    # Porcupine avec 3 mots-cl�s (audio start / video start / stop)
    try:
        porcupine = pvporcupine.create(
            access_key=ACCESS_KEY,
            keywords=[AUDIO_START_WORD, VIDEO_START_WORD, STOP_WORD],
            sensitivities=[SENSITIVITY, SENSITIVITY, SENSITIVITY],
        )
    except pvporcupine.PorcupineActivationLimitError:
        print("[ERROR] Votre cl� Picovoice a atteint la limite d?activations. R�voquez des appareils ou g�n�rez une nouvelle cl�.")
        return
    except Exception as e:
        print(f"[ERROR] �chec d?initialisation Porcupine : {e}")
        return

    sample_rate = porcupine.sample_rate
    frame_length = porcupine.frame_length

    recorder = PvRecorder(frame_length=frame_length)
    recorder.start()

    video_rec = VideoRecorder()

    print(f"�coute en cours?\n"
          f"- Dis '{AUDIO_START_WORD}' pour d�marrer l'**audio**\n"
          f"- Dis '{VIDEO_START_WORD}' pour d�marrer la **vid�o**\n"
          f"- Dis '{STOP_WORD}' pour **arr�ter tout** (audio+vid�o)\n"
          f"- Appuie sur [ESPACE] pour quitter.\n")

    audio_recording = False
    audio_buffer = bytearray()
    audio_start_time = 0.0
    wav_temp_path = None  # dernier WAV non chiffr�

    try:
        while not keyboard.is_pressed("space"):
            pcm = recorder.read()  # list[int16]
            kw_idx = porcupine.process(pcm)  # -1 si rien

            # si on enregistre l'audio, accumule
            if audio_recording:
                audio_buffer.extend(struct.pack("h" * len(pcm), *pcm))
                elapsed = time.time() - audio_start_time
                if elapsed > MAX_AUDIO_RECORD_S:
                    # auto stop audio (mais on ne stoppe pas la vid�o si elle tourne)
                    audio_recording = False
                    filename = os.path.join(AUDIO_SAVE_DIR, ts_name("audio", "wav"))
                    write_wav_int16(bytes(audio_buffer), sample_rate, filename)
                    print(f"[AUDIO] Auto-stop apr�s {MAX_AUDIO_RECORD_S}s ? {filename}")

                    # chiffrement + transcription + suppression WAV
                    enc_json = encrypt_wav_to_json(filename, ENCRYPTED_SAVE_DIR)
                    print(f"[AUDIO] Audio chiffr� : {enc_json}")

                    run_transcription(filename)
                    try:
                        os.remove(filename)
                    except Exception:
                        pass
                    audio_buffer.clear()
                    wav_temp_path = None

            # Wakeword handling
            if kw_idx == 0:  # AUDIO_START_WORD
                if not audio_recording:
                    audio_recording = True
                    audio_buffer.clear()
                    audio_start_time = time.time()
                    print(f"[AUDIO] Mot-cl� '{AUDIO_START_WORD}' d�tect� ? d�marrage de l'enregistrement audio.")
                # sinon d�j� en cours

            elif kw_idx == 1:  # VIDEO_START_WORD
                # d�marre vid�o si pas d�j�
                if not (video_rec._thread and video_rec._thread.is_alive()):
                    video_rec.start()
                else:
                    print("[VIDEO] D�j� en cours.")

            elif kw_idx == 2:  # STOP_WORD
                any_running = audio_recording or (video_rec._thread and video_rec._thread.is_alive())
                if any_running:
                    print(f"[ALL] Mot-cl� '{STOP_WORD}' d�tect� ? arr�t des enregistrements.")
                # Stop audio si en cours
                if audio_recording:
                    audio_recording = False
                    filename = os.path.join(AUDIO_SAVE_DIR, ts_name("audio", "wav"))
                    write_wav_int16(bytes(audio_buffer), sample_rate, filename)
                    print(f"[AUDIO] Enregistrement sauvegard� : {filename}")

                    # chiffrement + transcription + suppression WAV
                    enc_json = encrypt_wav_to_json(filename, ENCRYPTED_SAVE_DIR)
                    print(f"[AUDIO] Audio chiffr� : {enc_json}")

                    run_transcription(filename)
                    try:
                        os.remove(filename)
                    except Exception:
                        pass
                    audio_buffer.clear()
                    wav_temp_path = None

                # Stop vid�o si en cours
                if video_rec._thread and video_rec._thread.is_alive():
                    video_rec.stop()

    except KeyboardInterrupt:
        print("\n[INFO] Arr�t manuel.")
    finally:
        try:
            recorder.stop()
            recorder.delete()
        except Exception:
            pass
        try:
            porcupine.delete()
        except Exception:
            pass

        # En cas de sortie alors que l'audio �tait en cours ? flush/sauvegarde
        if audio_recording and audio_buffer:
            filename = os.path.join(AUDIO_SAVE_DIR, ts_name("audio", "wav"))
            write_wav_int16(bytes(audio_buffer), sample_rate, filename)
            print(f"[AUDIO] Sauvegarde de secours : {filename}")
            enc_json = encrypt_wav_to_json(filename, ENCRYPTED_SAVE_DIR)
            print(f"[AUDIO] Audio chiffr� : {enc_json}")
            run_transcription(filename)
            try:
                os.remove(filename)
            except Exception:
                pass

        # En cas de sortie alors que la vid�o tournait ? stop
        if video_rec._thread and video_rec._thread.is_alive():
            video_rec.stop()


if __name__ == "__main__":
    main()
