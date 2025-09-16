# V�rifie la version de Python
Write-Host "V�rification de Python..."
python --version

# Mise � jour de pip
Write-Host "Mise � jour de pip..."
python -m pip install --upgrade pip

# Installation des d�pendances pour la cam�ra
Write-Host "Installation des d�pendances OpenCV et outils..."
python -m pip install opencv-python opencv-contrib-python

# Installation des autres librairies utiles
Write-Host "Installation de Numpy..."
python -m pip install numpy

# (Optionnel si tu veux pr�parer aussi la voix plus tard)
Write-Host "Installation de Sounddevice et Vosk..."
python -m pip install sounddevice vosk

Write-Host "? Installation termin�e ! Tu peux tester avec : python camera/test_camera.py"
