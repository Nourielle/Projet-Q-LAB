# Vérifie la version de Python
Write-Host "Vérification de Python..."
python --version

# Mise à jour de pip
Write-Host "Mise à jour de pip..."
python -m pip install --upgrade pip

# Installation des dépendances pour la caméra
Write-Host "Installation des dépendances OpenCV et outils..."
python -m pip install opencv-python opencv-contrib-python

# Installation des autres librairies utiles
Write-Host "Installation de Numpy..."
python -m pip install numpy

# (Optionnel si tu veux préparer aussi la voix plus tard)
Write-Host "Installation de Sounddevice et Vosk..."
python -m pip install sounddevice vosk

Write-Host "? Installation terminée ! Tu peux tester avec : python camera/test_camera.py"
