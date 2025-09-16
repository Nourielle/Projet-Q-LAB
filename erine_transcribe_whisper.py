from faster_whisper import WhisperModel

_MODEL = None
def get_model():
    global _MODEL
    if _MODEL is None:
        # "small" = bonne qualité; "base" si PC lent (plus léger)
        _MODEL = WhisperModel("small", device="cpu", compute_type="int8")
    return _MODEL

def transcribe_wav(path_wav: str) -> str:
    model = get_model()
    segments, info = model.transcribe(path_wav, language="fr")
    parts = [seg.text.strip() for seg in segments]
    return " ".join(parts).strip()

if __name__ == "__main__":
    import sys
    print(transcribe_wav(sys.argv[1]))
