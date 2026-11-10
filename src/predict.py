# import joblib

# from src.preprocessing import clean_text
# from src.utils import load_yaml

# config = load_yaml("configs/config.yaml")
# model = joblib.load(config["model"]["model_path"])
# vectorizer = joblib.load(config["model"]["vectorizer_path"])


# def predict_urgency(description, component=""):
#     # text = f"{component}. {description}" if component else description
#     text = description
#     cleaned = clean_text(text)
#     features = vectorizer.transform([cleaned])
#     urgency = model.predict(features)[0]
#     return {"urgency": str(urgency), "cleaned_text": cleaned}


# if __name__ == "__main__":
#     print(predict_urgency("smoke smell in cockpit during taxi", "Cockpit"))
#     print(predict_urgency("hyd leek at MLG actuator", "Hydraulic System"))
#     print(predict_urgency("reading light flikering at seat 12", "Reading Light"))
import json
import joblib
import numpy as np

from src.preprocessing import clean_text
from src.utils import load_yaml

config = load_yaml("configs/config.yaml")
model = joblib.load(config["model"]["model_path"])
vectorizer = joblib.load(config["model"]["vectorizer_path"])

with open(config["model"]["info_path"]) as f:
    model_info = json.load(f)

# Below this confidence, the UI asks for an engineer to review the log
LOW_CONFIDENCE = 0.50


def get_probabilities(features):
    # NB, Logistic Regression and calibrated SVM all have predict_proba
    if hasattr(model, "predict_proba"):
        return model.predict_proba(features)[0]
    # Backup: turn raw scores into percentages (softmax)
    scores = model.decision_function(features)[0]
    exp = np.exp(scores - scores.max())
    return exp / exp.sum()


def predict_urgency(description, component=""):
    text = f"{component}. {description}" if component else description
    cleaned = clean_text(text)
    features = vectorizer.transform([cleaned])

    probs = get_probabilities(features)
    classes = model.classes_
    best = int(np.argmax(probs))
    confidence = float(probs[best])

    # Words the model actually knows from training
    keywords = [w for w in cleaned.split() if w in vectorizer.vocabulary_]

    return {
        "urgency": str(classes[best]),
        "confidence": round(confidence, 4),
        "probabilities": {str(c): round(float(p), 4) for c, p in zip(classes, probs)},
        "low_confidence": confidence < LOW_CONFIDENCE or len(keywords) == 0,
        "keywords": keywords,
        "cleaned_text": cleaned,
    }


if __name__ == "__main__":
    print(predict_urgency("smoke at electrical panel, fire risk", "Electrical"))
    print(predict_urgency("hyd line leak, minor, found on walkaround", "Hydraulic System"))