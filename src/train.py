import os
import json
import joblib
import mlflow
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, f1_score, classification_report

from src.data_ingestion import load_data
from src.preprocessing import preprocess_dataframe
from src.feature_engineering import build_vectorizer
from src.utils import load_yaml
from src.logger import get_logger

logger = get_logger(__name__)
config = load_yaml("configs/config.yaml")
params = load_yaml("configs/params.yaml")


def get_model(model_name, param_name, value):
    random_state = params.get("split", {}).get("random_state", 42)
    if model_name == "naive_bayes":
        return MultinomialNB(**{param_name: value})
    if model_name == "logistic_regression":
        return LogisticRegression(
            **{param_name: value},
            max_iter=1000,
            class_weight="balanced",
            random_state=random_state,
        )
    if model_name == "svm":
        # LinearSVC has no native probabilities -> CalibratedClassifierCV adds them
        svm = LinearSVC(
            **{param_name: value},
            class_weight="balanced",
            random_state=random_state,
            dual="auto",
        )
        return CalibratedClassifierCV(svm, cv=3)
    raise ValueError(f"Unknown model: {model_name}")


def main():
    # 1. Load + clean dataset
    df = load_data()
    df = preprocess_dataframe(df)

    # 2. Deduplication of identical cleaned texts to prevent data leakage
    before = len(df)
    df = df.drop_duplicates(subset=["clean_text"])
    logger.info(f"Removed {before - len(df)} duplicate texts -> {len(df)} unique rows left")

    # 3. Stratified 80/20 train-test split
    X_train_text, X_test_text, y_train, y_test = train_test_split(
        df["clean_text"],
        df["urgency"],
        test_size=params["split"]["test_size"],
        random_state=params["split"]["random_state"],
        stratify=df["urgency"],
    )

    # 4. Stratified 5-fold cross-validation on the training set
    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=params["split"]["random_state"],
    )

    # 5. MLflow experiment setup
    os.makedirs("mlruns", exist_ok=True)
    mlflow.set_tracking_uri(config["mlflow"]["tracking_uri"])
    mlflow.set_experiment(config["mlflow"]["experiment_name"])

    best_score = None  # Tuple: (cv_f1_mean, -cv_f1_std)
    best_pipe = None
    best_name = ""
    best_test_preds = None
    best_test_acc = 0.0

    all_results = []

    # 6. Grid evaluation over models and hyperparameters
    for model_name, param_grid in params["models"].items():
        for param_name, values in param_grid.items():
            for value in values:
                run_name = f"{model_name}_{param_name}={value}"

                # Pipeline: Vectorizer + Model (re-fit inside each CV fold to eliminate leakage)
                pipe = make_pipeline(
                    build_vectorizer(),
                    get_model(model_name, param_name, value),
                )

                # Stratified 5-fold cross-validation score on training partition
                cv_scores = cross_val_score(
                    pipe,
                    X_train_text,
                    y_train,
                    cv=cv,
                    scoring="f1_weighted",
                )
                cv_mean = float(cv_scores.mean())
                cv_std = float(cv_scores.std())

                # Fit on full training partition, then evaluate train vs test
                pipe.fit(X_train_text, y_train)
                train_f1 = float(f1_score(y_train, pipe.predict(X_train_text), average="weighted"))

                test_preds = pipe.predict(X_test_text)
                test_acc = float(accuracy_score(y_test, test_preds))
                test_f1 = float(f1_score(y_test, test_preds, average="weighted"))
                overfit_gap = float(train_f1 - test_f1)

                all_results.append({
                    "model": run_name,
                    "cv_f1": f"{cv_mean:.4f} ± {cv_std:.4f}",
                    "accuracy": f"{test_acc:.4f} ({test_acc * 100:.1f}%)",
                    "test_f1": f"{test_f1:.4f}",
                    "train_f1": f"{train_f1:.4f}",
                    "gap": f"{overfit_gap:.4f}"
                })

                # Log parameters & metrics to MLflow
                with mlflow.start_run(run_name=run_name):
                    mlflow.log_param("model", model_name)
                    mlflow.log_param(param_name, value)
                    mlflow.log_params(params["features"])
                    mlflow.log_metric("cv_f1_mean", cv_mean)
                    mlflow.log_metric("cv_f1_std", cv_std)
                    mlflow.log_metric("train_f1", train_f1)
                    mlflow.log_metric("test_f1", test_f1)
                    mlflow.log_metric("test_accuracy", test_acc)
                    mlflow.log_metric("overfit_gap", overfit_gap)

                logger.info(
                    f"{run_name:32s} acc={test_acc:.4f}  cv_f1={cv_mean:.4f}±{cv_std:.4f}  "
                    f"train_f1={train_f1:.4f}  test_f1={test_f1:.4f}  gap={overfit_gap:.4f}"
                )

                # Selection rule from README:
                # Highest mean CV F1; on a tie, the lower standard deviation (more stable) wins
                score = (round(cv_mean, 4), -round(cv_std, 4))
                if best_score is None or score > best_score:
                    best_score = score
                    best_pipe = pipe
                    best_name = run_name
                    best_test_preds = test_preds
                    best_test_acc = test_acc

    # 7. Print Model Comparison Table
    print("\n" + "=" * 90)
    print(f"{'MODEL / HYPERPARAMETER':<32} {'ACCURACY':<16} {'CV F1 (MEAN ± STD)':<22} {'TEST F1':<10} {'GAP':<8}")
    print("=" * 90)
    for res in all_results:
        star = " ★ BEST" if res["model"] == best_name else ""
        print(f"{res['model']:<32} {res['accuracy']:<16} {res['cv_f1']:<22} {res['test_f1']:<10} {res['gap']:<8}{star}")
    print("=" * 90)

    # Final report for the best model on the untouched test set
    cv_mean_best = best_score[0]
    cv_std_best = -best_score[1]
    logger.info(f"BEST MODEL SELECTED: {best_name} (acc={best_test_acc:.4f}, cv_f1={cv_mean_best:.4f} ± {cv_std_best:.4f})")
    print(f"\nFINAL EVALUATION ON UNTOUCHED TEST SET ({best_name})")
    print("=" * 60)
    print(classification_report(y_test, best_test_preds))

    # 8. Save best vectorizer, model, and metadata
    os.makedirs(config["model"]["model_dir"], exist_ok=True)
    joblib.dump(best_pipe[0], config["model"]["vectorizer_path"])
    joblib.dump(best_pipe[-1], config["model"]["model_path"])

    with open(config["model"]["info_path"], "w") as f:
        json.dump(
            {
                "best_model": best_name,
                "accuracy": round(best_test_acc, 4),
                "cv_f1_mean": round(cv_mean_best, 4),
                "cv_f1_std": round(cv_std_best, 4),
                "classes": [str(c) for c in best_pipe[-1].classes_],
            },
            f,
            indent=2,
        )

    logger.info(f"Saved best model, vectorizer, and metadata in {config['model']['model_dir']}/")


if __name__ == "__main__":
    main()
