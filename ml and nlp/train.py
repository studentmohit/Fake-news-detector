"""
=======================================================
  FAKE NEWS ANALYSER — PORTION 1: MODEL TRAINING
=======================================================
PURPOSE   : Train a fake-news classifier using NLP
            features and Machine Learning.
ALGORITHM :
  • TF-IDF  → converts text into numeric feature vectors
              (Term Frequency × Inverse Document Frequency)
  • Logistic Regression → binary classifier (FAKE / REAL)
DATASET   : WELFake (72,134 articles, Kaggle)
  Download: https://www.kaggle.com/datasets/
            saurabhshahane/fake-news-classification
OUTPUT    : saved_model/model.pkl
            saved_model/tfidf.pkl
            saved_model/preprocessor.pkl
=======================================================
"""

import os
import pickle

import numpy  as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model            import LogisticRegression
from sklearn.metrics                 import (accuracy_score,
                                             classification_report,
                                             confusion_matrix)
from sklearn.model_selection         import train_test_split

from preprocess import TextPreprocessor


# ─────────────────────────────────────────────────────
# STEP A — Load dataset
# ─────────────────────────────────────────────────────
def load_dataset(csv_path: str = 'WELFake_Dataset.csv') -> pd.DataFrame:
    """
    Expected CSV columns: title, text, label
      label: 1 = REAL news,  0 = FAKE news
    """
    try:
        df = pd.read_csv(csv_path)
        # Combine title + body for richer features
        if 'title' in df.columns and 'text' in df.columns:
            df['content'] = df['title'].fillna('') + ' ' + df['text'].fillna('')
        else:
            df['content'] = df['text'].fillna('')

        df = df.dropna(subset=['content', 'label'])
        df['label'] = df['label'].astype(int)

        print(f"✔ Loaded {len(df):,} articles")
        print(f"  REAL : {(df['label'] == 1).sum():,}")
        print(f"  FAKE : {(df['label'] == 0).sum():,}")
        return df

    except FileNotFoundError:
        print("⚠  Dataset file not found — using built-in demo data.")
        print("   Download WELFake from Kaggle for real training.\n")
        return _demo_dataset()


def _demo_dataset() -> pd.DataFrame:
    """Small hard-coded dataset for quick demos / testing."""
    fake_samples = [
        "SHOCKING vaccines cause autism government hiding truth mass cover up",
        "Alien spacecraft spotted over capital city government denies everything",
        "5G towers controlling minds deep state exposed drink bleach cure",
        "Moon landing completely faked Hollywood studio NASA conspirators caught",
        "Secret reptilian elite ruling world banker globalist exposed whistleblower",
        "Bill Gates microchip inside COVID vaccine track everyone worldwide",
        "Scientists discover miracle cure for cancer big pharma suppressing it",
        "Earth is actually flat and NASA lying to us since 1969",
    ]
    real_samples = [
        "Federal Reserve raised interest rates citing persistent inflation pressures",
        "Scientists publish peer-reviewed research showing rising sea levels globally",
        "Parliament passes new data privacy legislation protecting consumer information",
        "Tech firm reports twelve percent quarterly revenue growth beating estimates",
        "Health officials recommend vaccines as safest protection against seasonal flu",
        "New climate study confirms global temperatures rising over past century",
        "Central bank holds rates steady awaiting more economic data from markets",
        "Research published in journal Nature links air quality to heart disease",
    ]
    data = {
        'content': (fake_samples + real_samples) * 60,
        'label'  : ([0] * len(fake_samples) + [1] * len(real_samples)) * 60,
    }
    return pd.DataFrame(data)


# ─────────────────────────────────────────────────────
# STEP B — Preprocess text with NLP
# ─────────────────────────────────────────────────────
def preprocess_data(df: pd.DataFrame) -> tuple:
    print("\n[NLP] Cleaning and preprocessing text...")
    preprocessor = TextPreprocessor()
    df['clean'] = df['content'].apply(preprocessor.clean_text)
    print(f"  Sample → {df['clean'].iloc[0][:80]}...")
    return df['clean'], df['label'], preprocessor


