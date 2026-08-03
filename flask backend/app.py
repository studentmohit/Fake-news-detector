"""
=======================================================
  FAKE NEWS ANALYSER — UPDATED FLASK BACKEND
=======================================================
NEW: Now combines ML prediction + Fact Checking
  POST /api/analyze → ML + Wikipedia + Google Facts
  GET  /api/history → past analyses
  GET  /api/stats   → aggregate statistics
=======================================================
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ml and nlp'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'database'))

from flask      import Flask, request, jsonify
from flask_cors import CORS

from predict      import FakeNewsPredictor
from database     import Database
from fact_checker import FactChecker

app = Flask(__name__)
CORS(app)

# ── Load everything once at startup ──────────────────
try:
    predictor    = FakeNewsPredictor(model_dir='../ml and nlp/saved_model')
    db           = Database(db_path='../fake_news.db')

    # Add your Google API key here (optional — leave None for Wikipedia only)
    # Get free key: console.cloud.google.com → Enable "Fact Check Tools API"
    GOOGLE_API_KEY = None   # e.g. 'AIzaSy...'
    fact_checker   = FactChecker(google_api_key=GOOGLE_API_KEY)

    print("✔ Flask backend ready on http://localhost:5000")
except FileNotFoundError as e:
    print(f"⚠  {e}")
    predictor = None


@app.route('/api/analyze', methods=['POST'])
def analyze():
    if predictor is None:
        return jsonify({'error': 'Model not loaded. Run train.py first.'}), 503

    body = request.get_json()
    if not body or 'text' not in body:
        return jsonify({'error': 'Missing "text" field.'}), 400

    text = body['text'].strip()
    if len(text) < 20:
        return jsonify({'error': 'Text too short. Please provide more content.'}), 400

    # STEP 1: ML Prediction
    ml_result = predictor.predict(text)

    # STEP 2: Fact Checking
    fact_result = fact_checker.check(text)

    # STEP 3: Combine into final verdict
    final_verdict = _combine_verdicts(ml_result, fact_result)

    # STEP 4: Save to database
    db.save_analysis(
        text       = text,
        prediction = final_verdict['label'],
        confidence = ml_result['confidence'],
    )

    return jsonify({
        'success'          : True,
        'prediction'       : ml_result['prediction'],
        'confidence'       : ml_result['confidence'],
        'fake_probability' : ml_result['fake_probability'],
        'real_probability' : ml_result['real_probability'],
        'fact_check' : {
            'final_verdict' : fact_result['final_verdict'],
            'emoji'         : fact_result['emoji'],
            'wikipedia'     : {
                'verdict' : fact_result['wikipedia']['verdict'],
                'summary' : fact_result['wikipedia'].get('summary', ''),
                'url'     : fact_result['wikipedia'].get('url', None),
                'article' : fact_result['wikipedia'].get('article', ''),
            },
            'google' : {
                'verdict' : fact_result['google']['verdict'],
                'claims'  : fact_result['google'].get('claims', []),
            },
        },
        'final_label'   : final_verdict['label'],
        'final_message' : final_verdict['message'],
        'final_emoji'   : final_verdict['emoji'],
    })


def _combine_verdicts(ml_result, fact_result):
    ml_label   = ml_result['prediction']
    fact_label = fact_result['final_verdict']

    if fact_label == 'debunked':
        return {'label': 'FAKE',       'emoji': '🚫', 'message': 'Fact checkers have debunked this claim.'}
    elif fact_label == 'supported' and ml_label == 'REAL':
        return {'label': 'REAL',       'emoji': '✅', 'message': 'ML model and fact checkers both support this claim.'}
    elif fact_label == 'misleading':
        return {'label': 'FAKE',       'emoji': '⚠️', 'message': 'This claim has been found misleading by fact checkers.'}
    elif fact_label == 'partial':
        return {'label': 'UNVERIFIED', 'emoji': '🔶', 'message': 'Partially verified — claim needs more context.'}
    else:
        if ml_label == 'FAKE':
            return {'label': 'FAKE', 'emoji': '🚨', 'message': f"ML model detected fake news patterns ({ml_result['confidence']:.1f}% confidence)."}
        else:
            return {'label': 'REAL', 'emoji': '✅', 'message': f"ML model detected real news patterns ({ml_result['confidence']:.1f}% confidence). No contradicting facts found."}


@app.route('/api/history', methods=['GET'])
def history():
    try:
        return jsonify({'history': db.get_history(limit=20)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def stats():
    try:
        return jsonify(db.get_stats())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status'            : 'ok',
        'model_loaded'      : predictor is not None,
        'google_api_active' : GOOGLE_API_KEY is not None,
    })


@app.route('/api/history/<int:item_id>', methods=['DELETE'])
def delete_history(item_id):
    db.delete_analysis(item_id)
    return jsonify({'success': True})

@app.route('/api/history/all', methods=['DELETE'])
def delete_all_history():
    db.delete_all_analyses()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

