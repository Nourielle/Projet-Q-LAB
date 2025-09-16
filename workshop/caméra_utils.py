import cv2
import time

def record_video(filename="capture.avi", duration=3600):
    """
    Enregistre une vidéo depuis la webcam du PC pendant 'duration' secondes (par défaut 1h).
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Erreur : Impossible d'accéder à la caméra.")
        return

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    fps = 20.0
    width = int(cap.get(3))
    height = int(cap.get(4))
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))

    print(f"🎥 Enregistrement vidéo ({duration//60} minutes)...")
    start_time = time.time()
    while int(time.time() - start_time) < duration:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
        # Affiche la vidéo en direct (optionnel)
        cv2.imshow('Enregistrement', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print(f"Vidéo sauvegardée sous : {filename}")

def take_photo(filename="photo.jpg"):
    """
    Prend une photo depuis la webcam et la sauvegarde sous 'filename'.
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Erreur : Impossible d'accéder à la caméra.")
        return

    ret, frame = cap.read()
    if ret:
        cv2.imwrite(filename, frame)
        print(f"📸 Photo sauvegardée sous : {filename}")
        cv2.imshow('Photo', frame)
        cv2.waitKey(1000)  # Affiche la photo pendant 1 seconde
        cv2.destroyAllWindows()
    else:
        print("Erreur : Impossible de prendre la photo.")
    cap.release()