import yaml
import nltk


def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def download_nltk_data():
    # name to download -> where NLTK stores it
    resources = {
        "punkt": "tokenizers/punkt",
        "punkt_tab": "tokenizers/punkt_tab",
        "averaged_perceptron_tagger": "taggers/averaged_perceptron_tagger",
        "averaged_perceptron_tagger_eng": "taggers/averaged_perceptron_tagger_eng",
        "stopwords": "corpora/stopwords",
        "wordnet": "corpora/wordnet",
    }
    for name, path in resources.items():
        try:
            nltk.data.find(path)          # already downloaded? skip
        except LookupError:
            try:
                nltk.download(name, quiet=True)
            except Exception:
                pass                       # some names don't exist in every NLTK version