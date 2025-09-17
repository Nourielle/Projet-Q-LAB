import os
import time
import cv2
import pytz
from datetime import datetime
import pvporcupine
from pvrecorder import PvRecorder
import keyboard

# === CONFIGURATION ===
ACCESS_KEY = "QGobPJP9Rzl7HaJdOhzn3Gs3RW7aWyLQVHtUh+NOfeI2+SffLM+eqQ=="  
KEYWORDS = ["jarvis", "terminator"]     # jarvis = start vidéo, terminator = stop vidéo
SENSITIVITY = 0.9                       # plus proche de 1 = plus sensible
SAVE_DIR = "video"                      # dossier où sauvegarder les vidéos
MAX_RECORD_S = 3600                     # durée max d’un enregistrement (ici 1h)


# === UTILITAIRES ===

def ensure_dir(path):
    """Créer le dossier s’il n’existe pas."""
    os.makedirs(path, exist_ok=True)

def paris_now():
    """Retourne la date/heure de lyon."""
    return datetime.now(pytz.timezone("Europe/Paris"))

def paris_filename():
    """Crée un nom unique pour chaque fichier vidéo basé sur la date/heure."""
    return paris_now().strftime("%Y-%m-%d_%H-%M-%S") + ".avi"


# === FONCTION PRINCIPALE ===
def detect_keyword_video():
    ensure_dir(SAVE_DIR)  # s’assure que le dossier existe

    # Charger le modèle HaarCascade pour la détection faciale (OpenCV)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    if face_cascade.empty():
        raise RuntimeError("❌ Impossible de charger le modèle de détection faciale OpenCV.")

    # Initialiser Porcupine pour écouter les mots-clésco
    porcupine = pvporcupine.create(
        access_key=ACCESS_KEY,
        keywords=KEYWORDS,
        sensitivities=[SENSITIVITY]*len(KEYWORDS)
    )

    # Initialiser l’enregistreur (micro) pour Porcupine
    frame_length = porcupine.frame_length
    recorder = PvRecorder(frame_length=frame_length)
    recorder.start()

    print(f"🎤 Écoute vidéo... Dis '{KEYWORDS[0]}' pour démarrer, '{KEYWORDS[1]}' pour arrêter.")
    print("Appuie sur [ESPACE] pour quitter.\n")

    # Variables d’état
    recording = False
    cap = None
    out = None
    record_start_time = 0
    filename = None

    try:
        while not keyboard.is_pressed("space"):  # boucle principale
            pcm = recorder.read()  
            keyword_index = porcupine.process(pcm)  # -1 si rien, 0 = jarvis, 1 = terminator

            # === Si on est en train d’enregistrer ===
            if recording:
                ret, frame = cap.read()
                if not ret:
                    break  # si problème avec la caméra → stop

                # --- Détection faciale ---
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30)
                )

                # Dessiner un rectangle vert pour chaque visage détecté
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

                # ✅ Nouveau : afficher le nombre de visages détectés dans la console
                if len(faces) > 0:
                    print(f"👤 {len(faces)} visage(s) détecté(s)")

                # ✅ Nouveau : afficher le temps écoulé sur la vidéo
                elapsed = int(time.time() - record_start_time)
                cv2.putText(frame, f"Time: {elapsed}s", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

                # Sauvegarde + affichage
                out.write(frame)
                cv2.imshow("Recording Video + Face Detection", frame)

                # Arrêt automatique si durée max dépassée
                if elapsed > MAX_RECORD_S:
                    print(f"\n⏹️ Arrêt auto après {MAX_RECORD_S} secondes.")
                    recording = False

                # Arrêt manuel si touche Q pressée
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    recording = False

            # === Démarrage vidéo avec le mot "jarvis" ===
            if not recording and keyword_index == 0:
                filename = os.path.join(SAVE_DIR, paris_filename())
                cap = cv2.VideoCapture(0)  # ouvre la caméra
                fourcc = cv2.VideoWriter_fourcc(*'XVID')  # codec vidéo
                fps = 20.0
                width = int(cap.get(3))   # largeur de la vidéo
                height = int(cap.get(4))  # hauteur de la vidéo
                out = cv2.VideoWriter(filename, fourcc, fps, (width, height))

                recording = True
                record_start_time = time.time()
                print("▶️ Mot-clé 'jarvis' détecté : démarrage vidéo avec détection faciale...")

            # === Arrêt vidéo avec le mot "terminator" ===
            elif recording and keyword_index == 1:
                recording = False
                print(f"⏹️ Mot-clé 'terminator' détecté : arrêt de la vidéo -> {filename}")

    except KeyboardInterrupt:
        print("\nProgramme vidéo arrêté manuellement.")

    finally:
        # Nettoyage (libération des ressources)
        recorder.stop()
        recorder.delete()
        porcupine.delete()
        if cap:
            cap.release()
        if out:
            out.release()
        cv2.destroyAllWindows()


# === Lancement du programme ===
if __name__ == "__main__":
    detect_keyword_video()
