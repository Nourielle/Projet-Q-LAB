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

<<<<<<< HEAD
ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY") or "uBpKa3Nmidsl97vIjlL5yui5zDr2beiZ01v3tjeuDe6ZsMPV636ttg=="  # remplace si besoin
=======
ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY") or "QGobPJP9Rzl7HaJdOhzn3Gs3RW7aWyLQVHtUh+NOfeI2+SffLM+eqQ=="  # remplace si besoin
>>>>>>> 27780bb (Ajout/modif du recorder_porcupine_emma.py)

# Wakewords:
AUDIO_START_WORD = "computer"
VIDEO_START_WORD = "jarvis"
STOP_WORD        = "alexa"

SENSITIVITY = 0.9

# Dossiers
<<<<<<< HEAD
ENCRYPTED_SAVE_DIR = "enregistrements_chiffres"   
=======
AUDIO_SAVE_DIR = "enregistrements"
ENCRYPTED_SAVE_DIR = "enregistrements_chiffres"   
VIDEO_SAVE_DIR = "videos"
>>>>>>> 27780bb (Ajout/modif du recorder_porcupine_emma.py)

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
    Lance la transcription de manière bloquante en appelant retranscription.py.
    retranscription.py chiffre lui-même le texte, donc ici on attend qu'il finisse
    puis on peut supprimer le WAV en clair.
    """
    script = None
    if os.path.exists("retranscription_emma.py"):
        script = ["python", "retranscription_emma.py", wav_path]
    elif os.path.exists("retranscription.py"):
        script = ["python", "retranscription.py", wav_path]

    if script:
        try:
            # bloquant : attend la fin de la transcription + chiffrement du texte
            subprocess.run(script, check=False)
        except Exception as e:
            print(f"[WARN] Impossible de lancer la transcription : {e}")
    else:
        print("[INFO] Aucun script de transcription trouvé (retranscription_emma.py / retranscription.py).")


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
    """
    Enregistre la vidéo + affiche un aperçu temps réel avec détection des visages (rectangles verts).
    - Fichier de sortie .mp4 (mp4v)
    - Ouvre une fenêtre "Enregistrement vidéo"
    - Stop propre (writer/camera/fenêtre) via .stop()

    Dépendances: opencv-python (cv2) et les haarcascades (incluses via cv2.data.haarcascades).
    """
    def __init__(
        self,
<<<<<<< HEAD
        save_dir="videos_chiffrees",
=======
        save_dir="videos",
>>>>>>> 27780bb (Ajout/modif du recorder_porcupine_emma.py)
        fps=20,
        fourcc="mp4v",
        resolution=None,               # ex: (1280, 720) ou None pour auto
        camera_index=0,
        show_window=True,
        face_rect_color=(0, 255, 0),   # vert
        face_rect_thickness=2,
        cascade_path=None              # par défaut: cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    ):
        self.save_dir = save_dir
        self.fps = fps
        self.fourcc = fourcc
        self.resolution = resolution
        self.camera_index = camera_index
        self.show_window = show_window
        self.face_rect_color = face_rect_color
        self.face_rect_thickness = face_rect_thickness

        # Charge le classifieur visage (haar cascade)
        if cascade_path is None:
            cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            raise RuntimeError(f"[VIDEO] Impossible de charger le cascade: {cascade_path}")

        self._stop_evt = threading.Event()
        self._thread = None
        self._writer = None
        self._cap = None
        self._outfile = None
        self._win_name = "Enregistrement vidéo"

    def start(self):
        """Démarre l’enregistrement (thread)."""
        if self._thread and self._thread.is_alive():
            print("[VIDEO] Déjà en cours.")
            return

        ensure_dir(self.save_dir)
        self._outfile = os.path.join(self.save_dir, ts_name("video", "mp4"))

        self._stop_evt.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print(f"[VIDEO] Enregistrement démarré → {self._outfile}")

    def stop(self):
        """Demande l’arrêt et attend la fin proprement."""
        if not self._thread:
            return
        self._stop_evt.set()
        self._thread.join(timeout=5.0)
        self._thread = None
        print("[VIDEO] Enregistrement arrêté.")

    def _open_camera(self):
        self._cap = cv2.VideoCapture(self.camera_index)
        if not self._cap.isOpened():
            raise RuntimeError("[VIDEO] Impossible d'ouvrir la caméra.")

        # Résolution voulue
        if self.resolution:
            w, h = self.resolution
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

        # Résolution réelle
        w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Writer
        fourcc = cv2.VideoWriter_fourcc(*self.fourcc)
        self._writer = cv2.VideoWriter(self._outfile, fourcc, self.fps, (w, h))
        if not self._writer.isOpened():
            raise RuntimeError("[VIDEO] Impossible d'ouvrir le writer vidéo.")
        return w, h

    def _run(self):
        try:
            w, h = self._open_camera()
            # Petite montée en température de la caméra
            for _ in range(5):
                self._cap.read()

            if self.show_window:
                cv2.namedWindow(self._win_name, cv2.WINDOW_NORMAL)
                cv2.resizeWindow(self._win_name, min(960, w), min(540, h))

            while not self._stop_evt.is_set():
                ok, frame = self._cap.read()
                if not ok:
                    break

                # Détection des visages (sur niveaux de gris)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(60, 60)
                )

                # Dessine les rectangles verts autour des visages
                for (x, y, fw, fh) in faces:
                    cv2.rectangle(
                        frame,
                        (x, y),
                        (x + fw, y + fh),
                        self.face_rect_color,
                        self.face_rect_thickness
                    )

                # Écrit la frame dans la vidéo
                self._writer.write(frame)

                # Aperçu temps réel
                if self.show_window:
                    cv2.imshow(self._win_name, frame)
                    # waitKey(1) pour rafraîchir la fenêtre; ne bloque pas la boucle Porcupine
                    # On ne gère PAS de touche ici (l’arrêt se fait via mot-clé "terminator")
                    cv2.waitKey(1)

        except Exception as e:
            print(f"[VIDEO][ERROR] {e}")

        finally:
            # Libère proprement
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
            if self.show_window:
                try:
                    cv2.destroyWindow(self._win_name)
                except Exception:
<<<<<<< HEAD
                    pass 


def encrypt_video_to_json(video_path: str, out_dir="videos_chiffrees"):
=======
                    pass


def encrypt_video_to_json(video_path: str, out_dir="videos_chiffres"):
>>>>>>> 27780bb (Ajout/modif du recorder_porcupine_emma.py)
    """
    Lit un fichier vidéo MP4, chiffre son contenu avec AES-GCM et sauvegarde un JSON.
    """
    ensure_dir(out_dir)

    with open(video_path, "rb") as f:
        contenu_video = f.read()

    nonce, ciphertext = encrypt_bytes(contenu_video)
    bundle = {
        "nonce": base64.urlsafe_b64encode(nonce).decode("utf-8"),
        "ciphertext": base64.urlsafe_b64encode(ciphertext).decode("utf-8")
    }

    name_only = os.path.basename(video_path)
    out_path = os.path.join(out_dir, name_only + ".aes.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2)

    print(f"[VIDEO] Vidéo chiffrée sauvegardée : {out_path}")
    return out_path


# =========================
# ======  FUSION  =========
# =========================

def main():
<<<<<<< HEAD
    ensure_dir(ENCRYPTED_SAVE_DIR)
=======
    ensure_dir(AUDIO_SAVE_DIR)
    ensure_dir(ENCRYPTED_SAVE_DIR)
    ensure_dir(VIDEO_SAVE_DIR)
>>>>>>> 27780bb (Ajout/modif du recorder_porcupine_emma.py)

    # Porcupine avec 3 mots-clés (audio start / video start / stop)
    try:
        porcupine = pvporcupine.create(
            access_key=ACCESS_KEY,
            keywords=[AUDIO_START_WORD, VIDEO_START_WORD, STOP_WORD],
            sensitivities=[SENSITIVITY, SENSITIVITY, SENSITIVITY],
        )
    except pvporcupine.PorcupineActivationLimitError:
        print("[ERROR] Votre clé Picovoice a atteint la limite d’activations. Révoquez des appareils ou générez une nouvelle clé.")
        return
    except Exception as e:
        print(f"[ERROR] Échec d’initialisation Porcupine : {e}")
        return

    sample_rate = porcupine.sample_rate
    frame_length = porcupine.frame_length

    recorder = PvRecorder(frame_length=frame_length)
    recorder.start()

    video_rec = VideoRecorder()

    print(f"Écoute en cours…\n"
<<<<<<< HEAD
          f"- Dis '{AUDIO_START_WORD}' pour démarrer l'audio\n"
          f"- Dis '{VIDEO_START_WORD}' pour démarrer la vidéo\n"
          f"- Dis '{STOP_WORD}' pour arrêter tout (audio+vidéo)\n"
=======
          f"- Dis '{AUDIO_START_WORD}' pour démarrer l'**audio**\n"
          f"- Dis '{VIDEO_START_WORD}' pour démarrer la **vidéo**\n"
          f"- Dis '{STOP_WORD}' pour **arrêter tout** (audio+vidéo)\n"
>>>>>>> 27780bb (Ajout/modif du recorder_porcupine_emma.py)
          f"- Appuie sur [ESPACE] pour quitter.\n")

    audio_recording = False
    audio_buffer = bytearray()
    audio_start_time = 0.0
    wav_temp_path = None  # dernier WAV non chiffré

    try:
        while not keyboard.is_pressed("space"):
            pcm = recorder.read()  # list[int16]
            kw_idx = porcupine.process(pcm)  # -1 si rien

            # si on enregistre l'audio, accumule
            if audio_recording:
                audio_buffer.extend(struct.pack("h" * len(pcm), *pcm))
                elapsed = time.time() - audio_start_time
                if elapsed > MAX_AUDIO_RECORD_S:
                    # auto stop audio
<<<<<<< HEAD
                    audio_recording = False 
                    filename = os.path.join(ENCRYPTED_SAVE_DIR, ts_name("audio", "wav"))
=======
                    audio_recording = False
                    filename = os.path.join(AUDIO_SAVE_DIR, ts_name("audio", "wav"))
>>>>>>> 27780bb (Ajout/modif du recorder_porcupine_emma.py)
                    write_wav_int16(bytes(audio_buffer), sample_rate, filename)
                    print(f"[AUDIO] Auto-stop après {MAX_AUDIO_RECORD_S}s → {filename}")

                    # 1) Chiffrer le WAV
                    enc_json = encrypt_wav_to_json(filename, ENCRYPTED_SAVE_DIR)
                    print(f"[AUDIO] Audio chiffré : {enc_json}")

                    # 2) Transcrire + chiffrer le texte
                    run_transcription(filename)

                    # 3) Supprimer le WAV en clair
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
                    print(f"[AUDIO] Mot-clé '{AUDIO_START_WORD}' détecté → démarrage de l'enregistrement audio.")

            elif kw_idx == 1:  # VIDEO_START_WORD
                if not (video_rec._thread and video_rec._thread.is_alive()):
                    video_rec.start()
                else:
                    print("[VIDEO] Déjà en cours.")

            elif kw_idx == 2:  # STOP_WORD
                any_running = audio_recording or (video_rec._thread and video_rec._thread.is_alive())
                if any_running:
                    print(f"[ALL] Mot-clé '{STOP_WORD}' détecté → arrêt des enregistrements.")

                # Stop audio si en cours
                if audio_recording:
                    audio_recording = False
<<<<<<< HEAD
                    filename = os.path.join(ENCRYPTED_SAVE_DIR, ts_name("audio", "wav"))
=======
                    filename = os.path.join(AUDIO_SAVE_DIR, ts_name("audio", "wav"))
>>>>>>> 27780bb (Ajout/modif du recorder_porcupine_emma.py)
                    write_wav_int16(bytes(audio_buffer), sample_rate, filename)
                    print(f"[AUDIO] Enregistrement sauvegardé : {filename}")

                    # 1) Chiffrer le WAV
                    enc_json = encrypt_wav_to_json(filename, ENCRYPTED_SAVE_DIR)
                    print(f"[AUDIO] Audio chiffré : {enc_json}")

                    # 2) Transcrire + chiffrer le texte
                    run_transcription(filename)

                    # 3) Supprimer le WAV en clair
                    try:
                        os.remove(filename)
                    except Exception:
                        pass

                    audio_buffer.clear()
                    wav_temp_path = None

                # Stop vidéo si en cours
                if video_rec._thread and video_rec._thread.is_alive():
                    video_rec.stop()

<<<<<<< HEAD
                    # Chiffrement de la vidéo
                    if video_rec._outfile and os.path.exists(video_rec._outfile):
                        encrypt_video_to_json(video_rec._outfile)
                        try:
                            os.remove(video_rec._outfile)  # supprime la vidéo en clair
                        except Exception:
                            pass

=======
>>>>>>> 27780bb (Ajout/modif du recorder_porcupine_emma.py)
    except KeyboardInterrupt:
        print("\n[INFO] Arrêt manuel.")
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

        # En cas de sortie alors que l'audio était en cours → flush/sauvegarde
        if audio_recording and audio_buffer:
<<<<<<< HEAD
            filename = os.path.join(ENCRYPTED_SAVE_DIR, ts_name("audio", "wav"))
=======
            filename = os.path.join(AUDIO_SAVE_DIR, ts_name("audio", "wav"))
>>>>>>> 27780bb (Ajout/modif du recorder_porcupine_emma.py)
            write_wav_int16(bytes(audio_buffer), sample_rate, filename)
            print(f"[AUDIO] Sauvegarde de secours : {filename}")

            enc_json = encrypt_wav_to_json(filename, ENCRYPTED_SAVE_DIR)
            print(f"[AUDIO] Audio chiffré : {enc_json}")

            run_transcription(filename)

            try:
                os.remove(filename)
            except Exception:
                pass

        # En cas de sortie alors que la vidéo tournait → stop
        if video_rec._thread and video_rec._thread.is_alive():
            video_rec.stop()

            # Après video_rec.stop()
            if video_rec._outfile and os.path.exists(video_rec._outfile):
                encrypt_video_to_json(video_rec._outfile)
                try:
                    os.remove(video_rec._outfile)  # optionnel : supprime la vidéo en clair
                except Exception:
                    pass



if __name__ == "__main__":
    main()