# ─────────────────────────────────────────────────────
# STEP C — TF-IDF feature extraction
# ─────────────────────────────────────────────────────
def build_tfidf(X_train, X_test):
    """
    TF-IDF turns each article into a numeric vector.
    • TF  (Term Frequency)  = how often a word appears in THIS doc
    • IDF (Inverse Doc Freq)= how rare the word is across ALL docs
    Rare but frequently used words score highest → most informative.
    """
    print("\n[TF-IDF] Building feature matrix...")
    tfidf = TfidfVectorizer(
        max_features = 10_000,   # keep top 10k most informative words
        ngram_range  = (1, 2),   # single words AND two-word pairs
        min_df       = 2,        # ignore words appearing < 2 times
        max_df       = 0.95,     # ignore words in >95% of docs (too common)
        sublinear_tf = True,     # dampen extreme term frequencies
    )
    X_train_vec = tfidf.fit_transform(X_train)  # learn vocabulary on train
    X_test_vec  = tfidf.transform(X_test)       # apply same vocabulary to test
    print(f"  Vocabulary size : {len(tfidf.vocabulary_):,} terms")
    print(f"  Feature matrix  : {X_train_vec.shape[0]:,} × {X_train_vec.shape[1]:,}")
    return X_train_vec, X_test_vec, tfidf


# ─────────────────────────────────────────────────────
# STEP D — Train Logistic Regression classifier
# ─────────────────────────────────────────────────────
def train_classifier(X_train_vec, y_train):
    """
    Logistic Regression learns a weight for each TF-IDF feature.
    Features strongly associated with fake news get a high FAKE weight;
    those associated with real news get a high REAL weight.
    """
    print("\n[ML] Training Logistic Regression...")
    model = LogisticRegression(
      max_iter    = 1000,
      C           = 1.0,
      solver      = 'lbfgs',
    )
    model.fit(X_train_vec, y_train)
    return model


# ─────────────────────────────────────────────────────
# STEP E — Evaluate
# ─────────────────────────────────────────────────────
def evaluate(model, X_test_vec, y_test):
    print("\n[EVAL] Evaluating on held-out test set...")
    y_pred   = model.predict(X_test_vec)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"  Accuracy : {accuracy * 100:.2f}%")
    print("\n  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['FAKE', 'REAL']))
    print("  Confusion Matrix (rows=actual, cols=predicted):")
    print(confusion_matrix(y_test, y_pred))


# ─────────────────────────────────────────────────────
# STEP F — Save model artefacts
# ─────────────────────────────────────────────────────
def save_model(model, tfidf, preprocessor, out_dir: str = 'saved_model'):
    os.makedirs(out_dir, exist_ok=True)
    for obj, name in [(model, 'model'), (tfidf, 'tfidf'), (preprocessor, 'preprocessor')]:
        with open(f'{out_dir}/{name}.pkl', 'wb') as f:
            pickle.dump(obj, f)
    print(f"\n✔ Model saved to '{out_dir}/' — ready for the Flask backend.")


# ─────────────────────────────────────────────────────
# MAIN — run all steps
# ─────────────────────────────────────────────────────
def main():
    print("=" * 54)
    print("   FAKE NEWS ANALYSER — MODEL TRAINING PIPELINE")
    print("=" * 54)

    df                           = load_dataset()
    X, y, preprocessor           = preprocess_data(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    X_train_vec, X_test_vec, tfidf = build_tfidf(X_train, X_test)
    model                          = train_classifier(X_train_vec, y_train)
    evaluate(model, X_test_vec, y_test)
    save_model(model, tfidf, preprocessor)
    print("=" * 54)


if __name__ == '__main__':
    main()