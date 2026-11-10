from sklearn.feature_extraction.text import TfidfVectorizer

from src.utils import load_yaml


def build_vectorizer():
    params = load_yaml("configs/params.yaml")["features"]
    vectorizer = TfidfVectorizer(
        max_features=params["max_features"],
        ngram_range=tuple(params["ngram_range"]),
        min_df=params["min_df"],
    )
    return vectorizer