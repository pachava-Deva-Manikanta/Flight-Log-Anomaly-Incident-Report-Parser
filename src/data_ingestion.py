import pandas as pd

from src.utils import load_yaml
from src.logger import get_logger

logger = get_logger(__name__)


def load_data():
    config = load_yaml("configs/config.yaml")
    df = pd.read_csv(config["data"]["raw_path"])
    logger.info(f"Loaded {len(df)} rows")

    # Remove rows without description or urgency (we can't learn from them)
    df = df.dropna(subset=["description", "urgency"])

    # Remove exact duplicate rows
    df = df.drop_duplicates()

    # Fill missing component with empty text and tidy the label
    df["component"] = df["component"].fillna("")
    df["urgency"] = df["urgency"].str.strip()

    logger.info(f"After cleaning: {len(df)} rows")
    logger.info(f"Urgency counts:\n{df['urgency'].value_counts()}")
    return df


if __name__ == "__main__":
    data = load_data()
    print(data.head())