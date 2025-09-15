import glob, librosa, numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from joblib import dump

SR = 16000
N_MFCC = 13

def extract(path):
    y, sr = librosa.load(path, sr=SR)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
    feat = np.concatenate([mfcc.mean(axis=1), mfcc.std(axis=1)])
    return feat

X, y = [], []
for p in glob.glob("data/keyword/*.wav"):
    X.append(extract(p)); y.append(1)
for p in glob.glob("data/other/*.wav"):
    X.append(extract(p)); y.append(0)

X, y = np.array(X), np.array(y)

scaler = StandardScaler().fit(X)
X_scaled = scaler.transform(X)

clf = LogisticRegression(max_iter=200, class_weight="balanced", C=2.0)
clf.fit(X_scaled, y)

dump(scaler, "scaler.pkl")
dump(clf, "clf.pkl")
print("✅ Modèle entraîné et sauvegardé (scaler.pkl, clf.pkl)")
