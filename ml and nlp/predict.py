"""
=======================================================
  FAKE NEWS ANALYSER — PORTION 1: PREDICTION MODULE
=======================================================
PURPOSE : Load the trained model and predict whether
          a given piece of news is REAL or FAKE.
USED BY : Flask backend (app.py) — this module is
          imported and called for every /api/analyze request.
=======================================================
"""

import pickle
import os


class FakeNewsPredictor:
    """Wraps the trained ML model for easy prediction."""

    def __init__(self, model_dir: str = 'saved_model'):
        """Load the three artefacts saved by train_model.py."""
        if not os.path.exists(model_dir):
            raise FileNotFoundError(
                f"'{model_dir}' not found. Run train_model.py first."
            )
        self.model        = self._load(model_dir, 'model')
        self.tfidf        = self._load(model_dir, 'tfidf')
        self.preprocessor = self._load(model_dir, 'preprocessor')
        print(f"✔ Model loaded from '{model_dir}/'")

    @staticmethod
    def _load(directory, name):
        with open(f'{directory}/{name}.pkl', 'rb') as f:
            return pickle.load(f)

    # --------------------------------------------------
    def predict(self, raw_text: str) -> dict:
        """
        Full prediction pipeline:
          raw text → clean → TF-IDF vector → model → label + confidence
        Returns a dict with prediction, probabilities, and cleaned text.
        """
        # 1. NLP preprocessing (same as training)
        clean = self.preprocessor.clean_text(raw_text)

        # 2. Convert to TF-IDF feature vector
        features = self.tfidf.transform([clean])

        # 3. Classify
        label_id      = self.model.predict(features)[0]       # 0 or 1
        probabilities = self.model.predict_proba(features)[0] # [p_fake, p_real]

        label      = 'REAL' if label_id == 1 else 'FAKE'
        confidence = float(max(probabilities)) * 100
        fake_prob  = float(probabilities[0])  * 100
        real_prob  = float(probabilities[1])  * 100

        return {
            'prediction'       : label,
            'confidence'       : round(confidence, 2),
            'fake_probability' : round(fake_prob,  2),
            'real_probability' : round(real_prob,  2),
            'cleaned_text'     : clean,
        }


# ── Quick test ──────────────────────────────────────
if __name__ == '__main__':
    predictor = FakeNewsPredictor()

    test_cases = [
        "Scientists confirm COVID-19 vaccines are safe and effective according to peer-reviewed study",
        "EXPOSED: Government microchips hidden inside vaccines track your location 5G network",
        "Federal Reserve raises interest rates by 25 basis points citing inflation data",
        "SHOCKING proof the moon landing was faked in Area 51 by NASA agents",
        "Trump has alowed the indian products in usa"
    ]

    print("\n" + "=" * 60)
    print("PREDICTION RESULTS")
    print("=" * 60)

    for text in test_cases:
        result = predictor.predict(text)
        bar    = '█' * int(result['confidence'] / 5)
        print(f"\n📰 {text[:60]}...")
        print(f"   ➜  {result['prediction']}  |  {result['confidence']:.1f}% confidence  {bar}")
        print(f"      Fake: {result['fake_probability']:.1f}%  |  Real: {result['real_probability']:.1f}%")