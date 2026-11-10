import re
from nltk import sent_tokenize, word_tokenize, pos_tag
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

from src.utils import load_yaml, download_nltk_data
from src.logger import get_logger

logger = get_logger(__name__)
download_nltk_data()

# ---- Load settings once ----
params = load_yaml("configs/params.yaml")
dictionary = load_yaml("configs/acronyms.yaml")

ACRONYMS = {k.lower(): v.lower() for k, v in dictionary["acronyms"].items()}
SPELLING = {k.lower(): v.lower() for k, v in dictionary["spelling"].items()}
KEEP_POS = tuple(params["preprocessing"]["keep_pos"])

# Keep negation words: "not responding" is very different from "responding"
# NEGATIONS = {"no", "not", "nor"}
# Words we always keep, even if POS tagging would drop them
NEGATIONS = {"no", "not", "nor", "within", "beyond", "above", "below"}
STOP_WORDS = set(stopwords.words("english")) - NEGATIONS

lemmatizer = WordNetLemmatizer()


def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"\s+", " ", text)          # remove extra spaces
    final_words = []

    # 1. Sentence tokenization
    sentences = sent_tokenize(text)

    for sentence in sentences:
        # 2. Word tokenization
        words = word_tokenize(sentence)

        fixed_words = []
        for word in words:
            word = SPELLING.get(word, word)    # 3. Spelling correction
            word = ACRONYMS.get(word, word)    # 4. Acronym expansion
            fixed_words.extend(word.split())   # "mlg" -> "main landing gear" = 3 words

        # 5. POS tagging -> [("hydraulic", "JJ"), ("leak", "NN"), ...]
        tagged = pos_tag(fixed_words)

        for word, tag in tagged:
            if not word.isalpha():             # drop numbers and punctuation
                continue
            if word in NEGATIONS:
                final_words.append(word)
                continue
            if word in STOP_WORDS:
                continue
            if tag.startswith(KEEP_POS):       # keep only nouns, verbs, adjectives, adverbs
                pos = "v" if tag.startswith("VB") else "n"
                final_words.append(lemmatizer.lemmatize(word, pos=pos))  # 6. Lemmatize

    return " ".join(final_words)


def preprocess_dataframe(df):
    config = load_yaml("configs/config.yaml")
    df = df.copy()

    # Join component + description so the model sees both
    df["text"] = df["description"].astype(str)
    df["clean_text"] = df["text"].apply(clean_text)

    df = df[df["clean_text"].str.strip() != ""]   # drop rows that became empty

    df[["log_id", "text", "clean_text", "urgency"]].to_csv(
        config["data"]["processed_path"], index=False
    )
    logger.info(f"Saved processed data to {config['data']['processed_path']}")
    return df


if __name__ == "__main__":
    examples = [
        "Hydralic fluid leek found at MLG actuator. Reported by crew.",
        "Fire wraning eng 2 during climb",
        "Aileron jammed, flight control not responding",
    ]
    print("POS tags example:", pos_tag(word_tokenize("hydraulic fluid leak found at actuator")))
    print()
    for e in examples:
        print("BEFORE:", e)
        print("AFTER :", clean_text(e))
        print()