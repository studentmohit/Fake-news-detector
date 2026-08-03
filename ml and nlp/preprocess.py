"""
=======================================================
  FAKE NEWS ANALYSER — PORTION 1: NLP PREPROCESSING
=======================================================
PURPOSE  : Clean and normalize raw news text before
           feeding it into the ML model.
LIBRARY  : NLTK (Natural Language Toolkit)
HOW IT   :
  1. Lowercase the text
  2. Remove URLs, HTML tags, special characters
  3. Tokenize (split into individual words)
  4. Remove stopwords (the, is, a, an, etc.)
  5. Lemmatize (running → run, better → good)
=======================================================
"""

import re
import nltk

# Download required NLTK resources (run once)
nltk.download('punkt',     quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet',   quiet=True)

from nltk.corpus   import stopwords
from nltk.stem     import WordNetLemmatizer
from nltk.tokenize import word_tokenize


class TextPreprocessor:
    """Handles all NLP preprocessing steps."""

    def __init__(self):
        # Set of common English words to ignore (the, is, and, ...)
        self.stop_words  = set(stopwords.words('english'))
        # Lemmatizer converts words to base form (running → run)
        self.lemmatizer  = WordNetLemmatizer()

    # --------------------------------------------------
    # STEP 1 — Remove noise from raw text
    # --------------------------------------------------
    def _remove_noise(self, text: str) -> str:
        text = text.lower()                              # lowercase
        text = re.sub(r'https?://\S+|www\.\S+', '', text)  # URLs
        text = re.sub(r'<.*?>',                  '', text)  # HTML tags
        text = re.sub(r'\[.*?\]',                '', text)  # [brackets]
        text = re.sub(r'[^a-z\s]',               '', text)  # keep letters only
        text = re.sub(r'\s+',                   ' ', text).strip()
        return text

    # --------------------------------------------------
    # STEP 2 — Tokenize, filter stopwords, lemmatize
    # --------------------------------------------------
    def _tokenize_and_filter(self, text: str) -> list:
        tokens = word_tokenize(text)
        tokens = [
            self.lemmatizer.lemmatize(token)
            for token in tokens
            if token not in self.stop_words and len(token) > 2
        ]
        return tokens

    # --------------------------------------------------
    # PUBLIC METHOD — full pipeline
    # --------------------------------------------------
    def clean_text(self, text: str) -> str:
        """Run the full preprocessing pipeline on a news article."""
        text   = self._remove_noise(text)
        tokens = self._tokenize_and_filter(text)
        return ' '.join(tokens)


# ── Quick test ──────────────────────────────────────
if __name__ == '__main__':
    sample = (
        "BREAKING: Scientists Have PROVEN that the Earth is flat! "
        "Visit http://conspiracy.com for more info. <b>Share NOW!</b>"
    )
    preprocessor = TextPreprocessor()
    cleaned = preprocessor.clean_text(sample)
    print("Original :", sample)
    print("Cleaned  :", cleaned)