# -*- coding: utf-8 -*-
#!/usr/bin/env/
import cv2
import os
from datetime import datetime

# Dossier de sortie
OUTPUT_DIR = "../outputs/images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Ouvrir la cam�ra (0 = cam�ra par d�faut)
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # CAP_DSHOW am�liore la compatibilit� Windows

if not cap.isOpened():
    print("? Impossible d'ouvrir la cam�ra")
    exit()

# Capture une seule image
ret, frame = cap.read()

if ret:
    # G�n�rer un nom de fichier unique avec l'heure
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(OUTPUT_DIR, f"photo_{ts}.jpg")
    cv2.imwrite(file_path, frame)

    # Afficher l'image 3 secondes
    cv2.imshow("Test Cam�ra - Capture", frame)
    cv2.waitKey(3000)

    print(f"? Photo sauvegard�e : {file_path}")
else:
    print("? Impossible de capturer une image")

cap.release()
cv2.destroyAllWindows()
